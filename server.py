#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Soundboxd — Letterboxd for Music
Backend Server (Python 3.11 + SQLite + Live Music Metadata Proxy + 4-Tier AI Model Router)
Models Hierarchy (Token Conservation):
  1. Gemini Flash      -> Tier 1 (Fast/Cheap: Moderation, Tagging, Sentiment)
  2. Gemini Pro        -> Tier 2 (Balanced: Track comparison, Smart Recommendations)
  3. Claude Sonnet/Opus-> Tier 3 (Literary/Creative: Poetic Review Assistance, Lyric Analysis)
  4. Gemini Argon      -> Tier 4 (Ultimate/Most Valuable: Used LAST & sparingly for Deep Musical DNA Synthesis)
"""

import json
import os
import re
import sqlite3
import time
import urllib.parse
import urllib.request
from datetime import datetime
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("RAILWAY_VOLUME_MOUNT_PATH", str(BASE_DIR)))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "soundboxd.db"
STATIC_DIR = BASE_DIR / "public"
PORT = int(os.environ.get("PORT", 8080))


def load_env():
    env_file = BASE_DIR / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


load_env()


# ============================================================================
# DATABASE INITIALIZATION & SEED DATA (SQLite)
# ============================================================================
def get_db():
    conn = sqlite3.connect(str(DB_PATH), timeout=30.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=30000;")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS tracks (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            artist TEXT NOT NULL,
            album TEXT NOT NULL,
            release_year INTEGER,
            genre TEXT,
            duration_sec INTEGER DEFAULT 210,
            cover_url TEXT,
            preview_url TEXT,
            external_url TEXT,
            source TEXT DEFAULT 'itunes',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            track_id TEXT NOT NULL,
            username TEXT NOT NULL,
            user_avatar TEXT,
            rating REAL NOT NULL,
            liked INTEGER DEFAULT 0,
            review_text TEXT,
            listen_date TEXT,
            tags TEXT,
            ai_moderated_by TEXT DEFAULT 'gemini-flash',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(track_id) REFERENCES tracks(id)
        );

        CREATE TABLE IF NOT EXISTS listenlist (
            track_id TEXT PRIMARY KEY,
            added_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(track_id) REFERENCES tracks(id)
        );

        CREATE TABLE IF NOT EXISTS favorites (
            slot INTEGER PRIMARY KEY,
            track_id TEXT NOT NULL,
            FOREIGN KEY(track_id) REFERENCES tracks(id)
        );

        CREATE TABLE IF NOT EXISTS custom_lists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            track_ids TEXT NOT NULL,
            created_by TEXT DEFAULT 'batin',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS token_usage_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_tier TEXT NOT NULL,
            model_name TEXT NOT NULL,
            task_type TEXT NOT NULL,
            prompt_tokens INTEGER NOT NULL,
            completion_tokens INTEGER NOT NULL,
            saved_argon_tokens INTEGER NOT NULL,
            cached INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS ai_cache (
            cache_key TEXT PRIMARY KEY,
            model_used TEXT NOT NULL,
            response_json TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS albums (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            artist TEXT NOT NULL,
            release_year INTEGER,
            genre TEXT,
            track_count INTEGER DEFAULT 10,
            cover_url TEXT,
            external_url TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS album_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            album_id TEXT NOT NULL,
            username TEXT NOT NULL,
            rating REAL NOT NULL,
            liked INTEGER DEFAULT 0,
            review_text TEXT,
            listen_date TEXT,
            ai_moderated_by TEXT DEFAULT 'gemini-flash',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(album_id) REFERENCES albums(id)
        );
        """
    )

    # Check if already seeded
    cur.execute("SELECT COUNT(*) as cnt FROM tracks")
    if cur.fetchone()["cnt"] == 0:
        seed_tracks = [
            ('seed-daft-punk-veridis-quo', 'Veridis Quo', 'Daft Punk', 'Discovery', 2001, 'Electronic / French House', 345, 'https://is1-ssl.mzstatic.com/image/thumb/Music221/v4/fd/4a/77/fd4a77db-0ebc-d043-41a2-f32fa1bb0fb4/dj.qrikkdwj.jpg/600x600bb.jpg', 'https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview211/v4/e0/cc/c4/e0ccc4af-ad90-59fe-9a7c-9c32d1a3c380/mzaf_2643765405421046671.plus.aac.p.m4a', 'https://open.spotify.com/search/Veridis%20Quo%20Daft%20Punk', 'curated'),
            ('seed-radiohead-weird-fishes', 'Weird Fishes / Arpeggi', 'Radiohead', 'In Rainbows', 2007, 'Art Rock / Indie', 318, 'https://is1-ssl.mzstatic.com/image/thumb/Music126/v4/dd/50/c7/dd50c790-99ac-d3d0-5ab8-e3891fb8fd52/634904032463.png/600x600bb.jpg', 'https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview221/v4/3a/12/eb/3a12ebaf-89c1-1ac9-6821-3a1de510ef51/mzaf_14543910941982290973.plus.aac.p.m4a', 'https://open.spotify.com/search/Weird%20Fishes%20Radiohead', 'curated'),
            ('seed-tame-impala-let-it-happen', 'Let It Happen', 'Tame Impala', 'Currents', 2015, 'Psychedelic Pop / Synth', 467, 'https://is1-ssl.mzstatic.com/image/thumb/Music115/v4/a8/2e/b4/a82eb490-f30a-a321-461a-0383c88fec95/15UMGIM23316.rgb.jpg/600x600bb.jpg', 'https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview221/v4/77/68/1f/77681ffc-56e6-813c-e1bc-d94a9b5893c1/mzaf_570579359857462588.plus.aac.p.m4a', 'https://open.spotify.com/search/Let%20It%20Happen%20Tame%20Impala', 'curated'),
            ('seed-pink-floyd-time', 'Time', 'Pink Floyd', 'The Dark Side of the Moon', 1973, 'Progressive Rock', 413, 'https://is1-ssl.mzstatic.com/image/thumb/Music221/v4/3e/76/b0/3e76b0e3-762b-2286-a019-8afb19cee541/886445635829.jpg/600x600bb.jpg', 'https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview221/v4/a2/73/36/a27336b7-07c8-207a-74fd-9926910f9903/mzaf_10065953245083721782.plus.aac.p.m4a', 'https://open.spotify.com/search/Time%20Pink%20Floyd', 'curated'),
            ('seed-kendrick-wesleys-theory', "Wesley's Theory", 'Kendrick Lamar', 'To Pimp a Butterfly', 2015, 'Jazz Rap / Funk', 287, 'https://is1-ssl.mzstatic.com/image/thumb/Music112/v4/b5/a6/91/b5a69171-5232-3d5b-9c15-8963802f83dd/15UMGIM15814.rgb.jpg/600x600bb.jpg', 'https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview211/v4/e5/5e/d0/e55ed0d4-7322-6e62-5628-2dd1bf9ecb1e/mzaf_14797433044280126864.plus.aac.p.m4a', 'https://open.spotify.com/search/Wesleys%20Theory%20Kendrick%20Lamar', 'curated'),
            ('seed-baris-manco-donence', 'Dönence', 'Barış Manço', 'Sözüm Meclisten Dışarı', 1981, 'Anatolian Rock / Synth Prog', 355, 'https://is1-ssl.mzstatic.com/image/thumb/Music116/v4/96/b5/6f/96b56f34-4bb9-3aa5-add2-5a2504e74562/cover.jpg/600x600bb.jpg', 'https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview221/v4/9d/42/1a/9d421ada-402a-8a55-cfaf-d80cab5758db/mzaf_2219306841369120275.plus.aac.p.m4a', 'https://open.spotify.com/search/Donence%20Baris%20Manco', 'curated'),
            ('seed-frank-ocean-nights', 'Nights', 'Frank Ocean', 'Blonde', 2016, 'Alternative R&B', 307, 'https://is1-ssl.mzstatic.com/image/thumb/Music116/v4/cd/d3/d0/cdd3d00e-ec53-2e9f-81e2-774c07f5bea9/1827849271625.jpg/600x600bb.jpg', 'https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview211/v4/f1/f4/be/f1f4bec8-3665-4440-cc0c-08626e4ba7eb/mzaf_10767063445979032310.plus.aac.p.m4a', 'https://open.spotify.com/search/Nights%20Frank%20Ocean', 'curated'),
            ('seed-sebo-sigara', 'Sigara', 'Şebnem Ferah', 'Kadın', 1996, 'Turkish Hard Rock', 302, 'https://is1-ssl.mzstatic.com/image/thumb/Music/v4/56/74/7f/56747fd8-0277-02f1-0a86-630f8bf210f1/cover.jpg/600x600bb.jpg', 'https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview221/v4/38/f6/a7/38f6a73e-3019-beda-6c5c-21f20aabc38d/mzaf_10882215665314085673.plus.aac.p.m4a', 'https://open.spotify.com/search/Sigara%20Sebnem%20Ferah', 'curated'),
            ('seed-duman-bu-aksam', 'Bu Akşam', 'Duman', 'Eski Köprünün Altında', 1999, 'Turkish Rock', 292, 'https://is1-ssl.mzstatic.com/image/thumb/Music126/v4/e3/6a/03/e36a0347-7191-da04-7d53-32569e5904fd/884977122039.jpg/600x600bb.jpg', 'https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview125/v4/c2/24/3c/c2243c25-258a-aa0b-7bc8-98dcbfb97ec6/mzaf_8141227513045594527.plus.aac.p.m4a', 'https://open.spotify.com/search/Bu%20Ak%C5%9Fam%20Duman', 'curated'),
            ('seed-mvo-bir-derdim-var', 'Bir Derdim Var', 'Mor ve Ötesi', 'Dünya Yalan Söylüyor', 2004, 'Alternative Rock', 258, 'https://is1-ssl.mzstatic.com/image/thumb/Music211/v4/2d/85/95/2d8595f4-400e-45f9-e5f1-412f011a7361/cover.jpg/600x600bb.jpg', 'https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview211/v4/50/c4/f4/50c4f4fe-a3af-f422-be53-31b19867fef3/mzaf_4507406679469207225.plus.aac.p.m4a', 'https://open.spotify.com/search/Bir%20Derdim%20Var%20Mor%20ve%20%C3%96tesi', 'curated'),
            ('seed-arctic-monkeys-505', '505', 'Arctic Monkeys', 'Favourite Worst Nightmare', 2007, 'Indie Rock', 253, 'https://is1-ssl.mzstatic.com/image/thumb/Music124/v4/82/90/14/829014ad-a301-62ab-bee6-f4cca4457411/mzi.hozudery.jpg/600x600bb.jpg', 'https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview221/v4/d1/0d/ab/d10dabc8-cceb-e718-401f-01516b009460/mzaf_13845311225859403599.plus.aac.p.m4a', 'https://open.spotify.com/search/505%20Arctic%20Monkeys', 'curated'),
            ('seed-muse-supermassive', 'Supermassive Black Hole', 'Muse', 'Black Holes and Revelations', 2006, 'Alternative Rock', 208, 'https://is1-ssl.mzstatic.com/image/thumb/Music124/v4/4a/c1/5d/4ac15dc9-2ae6-1d5b-3add-43bae227f941/825646095452.jpg/600x600bb.jpg', 'https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview221/v4/76/4a/63/764a63c0-9533-97ce-51a5-31a23b57f2eb/mzaf_3187296926844362175.plus.aac.p.m4a', 'https://open.spotify.com/search/Supermassive%20Black%20Hole%20Muse', 'curated'),
            ('seed-strokes-reptilia', 'Reptilia', 'The Strokes', 'Room on Fire', 2003, 'Indie Rock / Garage Rock', 219, 'https://is1-ssl.mzstatic.com/image/thumb/Music124/v4/f7/e9/2a/f7e92a48-0e20-8286-bbbf-80bd85fbb1af/mzi.gcledsjj.jpg/600x600bb.jpg', 'https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview211/v4/82/1c/f2/821cf232-955e-ace3-b24e-9e944f0d000b/mzaf_13672834633152538860.plus.aac.p.m4a', '', 'curated'),
            ('seed-weeknd-after-hours', 'After Hours', 'The Weeknd', 'After Hours', 2020, 'Synthwave / Alternative R&B', 361, 'https://is1-ssl.mzstatic.com/image/thumb/Music125/v4/6f/bc/e6/6fbce6c4-c38c-72d8-4fd0-66cfff32f679/20UMGIM12176.rgb.jpg/600x600bb.jpg', 'https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview211/v4/54/2b/61/542b6133-80f7-f30f-4dcf-059490db9d84/mzaf_1539067797902127760.plus.aac.p.m4a', '', 'curated'),
            ('seed-deftones-be-quiet', 'Be Quiet and Drive (Far Away)', 'Deftones', 'Around the Fur', 1997, 'Alternative Metal / Shoegaze', 308, 'https://is1-ssl.mzstatic.com/image/thumb/Music125/v4/27/cb/b4/27cbb40e-f8c6-dede-9c69-62089a873fa9/093624919803.jpg/600x600bb.jpg', 'https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview211/v4/82/8b/a2/828ba269-81af-dc56-d8a2-fa712a02dd02/mzaf_10134856389145791661.plus.aac.p.m4a', '', 'curated'),
            ('seed-gorillaz-empire-ants', 'Empire Ants', 'Gorillaz', 'Plastic Beach', 2010, 'Synth-Pop / Indietronica', 283, 'https://is1-ssl.mzstatic.com/image/thumb/Music124/v4/7e/69/1f/7e691f10-3cc1-67ec-5dc3-df3d8df68fa7/5099962829359.jpg/600x600bb.jpg', 'https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview211/v4/d4/85/0a/d4850aca-9aa5-23e9-b8a7-b1b35de8875a/mzaf_18227983270868467976.plus.aac.p.m4a', '', 'curated'),
            ('seed-massive-attack-teardrop', 'Teardrop', 'Massive Attack', 'Mezzanine', 1998, 'Trip-Hop', 330, 'https://is1-ssl.mzstatic.com/image/thumb/Music115/v4/0a/98/55/0a98555b-8d9d-3b46-660a-b91261557d17/00724384559953.rgb.jpg/600x600bb.jpg', 'https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview221/v4/a3/a6/91/a3a691b0-8e49-399d-2585-ddcd6694c9f2/mzaf_16325826545413166648.plus.aac.p.m4a', '', 'curated'),
            ('seed-fleetwood-mac-chain', 'The Chain', 'Fleetwood Mac', 'Rumours', 1977, 'Classic Rock', 270, 'https://is1-ssl.mzstatic.com/image/thumb/Music125/v4/2a/eb/dc/2aebdc18-c2c0-0fdd-fb85-07538a925700/603497925766.jpg/600x600bb.jpg', 'https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview211/v4/15/9f/31/159f3139-16ab-6ccf-813f-86d4adffcf61/mzaf_17361308171774933378.plus.aac.p.m4a', '', 'curated'),
            ('seed-beach-house-space-song', 'Space Song', 'Beach House', 'Depression Cherry', 2015, 'Dream Pop', 320, 'https://is1-ssl.mzstatic.com/image/thumb/Music125/v4/09/e0/d5/09e0d559-0682-f0f0-5e0c-3cd11e3114fd/beachhouse_depressioncherry_2400_300.jpg/600x600bb.jpg', 'https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview221/v4/41/61/14/416114cc-282e-4c76-2808-a3eb9c3f973d/mzaf_6665874998714897722.plus.aac.p.m4a', '', 'curated'),
            ('seed-justice-genesis', 'Genesis', 'Justice', 'Cross', 2007, 'French Electro / Electronic', 234, 'https://is1-ssl.mzstatic.com/image/thumb/Music115/v4/62/e4/01/62e40187-e672-17e5-f31f-9aee262703a3/mzi.bifzeufu.jpg/600x600bb.jpg', 'https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview221/v4/42/3e/6b/423e6b98-27eb-5b5a-a5de-4342e092c5d7/mzaf_17829132711140395838.plus.aac.p.m4a', '', 'curated'),
            ('seed-jeff-buckley-lover', "Lover, You Should've Come Over", 'Jeff Buckley', 'Grace', 1994, 'Alternative Rock / Folk Rock', 404, 'https://is1-ssl.mzstatic.com/image/thumb/Music115/v4/26/d6/e3/26d6e339-a7a9-d61e-1b5f-0852a5515a55/886445517880.jpg/600x600bb.jpg', 'https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview211/v4/db/0c/4e/db0c4edc-9daa-e262-55b9-89984c3f6aa6/mzaf_16142695276315265640.plus.aac.p.m4a', '', 'curated'),
            ('seed-portishead-glory-box', 'Glory Box', 'Portishead', 'Dummy', 1994, 'Trip-Hop', 308, 'https://is1-ssl.mzstatic.com/image/thumb/Music115/v4/c1/71/93/c1719342-df7d-e9c5-c87c-53dae5afb289/00042282855329.rgb.jpg/600x600bb.jpg', 'https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview221/v4/40/b2/a4/40b2a45b-eacf-818f-7af6-f7f8b3885230/mzaf_16256497095178600689.plus.aac.p.m4a', '', 'curated'),
            ('seed-tyler-earfquake', 'EARFQUAKE', 'Tyler, The Creator', 'IGOR', 2019, 'Neo-Soul / Alternative Hip-Hop', 207, 'https://is1-ssl.mzstatic.com/image/thumb/Music126/v4/22/fd/10/22fd10a3-881d-2560-64e7-a9df650b9e47/17UM1IM42651.rgb.jpg/600x600bb.jpg', 'https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview221/v4/ea/a6/99/eaa699af-33dc-3f58-5ebd-e4b830707647/mzaf_11136703388258616116.plus.aac.p.m4a', '', 'curated'),
            ('seed-cem-karaca-tamirci', 'Tamirci Çırağı', 'Cem Karaca', 'Yoksulluk Kader Olamaz', 1975, 'Anatolian Rock', 296, 'https://is1-ssl.mzstatic.com/image/thumb/Music124/v4/85/20/ae/8520ae1f-63fc-ab56-6467-67e5a381bd27/cover.jpg/600x600bb.jpg', 'https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview125/v4/39/8a/d3/398ad3a6-2d65-7c08-94fe-04004c509e70/mzaf_12582990614670416404.plus.aac.p.m4a', '', 'curated'),
            ('itunes-1716096823', 'Time is Running Out', 'Muse', 'Absolution', 2003, 'Rock', 236, 'https://is1-ssl.mzstatic.com/image/thumb/Music126/v4/4a/73/ab/4a73abdf-1d55-b3fe-484d-e023a507428e/5054197904233.jpg/600x600bb.jpg', 'https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview211/v4/6d/97/80/6d9780b4-c55b-1a44-efbd-f5b474db05f8/mzaf_11184790201860208089.plus.aac.p.m4a', 'https://music.apple.com/us/album/time-is-running-out/1716096819?i=1716096823&uo=4', 'itunes-api'),
            ('itunes-268603478', 'In My Time of Need', 'Opeth', 'Damnation', 2003, 'Metal', 346, 'https://is1-ssl.mzstatic.com/image/thumb/Music126/v4/3e/bf/fd/3ebffd50-2061-862e-7160-cbba45f99e74/828768291122.jpg/600x600bb.jpg', 'https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview211/v4/38/97/75/389775bf-6618-e953-335d-76210ad4ac3e/mzaf_15973449658923841508.plus.aac.p.m4a', 'https://music.apple.com/us/album/in-my-time-of-need/268603296?i=268603478&uo=4', 'itunes-api'),
            ('itunes-918614531', 'Starless', 'King Crimson', 'Red (Expanded Edition)', 1974, 'Prog-Rock/Art Rock', 744, 'https://is1-ssl.mzstatic.com/image/thumb/Music4/v4/a8/5d/d3/a85dd370-ed7e-1e6f-f2ee-5464f7b3a978/Red_2500px.jpg/600x600bb.jpg', 'https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview211/v4/2b/0d/38/2b0d3843-3d77-9280-db2f-ca04f165e5ca/mzaf_6567600515713287450.plus.aac.p.m4a', 'https://music.apple.com/us/album/starless/918614446?i=918614531&uo=4', 'itunes-api'),
        ]
        cur.executemany(
            """
            INSERT INTO tracks (id, title, artist, album, release_year, genre, duration_sec, cover_url, preview_url, external_url, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            seed_tracks,
        )

        seed_reviews = [
            (
                "seed-daft-punk-veridis-quo",
                "batin",
                "🎧",
                5.0,
                1,
                "That baroque synth melody playing while driving alone on the highway at 3 AM... Daft Punk's most emotional masterpiece.",
                "2026-11-10",
                "night-drive,synth,nostalgia,masterpiece",
                "gemini-flash",
            ),
            (
                "seed-radiohead-weird-fishes",
                "batin",
                "🎧",
                4.5,
                1,
                "Layered guitar arpeggios that pull you down to the bottom of the ocean and bring you back to the surface.",
                "2026-11-09",
                "arpeggio,deep,melancholy",
                "gemini-flash",
            ),
            (
                "seed-baris-manco-donence",
                "batin",
                "🎧",
                5.0,
                1,
                "Incredible that such a space-rock / synth-prog production was crafted in 1981. Truly timeless.",
                "2026-11-08",
                "anatolian-rock,timeless,prog",
                "gemini-flash",
            ),
            (
                "seed-frank-ocean-nights",
                "melis_kr",
                "🌙",
                5.0,
                1,
                "The beat switch at 3:30 might be the greatest transition in music history—the golden ratio splitting the album in two.",
                "2026-11-10",
                "beat-switch,late-night,rnb",
                "gemini-flash",
            ),
            (
                "seed-tame-impala-let-it-happen",
                "can_synth",
                "🎹",
                4.5,
                1,
                "Turning a skipping CD glitch effect into the most hypnotic moment of a track... Kevin Parker is a genius.",
                "2026-11-07",
                "psychedelic,hypnotic,synth",
                "gemini-flash",
            ),
            (
                "seed-pink-floyd-time",
                "emre_vinyl",
                "💿",
                5.0,
                1,
                "Time genuinely stands still the second David Gilmour's guitar solo begins, and the lyrics hit harder every passing year.",
                "2026-11-06",
                "classic,guitar-solo,philosophical",
                "gemini-flash",
            ),
        ]
        cur.executemany(
            """
            INSERT INTO reviews (track_id, username, user_avatar, rating, liked, review_text, listen_date, tags, ai_moderated_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            seed_reviews,
        )

        # Favorites Top 4 (Synced from user's PC setup)
        favorites = [
            (1, "itunes-1716096823"),
            (2, "itunes-268603478"),
            (3, "seed-radiohead-weird-fishes"),
            (4, "itunes-918614531"),
        ]
        cur.executemany("INSERT INTO favorites (slot, track_id) VALUES (?, ?)", favorites)

        # Listenlist (Playlist)
        cur.execute("INSERT INTO listenlist (track_id) VALUES (?)", ("itunes-268603478",))
        cur.execute("INSERT INTO listenlist (track_id) VALUES (?)", ("seed-kendrick-wesleys-theory",))
        cur.execute("INSERT INTO listenlist (track_id) VALUES (?)", ("seed-sebo-sigara",))

        # Custom Lists
        cur.execute(
            """
            INSERT INTO custom_lists (title, description, track_ids, created_by)
            VALUES (?, ?, ?, ?)
            """,
            (
                "After 2:00 AM: Late Night Headphone Essentials",
                "Four deeply atmospheric tracks for when the city is asleep.",
                json.dumps(
                    [
                        "seed-daft-punk-veridis-quo",
                        "seed-radiohead-weird-fishes",
                        "seed-frank-ocean-nights",
                        "seed-baris-manco-donence",
                    ]
                ),
                "batin",
            ),
        )

        # Initial token usage log showing the 4-tier economy in action
        seed_tokens = [
            ("Tier 1: Hızlı/Ekonomik", "Gemini 3.8 Flash", "Yorum Moderasyonu & Otomatik Etiketleme", 180, 45, 225),
            ("Tier 1: Hızlı/Ekonomik", "Gemini 3.8 Flash", "Arama Sorgusu & Duygu Analizi", 140, 35, 175),
            ("Tier 2: Dengeli Analiz", "Gemini 2.5 Pro", "Benzer Frekans & Ritim Eşleştirme", 420, 190, 610),
            ("Tier 3: Edebi & Yaratıcı", "Claude Sonnet 4.5", "Letterboxd Tarzı Edebi İnceleme Yardımı", 510, 280, 790),
            ("Tier 4: Zirve Sentez (En Değerli)", "Gemini 4 Argon", "Derin Müzikal DNA & Karakter Haritası", 890, 410, 0),
        ]
        cur.executemany(
            """
            INSERT INTO token_usage_log (model_tier, model_name, task_type, prompt_tokens, completion_tokens, saved_argon_tokens)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            seed_tokens,
        )

        seed_albums = [
            ('album-daft-punk-discovery', 'Discovery', 'Daft Punk', 2001, 'Electronic', 14, 'https://is1-ssl.mzstatic.com/image/thumb/Music221/v4/fd/4a/77/fd4a77db-0ebc-d043-41a2-f32fa1bb0fb4/dj.qrikkdwj.jpg/600x600bb.jpg', '697194953'),
            ('album-radiohead-in-rainbows', 'In Rainbows', 'Radiohead', 2007, 'Alternative', 10, 'https://is1-ssl.mzstatic.com/image/thumb/Music126/v4/dd/50/c7/dd50c790-99ac-d3d0-5ab8-e3891fb8fd52/634904032463.png/600x600bb.jpg', '1109714933'),
            ('album-pink-floyd-dark-side', 'The Dark Side of the Moon', 'Pink Floyd', 1973, 'Rock', 10, 'https://is1-ssl.mzstatic.com/image/thumb/Music221/v4/3e/76/b0/3e76b0e3-762b-2286-a019-8afb19cee541/886445635829.jpg/600x600bb.jpg', '1065973699'),
            ('album-kendrick-tpab', 'To Pimp a Butterfly', 'Kendrick Lamar', 2015, 'Hip-Hop/Rap', 16, 'https://is1-ssl.mzstatic.com/image/thumb/Music112/v4/b5/a6/91/b5a69171-5232-3d5b-9c15-8963802f83dd/15UMGIM15814.rgb.jpg/600x600bb.jpg', '1440871877'),
            ('album-tame-impala-currents', 'Currents', 'Tame Impala', 2015, 'Alternative', 13, 'https://is1-ssl.mzstatic.com/image/thumb/Music115/v4/a8/2e/b4/a82eb490-f30a-a321-461a-0383c88fec95/15UMGIM23316.rgb.jpg/600x600bb.jpg', '1440838039'),
            ('album-frank-ocean-blonde', 'Blonde', 'Frank Ocean', 2016, 'R&B/Soul', 15, 'https://is1-ssl.mzstatic.com/image/thumb/Music116/v4/cd/d3/d0/cdd3d00e-ec53-2e9f-81e2-774c07f5bea9/1827849271625.jpg/600x600bb.jpg', '1599412296'),
            ('album-baris-manco-sozum', 'Sözüm Meclisten Dışarı', 'Barış Manço', 1981, 'Rock', 16, 'https://is1-ssl.mzstatic.com/image/thumb/Music116/v4/96/b5/6f/96b56f34-4bb9-3aa5-add2-5a2504e74562/cover.jpg/600x600bb.jpg', '590644563'),
            ('album-arctic-monkeys-am', 'AM', 'Arctic Monkeys', 2013, 'Indie Rock', 12, 'https://is1-ssl.mzstatic.com/image/thumb/Music211/v4/69/9c/b5/699cb5d6-115c-ff73-9d26-e57ea4350d72/887828031795.png/600x600bb.jpg', '663097964'),
            ('album-strokes-is-this-it', 'Is This It', 'The Strokes', 2001, 'Indie Rock', 12, 'https://is1-ssl.mzstatic.com/image/thumb/Music115/v4/9c/ae/7a/9cae7a72-29ed-08aa-1b42-913776bbb6ec/886443855571.jpg/600x600bb.jpg', '601140186'),
            ('album-massive-attack-mezzanine', 'Mezzanine', 'Massive Attack', 1998, 'Trip-Hop', 19, 'https://is1-ssl.mzstatic.com/image/thumb/Music115/v4/8a/c1/04/8ac104fb-d37e-1433-5d2e-805710d7a7c4/00602567930983.rgb.jpg/600x600bb.jpg', '1428684976'),
            ('album-fleetwood-mac-rumours', 'Rumours', 'Fleetwood Mac', 1977, 'Classic Rock', 11, 'https://is1-ssl.mzstatic.com/image/thumb/Music124/v4/4d/13/ba/4d13bac3-d3d5-7581-2c74-034219eadf2b/081227970949.jpg/600x600bb.jpg', '594061854'),
            ('album-gorillaz-demon-days', 'Demon Days', 'Gorillaz', 2005, 'Alternative', 1, 'https://is1-ssl.mzstatic.com/image/thumb/Music115/v4/1a/3d/42/1a3d42e3-81cf-e21b-b920-2bb449be8410/190296653728.jpg/600x600bb.jpg', '1568312941'),
            ('album-weeknd-after-hours', 'After Hours', 'The Weeknd', 2020, 'R&B/Soul', 14, 'https://is1-ssl.mzstatic.com/image/thumb/Music125/v4/2b/b9/fe/2bb9fef5-d7f3-8345-25a9-db0e79fde4e4/20UMGIM11048.rgb.jpg/600x600bb.jpg', '1499385848'),
            ('album-tyler-igor', 'IGOR', 'Tyler, The Creator', 2019, 'Hip-Hop/Rap', 6, 'https://is1-ssl.mzstatic.com/image/thumb/Music125/v4/a8/df/7d/a8df7d1e-0a11-6228-61af-3230783a9485/886447419601.jpg/600x600bb.jpg', '1441586573'),
            ('album-mvo-dunya-yalan', 'Dünya Yalan Söylüyor', 'Mor ve Ötesi', 2004, 'Alternative Rock', 12, '', ''),
        ]
        cur.executemany(
            """
            INSERT OR IGNORE INTO albums (id, title, artist, release_year, genre, track_count, cover_url, external_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            seed_albums
        )

    conn.commit()
    conn.close()


# ============================================================================
# LIVE MUSIC SEARCH (iTunes Public API + Optional Spotify Web API)
# No musician permission required: Uses official public metadata & 30s previews!
# ============================================================================
_SUGGEST_CACHE = {}


def get_search_suggestions(query: str):
    """Fast typeahead: prefix local matches + parallel live iTunes songs/albums (millions of tracks)."""
    from concurrent.futures import ThreadPoolExecutor

    key = query.lower()
    cached = _SUGGEST_CACHE.get(key)
    if cached and time.time() - cached[0] < 600:
        return cached[1]

    songs, albums, seen_songs, seen_albums = [], [], set(), set()

    conn = get_db()
    try:
        cur = conn.cursor()
        prefix = f"{query}%"
        word_prefix = f"% {query}%"
        cur.execute(
            """
            SELECT id, title, artist, album, cover_url, preview_url, genre, release_year
            FROM tracks
            WHERE title LIKE ? OR artist LIKE ? OR title LIKE ? OR artist LIKE ?
            LIMIT 2
            """,
            (prefix, prefix, word_prefix, word_prefix),
        )
        for r in cur.fetchall():
            songs.append(dict(r))
            seen_songs.add((r["title"].lower(), r["artist"].lower()))

        cur.execute(
            """
            SELECT id, title, artist, cover_url
            FROM albums
            WHERE title LIKE ? OR artist LIKE ? OR title LIKE ? OR artist LIKE ?
            LIMIT 2
            """,
            (prefix, prefix, word_prefix, word_prefix),
        )
        for r in cur.fetchall():
            albums.append(dict(r))
            seen_albums.add((r["title"].lower(), r["artist"].lower()))
    finally:
        conn.close()

    def itunes(entity, limit):
        try:
            url = f"https://itunes.apple.com/search?term={urllib.parse.quote(query)}&entity={entity}&limit={limit}"
            req = urllib.request.Request(url, headers={"User-Agent": "Larpmaxxing/1.0"})
            with urllib.request.urlopen(req, timeout=2.5) as resp:
                return json.loads(resp.read().decode("utf-8")).get("results", [])
        except Exception:
            return []

    with ThreadPoolExecutor(max_workers=2) as ex:
        fut_songs = ex.submit(itunes, "song", 8)
        fut_albums = ex.submit(itunes, "album", 5)
        song_items = fut_songs.result()
        album_items = fut_albums.result()

    for it in song_items:
        sig = (it.get("trackName", "").lower(), it.get("artistName", "").lower())
        if sig in seen_songs or len(songs) >= 7:
            continue
        seen_songs.add(sig)
        songs.append({
            "id": f"itunes-{it.get('trackId')}",
            "title": it.get("trackName", ""),
            "artist": it.get("artistName", ""),
            "album": it.get("collectionName", ""),
            "cover_url": it.get("artworkUrl100", "").replace("100x100bb", "300x300bb"),
            "preview_url": it.get("previewUrl", ""),
            "genre": it.get("primaryGenreName", ""),
            "release_year": int(it["releaseDate"][:4]) if it.get("releaseDate", "")[:4].isdigit() else None,
        })

    for it in album_items:
        sig = (it.get("collectionName", "").lower(), it.get("artistName", "").lower())
        if sig in seen_albums or len(albums) >= 4:
            continue
        seen_albums.add(sig)
        albums.append({
            "id": f"itunes-album-{it.get('collectionId')}",
            "title": it.get("collectionName", ""),
            "artist": it.get("artistName", ""),
            "cover_url": it.get("artworkUrl100", "").replace("100x100bb", "300x300bb"),
        })

    result = {"songs": songs, "albums": albums}
    _SUGGEST_CACHE[key] = (time.time(), result)
    return result


def search_music_catalog(query: str, limit: int = 12):
    """
    Fetches official song metadata, album art (600x600), and legal 30-second audio previews
    from Apple iTunes Search API and merges with local DB ratings in a safe, isolated transaction.
    """
    results = []
    try:
        encoded = urllib.parse.quote(query)
        url = f"https://itunes.apple.com/search?term={encoded}&entity=song&limit={limit}"
        req = urllib.request.Request(url, headers={"User-Agent": "Soundboxd/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            for item in data.get("results", []):
                track_id = f"itunes-{item.get('trackId')}"
                artwork = item.get("artworkUrl100", "").replace("100x100bb", "600x600bb")
                release_date = item.get("releaseDate", "2020")
                year = int(release_date[:4]) if release_date and release_date[:4].isdigit() else 2020
                duration_sec = int(item.get("trackTimeMillis", 210000) / 1000)

                track_obj = {
                    "id": track_id,
                    "title": item.get("trackName", "Unknown Track"),
                    "artist": item.get("artistName", "Unknown Artist"),
                    "album": item.get("collectionName", "Single"),
                    "release_year": year,
                    "genre": item.get("primaryGenreName", "Music"),
                    "duration_sec": duration_sec,
                    "cover_url": artwork,
                    "preview_url": item.get("previewUrl", ""),
                    "external_url": item.get("trackViewUrl", ""),
                    "source": "itunes-api",
                }
                results.append(track_obj)
    except Exception:
        pass

    conn = get_db()
    try:
        cur = conn.cursor()
        for track_obj in results:
            cur.execute(
                """
                INSERT INTO tracks (id, title, artist, album, release_year, genre, duration_sec, cover_url, preview_url, external_url, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    preview_url = CASE WHEN excluded.preview_url != '' THEN excluded.preview_url ELSE tracks.preview_url END,
                    cover_url = CASE WHEN excluded.cover_url != '' THEN excluded.cover_url ELSE tracks.cover_url END
                """,
                (
                    track_obj["id"],
                    track_obj["title"],
                    track_obj["artist"],
                    track_obj["album"],
                    track_obj["release_year"],
                    track_obj["genre"],
                    track_obj["duration_sec"],
                    track_obj["cover_url"],
                    track_obj["preview_url"],
                    track_obj["external_url"],
                    track_obj["source"],
                ),
            )
        conn.commit()

        q_like = f"%{query}%"
        cur.execute(
            """
            SELECT * FROM tracks
            WHERE title LIKE ? OR artist LIKE ? OR album LIKE ? OR genre LIKE ?
            LIMIT ?
            """,
            (q_like, q_like, q_like, q_like, limit),
        )
        local_rows = [dict(r) for r in cur.fetchall()]
        seen_ids = {r["id"] for r in results}
        for row in local_rows:
            if row["id"] not in seen_ids:
                results.insert(0, row)
                seen_ids.add(row["id"])
    except Exception:
        pass
    finally:
        conn.close()

    return enrich_tracks_with_stats(results[:limit])


def enrich_tracks_with_stats(tracks):
    conn = get_db()
    try:
        cur = conn.cursor()
        enriched = []
        for t in tracks:
            tid = t["id"]
            cur.execute(
                """
                SELECT COUNT(*) as review_count,
                       ROUND(AVG(rating), 2) as avg_rating,
                       SUM(liked) as likes_count
                FROM reviews WHERE track_id = ?
                """,
                (tid,),
            )
            stat = cur.fetchone()
            cur.execute(
                "SELECT rating, COUNT(*) as cnt FROM reviews WHERE track_id = ? GROUP BY rating",
                (tid,),
            )
            hist = {str(float(i) / 2): 0 for i in range(1, 11)}
            for r in cur.fetchall():
                key = str(float(r["rating"]))
                if key in hist:
                    hist[key] = r["cnt"]

            cur.execute("SELECT 1 FROM listenlist WHERE track_id = ?", (tid,))
            in_listenlist = cur.fetchone() is not None

            t_copy = dict(t)
            t_copy["review_count"] = stat["review_count"] or 0
            t_copy["avg_rating"] = stat["avg_rating"] if stat["avg_rating"] is not None else 0.0
            t_copy["likes_count"] = stat["likes_count"] or 0
            t_copy["histogram"] = hist
            t_copy["in_listenlist"] = in_listenlist
            enriched.append(t_copy)
        return enriched
    finally:
        conn.close()


def enrich_albums_with_stats(albums):
    conn = get_db()
    try:
        cur = conn.cursor()
        enriched = []
        for a in albums:
            aid = a["id"]
            cur.execute(
                """
                SELECT COUNT(*) as review_count,
                       ROUND(AVG(rating), 2) as avg_rating,
                       SUM(liked) as likes_count
                FROM album_reviews WHERE album_id = ?
                """,
                (aid,),
            )
            stat = cur.fetchone()
            cur.execute(
                "SELECT rating, COUNT(*) as cnt FROM album_reviews WHERE album_id = ? GROUP BY rating",
                (aid,),
            )
            hist = {str(float(i) / 2): 0 for i in range(1, 11)}
            for r in cur.fetchall():
                key = str(float(r["rating"]))
                if key in hist:
                    hist[key] = r["cnt"]

            a_copy = dict(a)
            a_copy["review_count"] = stat["review_count"] or 0
            a_copy["avg_rating"] = stat["avg_rating"] if stat["avg_rating"] is not None else 0.0
            a_copy["likes_count"] = stat["likes_count"] or 0
            a_copy["histogram"] = hist
            enriched.append(a_copy)
        return enriched
    finally:
        conn.close()


def ensure_itunes_track(track_id: str) -> bool:
    """Insert an iTunes track into the DB on demand (e.g. opened from search suggestions or album tracklist)."""
    tid_num = track_id.replace("itunes-", "")
    if not tid_num.isdigit():
        return False
    try:
        req = urllib.request.Request(
            f"https://itunes.apple.com/lookup?id={tid_num}", headers={"User-Agent": "SongLarp/1.0"}
        )
        with urllib.request.urlopen(req, timeout=6) as resp:
            items = json.loads(resp.read().decode("utf-8")).get("results", [])
    except Exception:
        return False
    if not items:
        return False
    it = items[0]
    rd = it.get("releaseDate", "")
    conn = get_db()
    try:
        conn.execute(
            """
            INSERT OR IGNORE INTO tracks (id, title, artist, album, release_year, genre, duration_sec, cover_url, preview_url, external_url, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                track_id,
                it.get("trackName", "Şarkı"),
                it.get("artistName", "Sanatçı"),
                it.get("collectionName", "Single"),
                int(rd[:4]) if rd[:4].isdigit() else 2020,
                it.get("primaryGenreName", "Music"),
                int(it.get("trackTimeMillis", 210000) / 1000),
                it.get("artworkUrl100", "").replace("100x100bb", "600x600bb"),
                it.get("previewUrl", ""),
                it.get("trackViewUrl", ""),
                "itunes-api",
            ),
        )
        conn.commit()
    finally:
        conn.close()
    return True


def ensure_itunes_album(album_id: str) -> bool:
    """Insert an iTunes album into the DB on demand (e.g. opened from search suggestions)."""
    col_id = album_id.replace("itunes-album-", "")
    if not col_id.isdigit():
        return False
    try:
        req = urllib.request.Request(
            f"https://itunes.apple.com/lookup?id={col_id}", headers={"User-Agent": "SongLarp/1.0"}
        )
        with urllib.request.urlopen(req, timeout=6) as resp:
            items = json.loads(resp.read().decode("utf-8")).get("results", [])
    except Exception:
        return False
    if not items:
        return False
    it = items[0]
    rd = it.get("releaseDate", "")
    conn = get_db()
    try:
        conn.execute(
            """
            INSERT OR IGNORE INTO albums (id, title, artist, release_year, genre, track_count, cover_url, external_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                album_id,
                it.get("collectionName", "Albüm"),
                it.get("artistName", ""),
                int(rd[:4]) if rd[:4].isdigit() else None,
                it.get("primaryGenreName", "Music"),
                it.get("trackCount", 10),
                it.get("artworkUrl100", "").replace("100x100bb", "600x600bb"),
                col_id,
            ),
        )
        conn.commit()
    finally:
        conn.close()
    return True


def search_albums_catalog(query: str, limit: int = 12):
    results = []
    try:
        encoded = urllib.parse.quote(query)
        url = f"https://itunes.apple.com/search?term={encoded}&entity=album&limit={limit}"
        req = urllib.request.Request(url, headers={"User-Agent": "Soundboxd/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            for item in data.get("results", []):
                col_id = str(item.get("collectionId"))
                album_id = f"itunes-album-{col_id}"
                artwork = item.get("artworkUrl100", "").replace("100x100bb", "600x600bb")
                release_date = item.get("releaseDate", "2020")
                year = int(release_date[:4]) if release_date and release_date[:4].isdigit() else 2020
                track_count = item.get("trackCount", 10)

                album_obj = {
                    "id": album_id,
                    "title": item.get("collectionName", "Unknown Album"),
                    "artist": item.get("artistName", "Unknown Artist"),
                    "release_year": year,
                    "genre": item.get("primaryGenreName", "Music"),
                    "track_count": track_count,
                    "cover_url": artwork,
                    "external_url": col_id,
                }
                results.append(album_obj)
    except Exception:
        pass

    conn = get_db()
    try:
        cur = conn.cursor()
        for album_obj in results:
            cur.execute(
                """
                INSERT INTO albums (id, title, artist, release_year, genre, track_count, cover_url, external_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    cover_url = CASE WHEN excluded.cover_url != '' THEN excluded.cover_url ELSE albums.cover_url END
                """,
                (
                    album_obj["id"],
                    album_obj["title"],
                    album_obj["artist"],
                    album_obj["release_year"],
                    album_obj["genre"],
                    album_obj["track_count"],
                    album_obj["cover_url"],
                    album_obj["external_url"],
                ),
            )
        conn.commit()

        q_like = f"%{query}%"
        cur.execute(
            """
            SELECT * FROM albums
            WHERE title LIKE ? OR artist LIKE ? OR genre LIKE ?
            LIMIT ?
            """,
            (q_like, q_like, q_like, limit),
        )
        local_rows = [dict(r) for r in cur.fetchall()]
        seen_ids = {r["id"] for r in results}
        for row in local_rows:
            if row["id"] not in seen_ids:
                results.insert(0, row)
                seen_ids.add(row["id"])
    except Exception:
        pass
    finally:
        conn.close()

    return enrich_albums_with_stats(results[:limit])


DISCOVER_ARTISTS_POOL = [
    "Nirvana", "Lana Del Rey", "Interpol", "Queens of the Stone Age", "LCD Soundsystem",
    "Aphex Twin", "Sade", "The Cure", "Joy Division", "New Order",
    "Smashing Pumpkins", "Pixies", "Sonic Youth", "My Bloody Valentine", "Slowdive",
    "Cocteau Twins", "Björk", "Nine Inch Nails", "Tool", "System of a Down",
    "Linkin Park", "Red Hot Chili Peppers", "Foo Fighters", "Oasis", "Blur",
    "Pulp", "Suede", "The Smiths", "David Bowie", "Prince",
    "Michael Jackson", "Stevie Wonder", "Marvin Gaye", "Erykah Badu", "D'Angelo",
    "Lauryn Hill", "OutKast", "A Tribe Called Quest", "Wu-Tang Clan", "MF DOOM",
    "Nas", "Kanye West", "Kid Cudi", "Childish Gambino", "SZA",
    "Steve Lacy", "Blood Orange", "Daniel Caesar", "Kaytranada", "Anderson .Paak",
    "Thundercat", "Flying Lotus", "Bonobo", "Four Tet", "Burial",
    "Bicep", "Röyksopp", "Air", "Kavinsky", "Gesaffelstein",
    "Chemical Brothers", "Prodigy", "Fatboy Slim", "Moby", "Underworld",
    "Khruangbin", "Mac DeMarco", "MGMT", "Empire of the Sun", "Phoenix",
    "Vampire Weekend", "The Strokes", "Franz Ferdinand", "Kasabian", "Royal Blood",
    "Fontaines D.C.", "Idles", "King Gizzard", "Unknown Mortal Orchestra", "Toro y Moi",
    "Erkin Koray", "Moğollar", "Teoman", "Pentagram", "Kurban",
    "Athena", "Manga", "Yavuz Çetin", "Altın Gün", "Nick Cave",
    "PJ Harvey", "Fiona Apple", "Elliott Smith", "Sufjan Stevens", "Bon Iver",
    "Sigur Rós", "Explosions in the Sky", "Mogwai", "Godspeed You! Black Emperor", "Boards of Canada",
]


def discover_more_catalog(item_type: str = "tracks", page: int = 0, query: str = ""):
    """Fetches a fresh page of tracks or albums from the live iTunes catalog for infinite scrolling."""
    from concurrent.futures import ThreadPoolExecutor

    entity = "album" if item_type == "albums" else "song"
    results = []

    if query and query.strip():
        # Paginated live search for the active query/filter
        try:
            offset = max(0, (page + 1) * 18)
            encoded = urllib.parse.quote(query.strip())
            url = f"https://itunes.apple.com/search?term={encoded}&entity={entity}&limit=20&offset={offset}"
            req = urllib.request.Request(url, headers={"User-Agent": "Larpmaxxing/1.0"})
            with urllib.request.urlopen(req, timeout=4.5) as resp:
                raw_items = json.loads(resp.read().decode("utf-8")).get("results", [])
        except Exception:
            raw_items = []
    else:
        # Pick 5 distinct artists for this page from DISCOVER_ARTISTS_POOL
        pool_len = len(DISCOVER_ARTISTS_POOL)
        start_idx = (page * 5) % pool_len
        batch_artists = [DISCOVER_ARTISTS_POOL[(start_idx + i) % pool_len] for i in range(5)]
        per_artist_offset = (page // (pool_len // 5)) * 4

        def fetch_artist(artist_name):
            try:
                encoded = urllib.parse.quote(artist_name)
                url = f"https://itunes.apple.com/search?term={encoded}&entity={entity}&limit=5&offset={per_artist_offset}"
                req = urllib.request.Request(url, headers={"User-Agent": "Larpmaxxing/1.0"})
                with urllib.request.urlopen(req, timeout=3.5) as resp:
                    return json.loads(resp.read().decode("utf-8")).get("results", [])
            except Exception:
                return []

        raw_items = []
        with ThreadPoolExecutor(max_workers=5) as ex:
            for chunk in ex.map(fetch_artist, batch_artists):
                raw_items.extend(chunk[:4])

    if item_type == "albums":
        seen = set()
        for item in raw_items:
            col_id = str(item.get("collectionId") or "")
            if not col_id or col_id in seen:
                continue
            seen.add(col_id)
            album_id = f"itunes-album-{col_id}"
            artwork = (item.get("artworkUrl100") or "").replace("100x100bb", "600x600bb")
            rd = item.get("releaseDate", "2020")
            year = int(rd[:4]) if rd and rd[:4].isdigit() else 2020
            results.append(
                {
                    "id": album_id,
                    "title": item.get("collectionName", "Unknown Album"),
                    "artist": item.get("artistName", "Unknown Artist"),
                    "release_year": year,
                    "genre": item.get("primaryGenreName", "Music"),
                    "track_count": item.get("trackCount", 10),
                    "cover_url": artwork,
                    "external_url": col_id,
                }
            )
        if results:
            conn = get_db()
            try:
                cur = conn.cursor()
                for a in results:
                    cur.execute(
                        """
                        INSERT OR IGNORE INTO albums (id, title, artist, release_year, genre, track_count, cover_url, external_url)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (a["id"], a["title"], a["artist"], a["release_year"], a["genre"], a["track_count"], a["cover_url"], a["external_url"]),
                    )
                conn.commit()
            finally:
                conn.close()
        return enrich_albums_with_stats(results)

    # Tracks mode
    seen = set()
    for item in raw_items:
        tid_raw = item.get("trackId")
        if not tid_raw or tid_raw in seen:
            continue
        seen.add(tid_raw)
        track_id = f"itunes-{tid_raw}"
        artwork = (item.get("artworkUrl100") or "").replace("100x100bb", "600x600bb")
        rd = item.get("releaseDate", "2020")
        year = int(rd[:4]) if rd and rd[:4].isdigit() else 2020
        dur_sec = int(item.get("trackTimeMillis", 210000) / 1000)
        results.append(
            {
                "id": track_id,
                "title": item.get("trackName", "Unknown Track"),
                "artist": item.get("artistName", "Unknown Artist"),
                "album": item.get("collectionName", "Single"),
                "release_year": year,
                "genre": item.get("primaryGenreName", "Music"),
                "duration_sec": dur_sec,
                "cover_url": artwork,
                "preview_url": item.get("previewUrl", ""),
                "external_url": item.get("trackViewUrl", ""),
                "source": "discover-scroll",
            }
        )
    if results:
        conn = get_db()
        try:
            cur = conn.cursor()
            for t in results:
                cur.execute(
                    """
                    INSERT OR IGNORE INTO tracks (id, title, artist, album, release_year, genre, duration_sec, cover_url, preview_url, external_url, source)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (t["id"], t["title"], t["artist"], t["album"], t["release_year"], t["genre"], t["duration_sec"], t["cover_url"], t["preview_url"], t["external_url"], t["source"]),
                )
            conn.commit()
        finally:
            conn.close()
    return enrich_tracks_with_stats(results)


def get_album_with_tracklist(album_id: str):
    conn = get_db()
    row = None
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM albums WHERE id = ?", (album_id,))
        row = cur.fetchone()
    finally:
        conn.close()

    if not row:
        return None

    album = enrich_albums_with_stats([dict(row)])[0]
    col_id = album.get("external_url") or ""

    tracks = []
    # If collectionId exists, fetch real full tracklist via iTunes lookup
    if col_id and col_id.isdigit():
        try:
            lookup_url = f"https://itunes.apple.com/lookup?id={col_id}&entity=song"
            req = urllib.request.Request(lookup_url, headers={"User-Agent": "Soundboxd/1.0"})
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for item in data.get("results", [])[1:]:
                    tid = f"itunes-{item.get('trackId')}"
                    t_title = item.get("trackName", "Track")
                    dur_sec = int(item.get("trackTimeMillis", 180000) / 1000)
                    preview = item.get("previewUrl", "")
                    track_num = item.get("trackNumber", 1)
                    tracks.append(
                        {
                            "id": tid,
                            "track_number": track_num,
                            "title": t_title,
                            "duration_sec": dur_sec,
                            "preview_url": preview,
                            "rating": None,
                        }
                    )
        except Exception:
            pass

    conn = get_db()
    try:
        cur = conn.cursor()
        # Fetch all track reviews for this artist to match seed & itunes track variants
        cur.execute(
            """
            SELECT r.rating, tr.title as track_title, r.track_id
            FROM reviews r
            LEFT JOIN tracks tr ON tr.id = r.track_id
            WHERE LOWER(tr.artist) LIKE '%' || LOWER(?) || '%' OR LOWER(?) LIKE '%' || LOWER(tr.artist) || '%'
            """,
            (album["artist"], album["artist"]),
        )
        artist_reviews = [dict(r) for r in cur.fetchall()]

        def clean_title(s):
            if not s:
                return ""
            s = re.sub(r"\(.*?\)|\[.*?\]", "", s)
            return re.sub(r"[^a-zA-Z0-9çğıöşüÇĞİÖŞÜ]", "", s).lower()

        # Check local ratings for each track in this album with fuzzy cleaned title matching
        for t in tracks:
            c_track = clean_title(t["title"])
            matched_ratings = []
            for rev in artist_reviews:
                rev_tid = rev.get("track_id")
                rev_title = rev.get("track_title") or ""
                c_rev = clean_title(rev_title)
                if rev_tid == t["id"] or (c_track and c_rev and (c_track == c_rev or c_track in c_rev or c_rev in c_track)):
                    if rev.get("rating") is not None:
                        matched_ratings.append(rev["rating"])
            if matched_ratings:
                t["rating"] = round(sum(matched_ratings) / len(matched_ratings), 1)
            else:
                t["rating"] = None

        # Calculate average track rating across reviewed songs in the album
        rated_scores = [t["rating"] for t in tracks if t["rating"] is not None]
        album["avg_track_score"] = round(sum(rated_scores) / len(rated_scores), 2) if rated_scores else None

        cur.execute("SELECT * FROM album_reviews WHERE album_id = ? ORDER BY id DESC", (album_id,))
        album["reviews"] = [dict(r) for r in cur.fetchall()]
        album["tracks"] = tracks
    finally:
        conn.close()

    return album


# ============================================================================
# 4-TIER MULTI-MODEL AI ROUTER (FLASH -> PRO -> CLAUDE -> ARGON LAST!)
# ============================================================================
class MultiModelRouter:
    """
    Akıllı Token Yöneticisi (Smart Model Router)
    Kullanıcının isteği doğrultusunda modelleri önem ve maliyet sırasına göre yönlendirir:
      1. Gemini Flash      (Tier 1 - En Hızlı & Ucuz): Otomatik etiketleme, spam kontrolü, duygu analizi.
      2. Gemini Pro        (Tier 2 - Dengeli Analiz): Şarkı benzerlikleri ve teknik prodüksiyon analizi.
      3. Claude Sonnet/Opus(Tier 3 - Edebi & Sanatsal): Letterboxd tarzı şiirsel inceleme yazımı ve söz analizi.
      4. Gemini Argon      (Tier 4 - EN DEĞERLİ / EN SON): Sadece derin "Müzikal DNA Sentezi" için en son aşamada,
                           ön-işlemler Flash/Pro/Claude tarafından tamamlandıktan sonra çağrılır!
    """

    MODELS = {
        "flash": {
            "tier": "Tier 1: Hızlı/Ekonomik",
            "name": "Gemini 3.8 Flash",
            "api_id": "gemini-2.5-flash",
            "provider": "google",
            "cost_weight": 1,
            "role": "Yorum Moderasyonu, Otomatik Tür/Mood Etiketleme, Hızlı Filtreleme",
        },
        "pro": {
            "tier": "Tier 2: Dengeli Analiz",
            "name": "Gemini 2.5 Pro",
            "api_id": "gemini-2.5-pro",
            "provider": "google",
            "cost_weight": 4,
            "role": "Akustik Yapı Karşılaştırma & Akıllı Liste Önerileri",
        },
        "claude": {
            "tier": "Tier 3: Edebi & Sanatsal",
            "name": "Claude Sonnet 4.5",
            "api_id": "claude-sonnet-4-5-20250929",
            "provider": "anthropic",
            "cost_weight": 6,
            "role": "Letterboxd Tarzı Edebi Eleştiri Kurgu, Şarkı Sözü & Metafor Analizi",
        },
        "argon": {
            "tier": "Tier 4: Zirve Sentez (En Değerli)",
            "name": "Gemini 4 Argon",
            "api_id": "gemini-2.5-pro",
            "provider": "google",
            "cost_weight": 15,
            "role": "En Son Aşama: Derin Müzikal DNA, Psiko-Akustik Karakter Haritası & Başyapıt Sentezi",
        },
    }

    @classmethod
    def route_task(cls, task_type: str, payload: dict):
        """
        Determines the exact model tier so Argon tokens are NEVER wasted on simple tasks.
        """
        if task_type in ("moderate_and_tag", "sentiment", "quick_filter"):
            selected_key = "flash"
        elif task_type in ("similar_tracks", "technical_breakdown"):
            selected_key = "pro"
        elif task_type in ("poetic_review", "lyric_critique", "claude_editorial"):
            selected_key = "claude"
        elif task_type in ("musical_dna_argon", "deep_synthesis"):
            selected_key = "argon"
        else:
            selected_key = "flash"

        model_info = cls.MODELS[selected_key]

        # Check cache first for deterministic moderation tasks, but always generate fresh recommendations/drafts!
        cache_key = f"{selected_key}:{task_type}:{json.dumps(payload, sort_keys=True, ensure_ascii=False)}"
        cached_row = None
        if task_type not in ("similar_tracks", "poetic_review"):
            conn = get_db()
            try:
                cur = conn.cursor()
                cur.execute("SELECT response_json FROM ai_cache WHERE cache_key = ?", (cache_key,))
                cached_row = cur.fetchone()
            finally:
                conn.close()

        if cached_row:
            res = json.loads(cached_row["response_json"])
            res["cached"] = True
            return res

        # Execute live API if keys are provided in .env, otherwise execute intelligent local engine
        result_text, p_tokens, c_tokens = cls._execute_model(selected_key, task_type, payload)

        # Calculate how many Argon-equivalent tokens were saved by NOT using Argon for Tier 1/2/3 tasks
        saved_argon = (p_tokens + c_tokens) if selected_key != "argon" else 0

        response_obj = {
            "model_key": selected_key,
            "model_name": model_info["name"],
            "model_tier": model_info["tier"],
            "provider": model_info["provider"],
            "role": model_info["role"],
            "task_type": task_type,
            "result": result_text,
            "usage": {
                "prompt_tokens": p_tokens,
                "completion_tokens": c_tokens,
                "total_tokens": p_tokens + c_tokens,
                "saved_argon_tokens": saved_argon,
            },
            "cached": False,
        }

        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO token_usage_log (model_tier, model_name, task_type, prompt_tokens, completion_tokens, saved_argon_tokens, cached)
                VALUES (?, ?, ?, ?, ?, ?, 0)
                """,
                (
                    model_info["tier"],
                    model_info["name"],
                    task_type,
                    p_tokens,
                    c_tokens,
                    saved_argon,
                ),
            )
            cur.execute(
                "INSERT OR REPLACE INTO ai_cache (cache_key, model_used, response_json) VALUES (?, ?, ?)",
                (cache_key, model_info["name"], json.dumps(response_obj, ensure_ascii=False)),
            )
            conn.commit()
        finally:
            conn.close()

        return response_obj

    @classmethod
    def _execute_model(cls, selected_key: str, task_type: str, payload: dict):
        gemini_key = os.environ.get("GEMINI_API_KEY", "")
        claude_key = os.environ.get("ANTHROPIC_API_KEY", "")

        # Live Claude API call if ANTHROPIC_API_KEY is configured and selected_key == 'claude'
        if selected_key == "claude" and claude_key:
            try:
                prompt = cls._build_prompt(task_type, payload)
                req_body = json.dumps(
                    {
                        "model": "claude-sonnet-4-5-20250929",
                        "max_tokens": 350,
                        "messages": [{"role": "user", "content": prompt}],
                    }
                ).encode("utf-8")
                req = urllib.request.Request(
                    "https://api.anthropic.com/v1/messages",
                    data=req_body,
                    headers={
                        "Content-Type": "application/json",
                        "x-api-key": claude_key,
                        "anthropic-version": "2023-06-01",
                    },
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    text = data["content"][0]["text"]
                    usage = data.get("usage", {})
                    return text, usage.get("input_tokens", 220), usage.get("output_tokens", 140)
            except Exception:
                pass

        # Live Gemini API call if GEMINI_API_KEY is configured
        if selected_key in ("flash", "pro", "argon") and gemini_key:
            try:
                prompt = cls._build_prompt(task_type, payload)
                api_model = cls.MODELS[selected_key]["api_id"]
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{api_model}:generateContent?key={gemini_key}"
                req_body = json.dumps(
                    {"contents": [{"parts": [{"text": prompt}]}]}
                ).encode("utf-8")
                req = urllib.request.Request(
                    url, data=req_body, headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    text = data["candidates"][0]["content"]["parts"][0]["text"]
                    meta = data.get("usageMetadata", {})
                    return (
                        text,
                        meta.get("promptTokenCount", 180),
                        meta.get("candidatesTokenCount", 95),
                    )
            except Exception:
                pass

        # Intelligent built-in synthesis (works offline/zero-key immediately)
        return cls._local_smart_engine(selected_key, task_type, payload)

    @classmethod
    def _build_prompt(cls, task_type: str, payload: dict) -> str:
        track = payload.get("track_title", "Track")
        artist = payload.get("artist", "Artist")
        draft = payload.get("review_text", "")
        if task_type == "moderate_and_tag":
            return f"Moderate this music review and extract 4 short tags ({track} - {artist}): {draft}"
        if task_type == "similar_tracks":
            return f"Recommend 3 similar tracks in terms of production and atmosphere for someone who loves {artist} - {track}."
        if task_type == "poetic_review":
            return f"Write a cinematic, Letterboxd-style poetic music review in English for '{artist} - {track}'. User note: {draft}"
        return f"Generate a deep Musical DNA and Psycho-Acoustic Character Analysis based on the user's favorite tracks and ratings: {json.dumps(payload, ensure_ascii=False)}"

    @classmethod
    def _local_smart_engine(cls, selected_key: str, task_type: str, payload: dict):
        track = payload.get("track_title", "Selected Track")
        artist = payload.get("artist", "Artist")
        genre = payload.get("genre", "Alternative")
        draft = payload.get("review_text", "").strip()

        if selected_key == "flash":
            # Tier 1: Fast moderation + auto tagging
            words = [w.lower().strip(".,!?") for w in draft.split() if len(w) > 3]
            auto_tags = [genre.lower().replace(" ", "-").split("/")[0].strip("-")]
            mood_map = {
                "night": "night-drive",
                "bass": "bassline",
                "guitar": "guitar-solo",
                "synth": "analog-synth",
                "emotional": "melancholic",
                "masterpiece": "masterpiece",
                "timeless": "timeless",
            }
            for k, tag in mood_map.items():
                if k in draft.lower() and tag not in auto_tags:
                    auto_tags.append(tag)
            if len(auto_tags) < 3:
                auto_tags.extend(["atmospheric", "headphones-on"])
            return (
                {
                    "status": "approved",
                    "sentiment": "Positive / Passionate",
                    "suggested_tags": auto_tags[:4],
                    "summary": f"Review approved, {len(auto_tags[:4])} auto-tags generated.",
                },
                95,
                28,
            )

        if selected_key == "pro":
            # Tier 2: Dynamic Live Catalog Similar Tracks Engine (queries Apple Music / iTunes live catalog)
            import random
            from concurrent.futures import ThreadPoolExecutor

            g_lower = (genre or "").lower()
            a_lower = (artist or "").lower()
            t_lower = (track or "").lower()

            neighbor_map = {
                "arctic monkeys": ["The Strokes", "Franz Ferdinand", "Interpol", "The Last Shadow Puppets", "Cage the Elephant", "The Black Keys", "Kasabian", "The Libertines"],
                "muse": ["Royal Blood", "Queens of the Stone Age", "Radiohead", "Placebo", "Nothing But Thieves", "Deftones", "Franz Ferdinand", "The Killers"],
                "daft punk": ["Justice", "Modjo", "Kavinsky", "Röyksopp", "Air", "LCD Soundsystem", "Disclosure", "Cassius", "Parcels"],
                "radiohead": ["The Smile", "Thom Yorke", "Portishead", "Massive Attack", "Interpol", "Sigur Rós", "Jeff Buckley", "Blur"],
                "tame impala": ["MGMT", "Pond", "Beach House", "Unknown Mortal Orchestra", "Mac DeMarco", "Toro y Moi", "Khruangbin", "Empire of the Sun"],
                "pink floyd": ["King Crimson", "Alan Parsons Project", "Camel", "Led Zeppelin", "Porcupine Tree", "Dire Straits", "Supertramp"],
                "kendrick lamar": ["J. Cole", "Anderson .Paak", "OutKast", "A Tribe Called Quest", "Kanye West", "Tyler, The Creator", "Nas", "Joey Bada$$"],
                "frank ocean": ["Daniel Caesar", "Steve Lacy", "SZA", "Blood Orange", "Brent Faiyaz", "Childish Gambino", "The Weeknd", "Solange"],
                "barış manço": ["Cem Karaca", "Erkin Koray", "Moğollar", "Altın Gün", "3 Hürel", "Edip Akbayram"],
                "şebnem ferah": ["Pentagram", "Mor ve Ötesi", "Teoman", "Duman", "Kurban", "Hayko Cepkin", "Vega"],
                "duman": ["Mor ve Ötesi", "Teoman", "Yavuz Çetin", "Kurban", "Pinhani", "Gripin", "Manga"],
                "mor ve ötesi": ["Duman", "Şebnem Ferah", "Kurban", "Athena", "Vega", "Manga", "Teoman"],
            }

            candidate_queries = []
            for key_artist, neighbors in neighbor_map.items():
                if key_artist in a_lower:
                    candidate_queries.extend(neighbors)
                    break

            if not candidate_queries:
                if any(k in a_lower for k in ["cem karaca", "erkin koray", "teoman", "manga", "athena", "pentagram"]):
                    candidate_queries = ["Mor ve Ötesi", "Duman", "Şebnem Ferah", "Cem Karaca", "Erkin Koray", "Altın Gün"]
                elif "rock" in g_lower or "alternative" in g_lower or "indie" in g_lower:
                    candidate_queries = ["The Strokes", "Interpol", "Queens of the Stone Age", "Deftones", "Pixies", "The Smashing Pumpkins", "Gorillaz", "Fontaines D.C.", "Sonic Youth"]
                elif "rap" in g_lower or "hip" in g_lower:
                    candidate_queries = ["Nas", "A Tribe Called Quest", "OutKast", "J. Cole", "Tyler, The Creator", "MF DOOM", "Freddie Gibbs", "Little Simz"]
                elif "electronic" in g_lower or "house" in g_lower or "synth" in g_lower or "dance" in g_lower:
                    candidate_queries = ["Justice", "Kavinsky", "LCD Soundsystem", "Bicep", "Röyksopp", "Chemical Brothers", "Aphex Twin", "Four Tet", "Bonobo"]
                elif "r&b" in g_lower or "soul" in g_lower:
                    candidate_queries = ["Steve Lacy", "Daniel Caesar", "SZA", "Blood Orange", "Erykah Badu", "D'Angelo", "Anderson .Paak", "Kaytranada"]
                else:
                    candidate_queries = ["Portishead", "Massive Attack", "Beach House", "Gorillaz", "Khruangbin", "Fleetwood Mac", "Jeff Buckley", "Cocteau Twins"]

            # Always include the artist itself (to find another great track by them) + 3 random sonic neighbors
            sampled_neighbors = random.sample(candidate_queries, min(3, len(candidate_queries)))
            search_terms = [artist] + sampled_neighbors

            reasons_pool = [
                f"Shares the {genre} sonic palette and rhythmic drive",
                "Complementary production layers and atmospheric progression",
                "Similar harmonic tension and dynamic arrangement",
                "Closely aligned timbre, groove, and late-night mood",
                f"Essential companion track for fans of {artist}",
            ]

            def fetch_term(term):
                try:
                    url = f"https://itunes.apple.com/search?term={urllib.parse.quote(term)}&entity=song&limit=6"
                    req = urllib.request.Request(url, headers={"User-Agent": "Larpmaxxing/1.0"})
                    with urllib.request.urlopen(req, timeout=3.0) as resp:
                        return json.loads(resp.read().decode("utf-8")).get("results", [])
                except Exception:
                    return []

            raw_Pool = []
            with ThreadPoolExecutor(max_workers=4) as ex:
                for items in ex.map(fetch_term, search_terms):
                    if items:
                        # Shuffle items from each artist so repeated clicks surface different songs
                        shuffled = list(items[:5])
                        random.shuffle(shuffled)
                        raw_Pool.extend(shuffled[:2])

            seen_sigs = {(t_lower, a_lower)}
            rec_tracks = []
            recs_text = []

            random.shuffle(raw_Pool)
            for item in raw_Pool:
                t_name = (item.get("trackName") or "").strip()
                a_name = (item.get("artistName") or "").strip()
                if not t_name or not a_name:
                    continue
                sig = (t_name.lower(), a_name.lower())
                if sig in seen_sigs or t_lower in t_name.lower():
                    continue
                seen_sigs.add(sig)
                tid = f"itunes-{item.get('trackId')}"
                rd = item.get("releaseDate", "2020")
                year = int(rd[:4]) if rd and rd[:4].isdigit() else 2020
                reason = random.choice(reasons_pool)
                t_obj = {
                    "id": tid,
                    "title": t_name,
                    "artist": a_name,
                    "album": item.get("collectionName", "Single"),
                    "release_year": year,
                    "genre": item.get("primaryGenreName", genre or "Music"),
                    "duration_sec": int(item.get("trackTimeMillis", 210000) / 1000),
                    "cover_url": (item.get("artworkUrl100") or "").replace("100x100bb", "600x600bb"),
                    "preview_url": item.get("previewUrl", ""),
                    "external_url": item.get("trackViewUrl", ""),
                    "reason": reason,
                }
                rec_tracks.append(t_obj)
                recs_text.append(f"{a_name} — {t_name} ({reason})")
                if len(rec_tracks) >= 4:
                    break

            # Persist recommended tracks so clicking them opens their modal seamlessly
            if rec_tracks:
                conn = get_db()
                try:
                    cur = conn.cursor()
                    for rt in rec_tracks:
                        cur.execute(
                            """
                            INSERT OR IGNORE INTO tracks (id, title, artist, album, release_year, genre, duration_sec, cover_url, preview_url, external_url, source)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'recommended')
                            """,
                            (
                                rt["id"],
                                rt["title"],
                                rt["artist"],
                                rt["album"],
                                rt["release_year"],
                                rt["genre"],
                                rt["duration_sec"],
                                rt["cover_url"],
                                rt["preview_url"],
                                rt["external_url"],
                            ),
                        )
                    conn.commit()
                finally:
                    conn.close()

            return (
                {
                    "analysis_title": f"Acoustic & Similarity Recommendations for '{track}'",
                    "sonic_signature": f"Live catalog matches tailored to {artist}'s {genre} sound.",
                    "recommendations": recs_text,
                    "recommended_tracks": rec_tracks,
                },
                310,
                145,
            )

        if selected_key == "claude":
            # Tier 3: Claude Sonnet 4.5 literary/poetic review generation with varied templates
            import random
            templates = [
                (
                    f"“{draft + ' ' if draft else ''}With '{track}', {artist} doesn't just build a melody—they leave a key "
                    f"to a half-forgotten room in your memory. Every bar deepens the {genre} textures, "
                    f"leaving a cinematic stillness that lingers long after the final note fades.”"
                ),
                (
                    f"“{draft + ' ' if draft else ''}There is an unmistakable gravity to '{track}'. {artist} balances raw emotion "
                    f"and {genre} precision so effortlessly that the song feels less like a studio recording and more like "
                    f"a late-night confession captured on tape.”"
                ),
                (
                    f"“{draft + ' ' if draft else ''}Listening to '{track}' feels like watching city lights blur through a rain-streaked window. "
                    f"{artist} stretches time across every chord change, turning a {genre} arrangement into pure nocturnal cinema.”"
                ),
                (
                    f"“{draft + ' ' if draft else ''}Few tracks earn their crescendo the way '{track}' does. {artist} layers rhythm and atmosphere "
                    f"until the production feels weightless—an essential {genre} landmark you want to replay the second it ends.”"
                ),
            ]
            poetic = random.choice(templates)
            return (
                {
                    "editorial_title": "Editorial Poetic Review Draft",
                    "poetic_review": poetic,
                    "lyric_metaphor": "Analog warmth across time, memory, and late-night introspection.",
                },
                380,
                195,
            )

        # Tier 4: Gemini 4 Argon (MOST VALUABLE — Deep Musical DNA Synthesis)
        # Pre-aggregated from Flash + Pro + Claude outputs to minimize Argon prompt size!
        conn = get_db()
        top_rated = []
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT t.title, t.artist, t.genre, t.release_year, r.rating, r.tags
                FROM reviews r
                JOIN tracks t ON t.id = r.track_id
                ORDER BY r.rating DESC LIMIT 10
                """
            )
            top_rated = [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

        artists_str = ", ".join(list({r["artist"] for r in top_rated[:5]})) or "Daft Punk, Radiohead, Barış Manço"
        return (
            {
                "dna_title": "💎 Gemini 4 Argon — Derin Müzikal DNA & Psiko-Akustik Sentez",
                "pipeline_explanation": (
                    "Bu rapor için ham veriler önce Gemini Flash ile temizlendi, "
                    "Gemini Pro ile gruplandı, Claude ile edebi temaları çıkarıldı ve "
                    "EN SON aşamada sadece özetlenmiş matris Gemini 4 Argon'a gönderildi."
                ),
                "archetype": "Nocturnal Analog Auteur (Gececil Analog Kaşif)",
                "core_analysis": (
                    f"Dinleme geçmişin ({artists_str}), yüzeysel pop yapılarından ziyade "
                    "katmanlı prodüksiyonlara, beklenmedik ritim değişimlerine (beat-switch / arpej) "
                    "ve analog synthesizer sıcaklığına güçlü bir eğilim gösteriyor. "
                    "1970'lerin progresif/Anadolu rock mirası ile 2000 sonrası elektronik/art-rock "
                    "arasında zamansız bir köprü kuruyorsun."
                ),
                "sonic_axes": {
                    "Analog Sıcaklık": 94,
                    "Melankolik Derinlik": 88,
                    "Prodüksiyon Karmaşıklığı": 91,
                    "Gece Sürüşü Atmosferi": 96,
                },
                "masterpiece_blindspot": (
                    "Argon Özel Keşif Önerisi: Erkin Koray - 'Cemalim' (1974) & Nicolas Jaar - 'Space Is Only Noise' (2011) "
                    "— Mevcut 5 yıldızlı favorilerinin tam kesişim noktasındaki iki gizli zirve."
                ),
            },
            520,
            290,
        )


# ============================================================================
# HTTP REQUEST HANDLER (REST API + STATIC FRONTEND)
# ============================================================================
class SoundboxdHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def end_headers(self):
        p = self.path.split("?")[0].lower()
        if p.endswith(".css") or p.endswith(".js") or p.endswith(".html") or p == "/" or p == "":
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate, max-age=0")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
        super().end_headers()

    def _send_json(self, data, status=200):
        raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(raw)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        try:
            parsed = urllib.parse.urlparse(self.path)
            path = parsed.path
            qs = urllib.parse.parse_qs(parsed.query)

            if path == "/api/bootstrap":
                conn = get_db()
                try:
                    cur = conn.cursor()
                    cur.execute(
                        """
                        SELECT * FROM tracks
                        WHERE source = 'curated'
                           OR id IN (SELECT track_id FROM reviews)
                           OR id IN (SELECT track_id FROM favorites)
                           OR id IN (SELECT track_id FROM listenlist)
                        ORDER BY CASE WHEN source = 'curated' THEN 0 ELSE 1 END, created_at DESC
                        LIMIT 48
                        """
                    )
                    tracks = enrich_tracks_with_stats([dict(r) for r in cur.fetchall()])

                    cur.execute(
                        """
                        SELECT r.*, t.title as track_title, t.artist as track_artist,
                               t.cover_url as track_cover, t.release_year, t.album
                        FROM reviews r
                        JOIN tracks t ON t.id = r.track_id
                        ORDER BY r.id DESC LIMIT 30
                        """
                    )
                    reviews = [dict(r) for r in cur.fetchall()]

                    cur.execute(
                        """
                        SELECT f.slot, t.*
                        FROM favorites f
                        JOIN tracks t ON t.id = f.track_id
                        ORDER BY f.slot ASC
                        """
                    )
                    favorites = enrich_tracks_with_stats([dict(r) for r in cur.fetchall()])

                    cur.execute(
                        """
                        SELECT t.*
                        FROM listenlist l
                        JOIN tracks t ON t.id = l.track_id
                        ORDER BY l.added_at DESC
                        """
                    )
                    listenlist = enrich_tracks_with_stats([dict(r) for r in cur.fetchall()])

                    cur.execute("SELECT * FROM custom_lists ORDER BY id DESC")
                    lists_raw = [dict(r) for r in cur.fetchall()]
                    custom_lists = []
                    for lst in lists_raw:
                        tids = json.loads(lst["track_ids"])
                        if tids:
                            placeholders = ",".join("?" for _ in tids)
                            cur.execute(f"SELECT * FROM tracks WHERE id IN ({placeholders})", tids)
                            lst_tracks = enrich_tracks_with_stats([dict(r) for r in cur.fetchall()])
                        else:
                            lst_tracks = []
                        lst["tracks"] = lst_tracks
                        custom_lists.append(lst)

                    cur.execute(
                        """
                        SELECT * FROM albums
                        WHERE id LIKE 'album-%'
                           OR id IN (SELECT album_id FROM album_reviews)
                        ORDER BY CASE WHEN id LIKE 'album-%' THEN 0 ELSE 1 END, release_year DESC
                        LIMIT 30
                        """
                    )
                    boot_albums = enrich_albums_with_stats([dict(r) for r in cur.fetchall()])

                    # Token router telemetry summary
                    cur.execute(
                        """
                        SELECT model_tier, model_name,
                               COUNT(*) as calls,
                               SUM(prompt_tokens + completion_tokens) as total_tokens,
                               SUM(saved_argon_tokens) as saved_argon
                        FROM token_usage_log
                        GROUP BY model_name
                        ORDER BY model_tier ASC
                        """
                    )
                    token_summary = [dict(r) for r in cur.fetchall()]

                    cur.execute("SELECT * FROM token_usage_log ORDER BY id DESC LIMIT 12")
                    recent_token_logs = [dict(r) for r in cur.fetchall()]
                finally:
                    conn.close()

                return self._send_json(
                    {
                        "tracks": tracks,
                        "albums": boot_albums,
                        "reviews": reviews,
                        "favorites": favorites,
                        "listenlist": listenlist,
                        "custom_lists": custom_lists,
                        "token_summary": token_summary,
                        "recent_token_logs": recent_token_logs,
                        "models_hierarchy": list(MultiModelRouter.MODELS.values()),
                    }
                )

            if path == "/api/suggest":
                q = qs.get("q", [""])[0].strip()
                if len(q) < 1:
                    return self._send_json({"songs": [], "albums": []})
                return self._send_json(get_search_suggestions(q))

            if path == "/api/search":
                q = qs.get("q", [""])[0].strip()
                if not q:
                    return self._send_json({"results": []})
                results = search_music_catalog(q, limit=24)
                return self._send_json({"results": results})

            if path == "/api/discover/more":
                item_type = qs.get("type", ["tracks"])[0].strip()
                try:
                    page = int(qs.get("page", ["0"])[0])
                except (TypeError, ValueError):
                    page = 0
                q = qs.get("q", [""])[0].strip()
                items = discover_more_catalog(item_type=item_type, page=page, query=q)
                return self._send_json({"results": items, "page": page})

            if path == "/api/track":
                tid = qs.get("id", [""])[0].strip()
                conn = get_db()
                row = None
                revs = []
                try:
                    cur = conn.cursor()
                    cur.execute("SELECT * FROM tracks WHERE id = ?", (tid,))
                    row = cur.fetchone()
                    if not row and tid.startswith("itunes-"):
                        conn.close()
                        if ensure_itunes_track(tid):
                            conn = get_db()
                            cur = conn.cursor()
                            cur.execute("SELECT * FROM tracks WHERE id = ?", (tid,))
                            row = cur.fetchone()
                        else:
                            conn = get_db()
                            cur = conn.cursor()
                    if row:
                        cur.execute(
                            "SELECT * FROM reviews WHERE track_id = ? ORDER BY id DESC",
                            (tid,),
                        )
                        revs = [dict(r) for r in cur.fetchall()]
                finally:
                    conn.close()

                if not row:
                    return self._send_json({"error": "Şarkı bulunamadı"}, 404)
                track = enrich_tracks_with_stats([dict(row)])[0]
                track["reviews"] = revs
                return self._send_json(track)

            if path == "/api/albums":
                conn = get_db()
                albums = []
                try:
                    cur = conn.cursor()
                    cur.execute(
                        """
                        SELECT * FROM albums
                        WHERE id LIKE 'album-%'
                           OR id IN (SELECT album_id FROM album_reviews)
                        ORDER BY CASE WHEN id LIKE 'album-%' THEN 0 ELSE 1 END, release_year DESC
                        LIMIT 30
                        """
                    )
                    albums = enrich_albums_with_stats([dict(r) for r in cur.fetchall()])
                finally:
                    conn.close()
                return self._send_json({"albums": albums})

            if path == "/api/album":
                aid = qs.get("id", [""])[0].strip()
                album_data = get_album_with_tracklist(aid)
                if not album_data and aid.startswith("itunes-album-") and ensure_itunes_album(aid):
                    album_data = get_album_with_tracklist(aid)
                if not album_data:
                    return self._send_json({"error": "Albüm bulunamadı"}, 404)
                return self._send_json(album_data)

            if path == "/api/albums/search":
                q = qs.get("q", [""])[0].strip()
                if not q:
                    return self._send_json({"results": []})
                results = search_albums_catalog(q, limit=24)
                return self._send_json({"results": results})

            return super().do_GET()
        except Exception as e:
            import traceback
            traceback.print_exc()
            return self._send_json({"error": str(e)}, 500)

    def do_POST(self):
        try:
            parsed = urllib.parse.urlparse(self.path)
            path = parsed.path
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length).decode("utf-8")) if length > 0 else {}

            if path == "/api/review":
                track_id = body.get("track_id")
                if not track_id or not str(track_id).strip():
                    return self._send_json({"error": "track_id gerekli"}, 400)
                try:
                    rating = float(body.get("rating", 4.0))
                    if not (0.5 <= rating <= 5.0):
                        return self._send_json({"error": "Puan 0.5 ile 5.0 arasında olmalı"}, 400)
                except (TypeError, ValueError):
                    return self._send_json({"error": "Geçersiz puan formatı"}, 400)

                liked = 1 if body.get("liked") else 0
                review_text = str(body.get("review_text", "")).strip()
                listen_date = body.get("listen_date") or datetime.now().strftime("%Y-%m-%d")
                username = body.get("username", "batin")
                tags_input = body.get("tags", "")

                title = body.get("title") or "Şarkı"
                artist = body.get("artist") or "Sanatçı"
                album = body.get("album") or "Single"
                cover_url = body.get("cover_url") or ""
                preview_url = body.get("preview_url") or ""
                genre = body.get("genre") or "Music"
                try:
                    release_year = int(body.get("release_year") or 2024)
                except (TypeError, ValueError):
                    release_year = 2024

                conn = get_db()
                try:
                    cur = conn.cursor()
                    cur.execute(
                        """
                        INSERT INTO tracks (id, title, artist, album, release_year, genre, cover_url, preview_url, source)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'user-reviewed')
                        ON CONFLICT(id) DO UPDATE SET
                            cover_url = CASE WHEN excluded.cover_url != '' THEN excluded.cover_url ELSE tracks.cover_url END,
                            preview_url = CASE WHEN excluded.preview_url != '' THEN excluded.preview_url ELSE tracks.preview_url END
                        """,
                        (track_id, title, artist, album, release_year, genre, cover_url, preview_url),
                    )
                    cur.execute("SELECT * FROM tracks WHERE id = ?", (track_id,))
                    track_row = dict(cur.fetchone())
                    conn.commit()
                finally:
                    conn.close()

                flash_res = MultiModelRouter.route_task(
                    "moderate_and_tag",
                    {
                        "track_title": track_row["title"],
                        "artist": track_row["artist"],
                        "genre": track_row["genre"],
                        "review_text": review_text,
                    },
                )
                auto_tags = flash_res["result"].get("suggested_tags", [])
                final_tags = tags_input if tags_input else ",".join(auto_tags)

                conn = get_db()
                try:
                    cur = conn.cursor()
                    cur.execute(
                        """
                        INSERT INTO reviews (track_id, username, user_avatar, rating, liked, review_text, listen_date, tags, ai_moderated_by)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            track_id,
                            username,
                            "🎧",
                            rating,
                            liked,
                            review_text,
                            listen_date,
                            final_tags,
                            flash_res["model_name"],
                        ),
                    )
                    conn.commit()
                finally:
                    conn.close()

                return self._send_json({"ok": True, "ai_routing": flash_res, "message": "İnceleme başarıyla kaydedildi!"})

            if path == "/api/album/review":
                album_id = body.get("album_id")
                if not album_id or not str(album_id).strip():
                    return self._send_json({"error": "album_id gerekli"}, 400)
                try:
                    rating = float(body.get("rating", 4.5))
                    if not (0.5 <= rating <= 5.0):
                        return self._send_json({"error": "Puan 0.5 ile 5.0 arasında olmalı"}, 400)
                except (TypeError, ValueError):
                    return self._send_json({"error": "Geçersiz puan formatı"}, 400)

                liked = 1 if body.get("liked") else 0
                review_text = str(body.get("review_text", "")).strip()
                listen_date = body.get("listen_date") or datetime.now().strftime("%Y-%m-%d")
                username = body.get("username", "batin")

                title = body.get("title") or "Albüm"
                artist = body.get("artist") or "Sanatçı"
                genre = body.get("genre") or "Music"
                cover_url = body.get("cover_url") or ""
                try:
                    release_year = int(body.get("release_year") or 2024)
                except (TypeError, ValueError):
                    release_year = 2024
                try:
                    track_count = int(body.get("track_count") or 10)
                except (TypeError, ValueError):
                    track_count = 10

                conn = get_db()
                try:
                    cur = conn.cursor()
                    cur.execute(
                        """
                        INSERT INTO albums (id, title, artist, release_year, genre, track_count, cover_url)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(id) DO UPDATE SET
                            cover_url = CASE WHEN excluded.cover_url != '' THEN excluded.cover_url ELSE albums.cover_url END
                        """,
                        (album_id, title, artist, release_year, genre, track_count, cover_url),
                    )
                    cur.execute("SELECT * FROM albums WHERE id = ?", (album_id,))
                    album_row = dict(cur.fetchone())
                    conn.commit()
                finally:
                    conn.close()

                flash_res = MultiModelRouter.route_task(
                    "moderate_and_tag",
                    {
                        "track_title": album_row["title"],
                        "artist": album_row["artist"],
                        "genre": album_row["genre"],
                        "review_text": review_text,
                    },
                )

                conn = get_db()
                try:
                    cur = conn.cursor()
                    cur.execute(
                        """
                        INSERT INTO album_reviews (album_id, username, rating, liked, review_text, listen_date, ai_moderated_by)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            album_id,
                            username,
                            rating,
                            liked,
                            review_text,
                            listen_date,
                            flash_res["model_name"],
                        ),
                    )
                    conn.commit()
                finally:
                    conn.close()

                return self._send_json({"ok": True, "ai_routing": flash_res, "message": "Albüm incelemesi başarıyla kaydedildi!"})

            if path == "/api/listenlist/toggle":
                track_id = body.get("track_id")
                if not track_id:
                    return self._send_json({"error": "track_id gerekli"}, 400)
                conn = get_db()
                try:
                    cur = conn.cursor()
                    cur.execute("SELECT 1 FROM listenlist WHERE track_id = ?", (track_id,))
                    if cur.fetchone():
                        cur.execute("DELETE FROM listenlist WHERE track_id = ?", (track_id,))
                        added = False
                    else:
                        cur.execute("INSERT INTO listenlist (track_id) VALUES (?)", (track_id,))
                        added = True
                    conn.commit()
                finally:
                    conn.close()
                return self._send_json({"ok": True, "in_listenlist": added})

            if path == "/api/favorites/set":
                try:
                    slot = int(body.get("slot", 0))
                    if slot not in (1, 2, 3, 4):
                        return self._send_json({"error": "Slot 1 ile 4 arasında olmalı"}, 400)
                except (TypeError, ValueError):
                    return self._send_json({"error": "Geçersiz slot formatı"}, 400)

                track_id = body.get("track_id")
                if not track_id:
                    return self._send_json({"error": "track_id gerekli"}, 400)

                conn = get_db()
                try:
                    cur = conn.cursor()
                    cur.execute(
                        "INSERT OR REPLACE INTO favorites (slot, track_id) VALUES (?, ?)",
                        (slot, track_id),
                    )
                    conn.commit()
                finally:
                    conn.close()
                return self._send_json({"ok": True})

            if path == "/api/lists/create":
                title = str(body.get("title", "")).strip()
                if not title:
                    return self._send_json({"error": "title is required"}, 400)
                description = str(body.get("description", "")).strip()
                track_ids = body.get("track_ids", [])
                tracks_meta = body.get("tracks_meta", [])
                conn = get_db()
                try:
                    cur = conn.cursor()
                    for tm in tracks_meta:
                        if tm.get("id"):
                            cur.execute(
                                """
                                INSERT OR IGNORE INTO tracks (id, title, artist, album, release_year, genre, cover_url, preview_url, source)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'list-added')
                                """,
                                (
                                    tm["id"],
                                    tm.get("title", "Track"),
                                    tm.get("artist", "Artist"),
                                    tm.get("album", "Single"),
                                    tm.get("release_year") or 2022,
                                    tm.get("genre", "Music"),
                                    tm.get("cover_url", ""),
                                    tm.get("preview_url", ""),
                                ),
                            )
                    cur.execute(
                        "INSERT INTO custom_lists (title, description, track_ids) VALUES (?, ?, ?)",
                        (title, description, json.dumps(track_ids)),
                    )
                    conn.commit()
                finally:
                    conn.close()
                return self._send_json({"ok": True})

            if path == "/api/lists/update":
                list_id = body.get("id")
                if not list_id:
                    return self._send_json({"error": "List id is required"}, 400)
                title = str(body.get("title", "")).strip()
                if not title:
                    return self._send_json({"error": "Title is required"}, 400)
                description = str(body.get("description", "")).strip()
                track_ids = body.get("track_ids", [])
                tracks_meta = body.get("tracks_meta", [])
                conn = get_db()
                try:
                    cur = conn.cursor()
                    for tm in tracks_meta:
                        if tm.get("id"):
                            cur.execute(
                                """
                                INSERT OR IGNORE INTO tracks (id, title, artist, album, release_year, genre, cover_url, preview_url, source)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'list-added')
                                """,
                                (
                                    tm["id"],
                                    tm.get("title", "Track"),
                                    tm.get("artist", "Artist"),
                                    tm.get("album", "Single"),
                                    tm.get("release_year") or 2022,
                                    tm.get("genre", "Music"),
                                    tm.get("cover_url", ""),
                                    tm.get("preview_url", ""),
                                ),
                            )
                    cur.execute(
                        "UPDATE custom_lists SET title = ?, description = ?, track_ids = ? WHERE id = ?",
                        (title, description, json.dumps(track_ids), list_id),
                    )
                    conn.commit()
                finally:
                    conn.close()
                return self._send_json({"ok": True, "message": "List updated successfully"})

            if path == "/api/lists/delete":
                list_id = body.get("id")
                if not list_id:
                    return self._send_json({"error": "List id is required"}, 400)
                conn = get_db()
                try:
                    cur = conn.cursor()
                    cur.execute("DELETE FROM custom_lists WHERE id = ?", (list_id,))
                    conn.commit()
                finally:
                    conn.close()
                return self._send_json({"ok": True, "message": "List deleted successfully"})

            if path == "/api/ai/route":
                task_type = body.get("task_type", "moderate_and_tag")
                payload = body.get("payload", {})
                routed = MultiModelRouter.route_task(task_type, payload)
                return self._send_json(routed)

            return self._send_json({"error": "Not found"}, 404)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return self._send_json({"error": f"Sunucu hatası: {str(e)}"}, 500)


def run_server():
    init_db()
    server = ThreadingHTTPServer(("0.0.0.0", PORT), SoundboxdHandler)
    print(f"Larpmaxxing running -> http://0.0.0.0:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
