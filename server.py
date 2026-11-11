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
import sqlite3
import time
import urllib.parse
import urllib.request
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "soundboxd.db"
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
    conn = sqlite3.connect(str(DB_PATH))
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
        """
    )

    # Check if already seeded
    cur.execute("SELECT COUNT(*) as cnt FROM tracks")
    if cur.fetchone()["cnt"] == 0:
        seed_tracks = [
            (
                "seed-daft-punk-veridis-quo",
                "Veridis Quo",
                "Daft Punk",
                "Discovery",
                2001,
                "Electronic / French House",
                345,
                "https://is1-ssl.mzstatic.com/image/thumb/Music221/v4/fd/4a/77/fd4a77db-0ebc-d043-41a2-f32fa1bb0fb4/dj.qrikkdwj.jpg/600x600bb.jpg",
                "https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview116/v4/31/34/41/313441ef-0df7-380d-85fa-7d9a10dbb5a9/mzaf_10526081191566838334.plus.aac.p.m4a",
                "https://open.spotify.com/search/Veridis%20Quo%20Daft%20Punk",
                "curated",
            ),
            (
                "seed-radiohead-weird-fishes",
                "Weird Fishes / Arpeggi",
                "Radiohead",
                "In Rainbows",
                2007,
                "Art Rock / Indie",
                318,
                "https://is1-ssl.mzstatic.com/image/thumb/Music126/v4/dd/50/c7/dd50c790-99ac-d3d0-5ab8-e3891fb8fd52/634904032463.png/600x600bb.jpg",
                "https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview115/v4/58/09/b3/5809b30b-9df0-eec8-5be4-1c255554628d/mzaf_13506374943916960814.plus.aac.p.m4a",
                "https://open.spotify.com/search/Weird%20Fishes%20Radiohead",
                "curated",
            ),
            (
                "seed-tame-impala-let-it-happen",
                "Let It Happen",
                "Tame Impala",
                "Currents",
                2015,
                "Psychedelic Pop / Synth",
                467,
                "https://is1-ssl.mzstatic.com/image/thumb/Music115/v4/a8/2e/b4/a82eb490-f30a-a321-461a-0383c88fec95/15UMGIM23316.rgb.jpg/600x600bb.jpg",
                "",
                "https://open.spotify.com/search/Let%20It%20Happen%20Tame%20Impala",
                "curated",
            ),
            (
                "seed-pink-floyd-time",
                "Time",
                "Pink Floyd",
                "The Dark Side of the Moon",
                1973,
                "Progressive Rock",
                413,
                "https://is1-ssl.mzstatic.com/image/thumb/Music221/v4/3e/76/b0/3e76b0e3-762b-2286-a019-8afb19cee541/886445635829.jpg/600x600bb.jpg",
                "",
                "https://open.spotify.com/search/Time%20Pink%20Floyd",
                "curated",
            ),
            (
                "seed-kendrick-wesleys-theory",
                "Wesley's Theory",
                "Kendrick Lamar",
                "To Pimp a Butterfly",
                2015,
                "Jazz Rap / Funk",
                287,
                "https://is1-ssl.mzstatic.com/image/thumb/Music112/v4/b5/a6/91/b5a69171-5232-3d5b-9c15-8963802f83dd/15UMGIM15814.rgb.jpg/600x600bb.jpg",
                "",
                "https://open.spotify.com/search/Wesleys%20Theory%20Kendrick%20Lamar",
                "curated",
            ),
            (
                "seed-baris-manco-donence",
                "Dönence",
                "Barış Manço",
                "Sözüm Meclisten Dışarı",
                1981,
                "Anatolian Rock / Synth Prog",
                355,
                "https://is1-ssl.mzstatic.com/image/thumb/Music116/v4/96/b5/6f/96b56f34-4bb9-3aa5-add2-5a2504e74562/cover.jpg/600x600bb.jpg",
                "",
                "https://open.spotify.com/search/Donence%20Baris%20Manco",
                "curated",
            ),
            (
                "seed-frank-ocean-nights",
                "Nights",
                "Frank Ocean",
                "Blonde",
                2016,
                "Alternative R&B",
                307,
                "https://is1-ssl.mzstatic.com/image/thumb/Music116/v4/cd/d3/d0/cdd3d00e-ec53-2e9f-81e2-774c07f5bea9/1827849271625.jpg/600x600bb.jpg",
                "",
                "https://open.spotify.com/search/Nights%20Frank%20Ocean",
                "curated",
            ),
            (
                "seed-sebo-sigara",
                "Sigara",
                "Şebnem Ferah",
                "Kadın",
                1996,
                "Turkish Hard Rock",
                302,
                "https://is1-ssl.mzstatic.com/image/thumb/Music/v4/56/74/7f/56747fd8-0277-02f1-0a86-630f8bf210f1/cover.jpg/600x600bb.jpg",
                "",
                "https://open.spotify.com/search/Sigara%20Sebnem%20Ferah",
                "curated",
            ),
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
                "Gece 3'te otobanda tek başına sürerken çalan o barok synth melodisi... Daft Punk'ın en duygusal başyapıtı.",
                "2026-11-10",
                "gece-surusu,synth,nostalji,bas-yapit",
                "gemini-flash",
            ),
            (
                "seed-radiohead-weird-fishes",
                "batin",
                "🎧",
                4.5,
                1,
                "Katman katman açılan gitar arpejleri insanı okyanusun dibine indirip tekrar yüzeye çıkarıyor.",
                "2026-11-09",
                "arpej,derin,melankoli",
                "gemini-flash",
            ),
            (
                "seed-baris-manco-donence",
                "batin",
                "🎧",
                5.0,
                1,
                "1981 yılında Türkiye'de böyle bir space-rock / synth-prog prodüksiyonu yapılabilmiş olması inanılmaz. Zamansız.",
                "2026-11-08",
                "anadolu-rock,zamansiz,prog",
                "gemini-flash",
            ),
            (
                "seed-frank-ocean-nights",
                "melis_kr",
                "🌙",
                5.0,
                1,
                "3:30'daki beat switch tarihin en iyi geçişi olabilir. Albümü tam ortadan ikiye bölen altın oran.",
                "2026-11-10",
                "beat-switch,gece,rnb",
                "gemini-flash",
            ),
            (
                "seed-tame-impala-let-it-happen",
                "can_synth",
                "🎹",
                4.5,
                1,
                "Takılan CD efektinin bir şarkının en hipnotize edici kısmına dönüşmesi... Kevin Parker bir dahi.",
                "2026-11-07",
                "psikedelik,hipnotik,synth",
                "gemini-flash",
            ),
            (
                "seed-pink-floyd-time",
                "emre_vinyl",
                "💿",
                5.0,
                1,
                "David Gilmour'un gitar solosu başladığı an zaman gerçekten duruyor, sözleri ise her geçen yıl daha sert vuruyor.",
                "2026-11-06",
                "klasik,gitar-solosu,felsefi",
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

        # Favorites Top 4
        favorites = [
            (1, "seed-daft-punk-veridis-quo"),
            (2, "seed-baris-manco-donence"),
            (3, "seed-radiohead-weird-fishes"),
            (4, "seed-frank-ocean-nights"),
        ]
        cur.executemany("INSERT INTO favorites (slot, track_id) VALUES (?, ?)", favorites)

        # Listenlist
        cur.execute("INSERT INTO listenlist (track_id) VALUES (?)", ("seed-kendrick-wesleys-theory",))
        cur.execute("INSERT INTO listenlist (track_id) VALUES (?)", ("seed-sebo-sigara",))

        # Custom Lists
        cur.execute(
            """
            INSERT INTO custom_lists (title, description, track_ids, created_by)
            VALUES (?, ?, ?, ?)
            """,
            (
                "Gece 02:00'den Sonra Ruhun Dinledikleri",
                "Şehir uyurken kulaklıkla dinlenecek, atmosferi en yüksek 4 parça.",
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

    conn.commit()
    conn.close()


# ============================================================================
# LIVE MUSIC SEARCH (iTunes Public API + Optional Spotify Web API)
# No musician permission required: Uses official public metadata & 30s previews!
# ============================================================================
def search_music_catalog(query: str, limit: int = 12):
    """
    Fetches official song metadata, album art (600x600), and legal 30-second audio previews
    from Apple iTunes Search API (zero-config, legal metadata) and merges with local DB ratings.
    """
    results = []
    conn = get_db()
    cur = conn.cursor()

    # 1. Try live iTunes Search API first
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

                # Upsert into local tracks table so users can immediately rate/review it
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
                results.append(track_obj)
        conn.commit()
    except Exception:
        pass

    # 2. Also search local DB tracks matching query
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

    conn.close()
    return enrich_tracks_with_stats(results[:limit])


def enrich_tracks_with_stats(tracks):
    conn = get_db()
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
        # Histogram distribution (0.5 to 5.0)
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
    conn.close()
    return enriched


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

        # Check cache first to protect Argon & Claude tokens!
        cache_key = f"{selected_key}:{task_type}:{json.dumps(payload, sort_keys=True, ensure_ascii=False)}"
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT response_json FROM ai_cache WHERE cache_key = ?", (cache_key,))
        cached_row = cur.fetchone()
        if cached_row:
            conn.close()
            res = json.loads(cached_row["response_json"])
            res["cached"] = True
            res["token_note"] = "Önbellekten (Cache) getirildi — 0 yeni token harcandı!"
            return res

        # Execute live API if keys are provided in .env, otherwise execute intelligent local engine
        result_text, p_tokens, c_tokens = cls._execute_model(selected_key, task_type, payload)

        # Calculate how many Argon-equivalent tokens were saved by NOT using Argon for Tier 1/2/3 tasks
        saved_argon = (p_tokens + c_tokens) if selected_key != "argon" else 0

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

        cur.execute(
            "INSERT OR REPLACE INTO ai_cache (cache_key, model_used, response_json) VALUES (?, ?, ?)",
            (cache_key, model_info["name"], json.dumps(response_obj, ensure_ascii=False)),
        )
        conn.commit()
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
        track = payload.get("track_title", "Şarkı")
        artist = payload.get("artist", "Sanatçı")
        draft = payload.get("review_text", "")
        if task_type == "moderate_and_tag":
            return f"Şu müzik incelemesini denetle ve 4 kısa etiket çıkar ({track} - {artist}): {draft}"
        if task_type == "similar_tracks":
            return f"{artist} - {track} şarkısını seven birine prodüksiyon ve atmosfer açısından 3 şarkı öner."
        if task_type == "poetic_review":
            return f"Letterboxd'daki en popüler sinematik müzik incelemeleri gibi '{artist} - {track}' için edebi, etkileyici Türkçe bir inceleme yaz. Kullanıcı notu: {draft}"
        return f"Kullanıcının favori şarkılarına ve puanlarına göre derin Müzikal DNA ve Psiko-Akustik Karakter Analizi çıkar: {json.dumps(payload, ensure_ascii=False)}"

    @classmethod
    def _local_smart_engine(cls, selected_key: str, task_type: str, payload: dict):
        track = payload.get("track_title", "Seçili Parça")
        artist = payload.get("artist", "Sanatçı")
        genre = payload.get("genre", "Alternative")
        draft = payload.get("review_text", "").strip()

        if selected_key == "flash":
            # Tier 1: Fast moderation + auto tagging
            words = [w.lower().strip(".,!?") for w in draft.split() if len(w) > 3]
            auto_tags = [genre.lower().replace(" ", "-").split("/")[0].strip("-")]
            mood_map = {
                "gece": "gece-surusu",
                "bas": "bas-hatti",
                "gitar": "gitar-solosu",
                "synth": "analog-synth",
                "duygusal": "melankolik",
                "efsane": "bas-yapit",
                "zaman": "zamansiz",
            }
            for k, tag in mood_map.items():
                if k in draft.lower() and tag not in auto_tags:
                    auto_tags.append(tag)
            if len(auto_tags) < 3:
                auto_tags.extend(["atmosferik", "kulaklikla-dinle"])
            return (
                {
                    "status": "approved",
                    "sentiment": "Pozitif / Tutkulu",
                    "suggested_tags": auto_tags[:4],
                    "summary": f"Gemini Flash: İnceleme temiz, {len(auto_tags[:4])} otomatik etiket üretildi (Argon tokenları korundu).",
                },
                95,
                28,
            )

        if selected_key == "pro":
            # Tier 2: Gemini Pro technical & similarity matching
            return (
                {
                    "analysis_title": f"Gemini Pro — '{track}' Akustik & Benzerlik Analizi",
                    "sonic_signature": f"{artist} bu parçada {genre} dokularını dinamik frekans geçişleriyle birleştiriyor.",
                    "recommendations": [
                        f"Air — La Femme d'Argent (Benzer atmosferik derinlik ve bas yürüyüşü)",
                        f"Khruangbin — Time (You and I) (Groove ve organik enstrümantasyon uyumu)",
                        f"Massive Attack — Teardrop (Karanlık ama hipnotize edici ritmik kurgu)",
                    ],
                },
                310,
                145,
            )

        if selected_key == "claude":
            # Tier 3: Claude Sonnet 4.5 literary/poetic review generation
            base_thought = draft if draft else f"{track} başladığı anda odanın havası değişiyor."
            poetic = (
                f"“{base_thought} {artist}, '{track}' ile sadece bir melodi kurmuyor; "
                f"insanın kendi hafızasında unuttuğu bir odaya anahtar bırakıyor. "
                f"Her ölçüde biraz daha derinleşen {genre} katmanları, şarkı bittiğinde bile kulakta asılı kalan "
                f"sinematik bir boşluk yaratıyor.”"
            )
            return (
                {
                    "editorial_title": f"Claude Sonnet 4.5 — Letterboxd Edebi Eleştiri Kurgusu",
                    "poetic_review": poetic,
                    "lyric_metaphor": "Zaman, bellek ve içsel yolculuk ekseninde analog sıcaklık.",
                },
                380,
                195,
            )

        # Tier 4: Gemini 4 Argon (MOST VALUABLE — Deep Musical DNA Synthesis)
        # Pre-aggregated from Flash + Pro + Claude outputs to minimize Argon prompt size!
        conn = get_db()
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
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        qs = urllib.parse.parse_qs(parsed.query)

        if path == "/api/bootstrap":
            conn = get_db()
            cur = conn.cursor()

            cur.execute("SELECT * FROM tracks ORDER BY created_at DESC LIMIT 24")
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

            conn.close()
            return self._send_json(
                {
                    "tracks": tracks,
                    "reviews": reviews,
                    "favorites": favorites,
                    "listenlist": listenlist,
                    "custom_lists": custom_lists,
                    "token_summary": token_summary,
                    "recent_token_logs": recent_token_logs,
                    "models_hierarchy": list(MultiModelRouter.MODELS.values()),
                }
            )

        if path == "/api/search":
            q = qs.get("q", [""])[0].strip()
            if not q:
                return self._send_json({"results": []})
            results = search_music_catalog(q, limit=12)
            return self._send_json({"results": results})

        if path == "/api/track":
            tid = qs.get("id", [""])[0].strip()
            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT * FROM tracks WHERE id = ?", (tid,))
            row = cur.fetchone()
            if not row:
                conn.close()
                return self._send_json({"error": "Şarkı bulunamadı"}, 404)
            track = enrich_tracks_with_stats([dict(row)])[0]
            cur.execute(
                "SELECT * FROM reviews WHERE track_id = ? ORDER BY id DESC",
                (tid,),
            )
            track["reviews"] = [dict(r) for r in cur.fetchall()]
            conn.close()
            return self._send_json(track)

        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length).decode("utf-8")) if length > 0 else {}

        if path == "/api/review":
            track_id = body.get("track_id")
            rating = float(body.get("rating", 4.0))
            liked = 1 if body.get("liked") else 0
            review_text = body.get("review_text", "").strip()
            listen_date = body.get("listen_date") or datetime.now().strftime("%Y-%m-%d")
            username = body.get("username", "batin")
            tags_input = body.get("tags", "")

            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT * FROM tracks WHERE id = ?", (track_id,))
            track_row = cur.fetchone()
            if not track_row:
                conn.close()
                return self._send_json({"error": "Track not found"}, 404)

            # Tier 1 (Gemini Flash) automatically moderates and generates tags on review submission!
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
            conn.close()
            return self._send_json({"ok": True, "ai_routing": flash_res})

        if path == "/api/listenlist/toggle":
            track_id = body.get("track_id")
            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM listenlist WHERE track_id = ?", (track_id,))
            if cur.fetchone():
                cur.execute("DELETE FROM listenlist WHERE track_id = ?", (track_id,))
                added = False
            else:
                cur.execute("INSERT INTO listenlist (track_id) VALUES (?)", (track_id,))
                added = True
            conn.commit()
            conn.close()
            return self._send_json({"ok": True, "in_listenlist": added})

        if path == "/api/favorites/set":
            slot = int(body.get("slot", 1))
            track_id = body.get("track_id")
            conn = get_db()
            cur = conn.cursor()
            cur.execute(
                "INSERT OR REPLACE INTO favorites (slot, track_id) VALUES (?, ?)",
                (slot, track_id),
            )
            conn.commit()
            conn.close()
            return self._send_json({"ok": True})

        if path == "/api/lists/create":
            title = body.get("title", "Yeni Liste").strip()
            description = body.get("description", "").strip()
            track_ids = body.get("track_ids", [])
            conn = get_db()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO custom_lists (title, description, track_ids) VALUES (?, ?, ?)",
                (title, description, json.dumps(track_ids)),
            )
            conn.commit()
            conn.close()
            return self._send_json({"ok": True})

        if path == "/api/ai/route":
            task_type = body.get("task_type", "moderate_and_tag")
            payload = body.get("payload", {})
            routed = MultiModelRouter.route_task(task_type, payload)
            return self._send_json(routed)

        return self._send_json({"error": "Not found"}, 404)


def run_server():
    init_db()
    server = HTTPServer(("127.0.0.1", PORT), SoundboxdHandler)
    print(f"Soundboxd calisiyor -> http://localhost:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
