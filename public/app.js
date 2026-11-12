// ============================================================================
// SOUNDBOXD — Frontend Application & 4-Tier AI Model Router Client
// Hierarchy: 1. Gemini Flash -> 2. Gemini Pro -> 3. Claude Sonnet 4.5 -> 4. Gemini 4 Argon (LAST/ULTIMATE)
// ============================================================================

let appState = {
  tracks: [],
  albums: [],
  reviews: [],
  favorites: [],
  listenlist: [],
  custom_lists: [],
  token_summary: [],
  recent_token_logs: [],
  currentModalTrack: null,
  currentModalAlbum: null,
  currentLiked: true,
  albumLiked: true,
  backendAvailable: true,
};

// Format numeric rating (0.5 - 5.0) to Letterboxd stars "★★★★½"
function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function formatStars(rating) {
  const num = parseFloat(rating) || 0;
  const full = Math.floor(num);
  const half = num - full >= 0.5 ? "½" : "";
  return "★".repeat(full) + half;
}

function showToast(message) {
  const toast = document.getElementById("toastBanner");
  if (!toast) return;
  toast.textContent = message;
  toast.classList.remove("hidden");
  toast.style.opacity = "1";
  setTimeout(() => {
    toast.style.opacity = "0";
    setTimeout(() => toast.classList.add("hidden"), 300);
  }, 3200);
}

function setPickerRating(val) {
  const input = document.getElementById("ratingRangeInput");
  if (input) {
    input.value = val;
    updateStarDisplay(val);
  }
}

function setAlbumPickerRating(val) {
  const input = document.getElementById("albumRatingRange");
  if (input) {
    input.value = val;
    updateAlbumStarDisplay(val);
  }
}

function updateStarDisplay(val) {
  const disp = document.getElementById("starVisualDisplay");
  if (disp) {
    disp.textContent = `${formatStars(val)} (${parseFloat(val).toFixed(1)})`;
  }
}

function toggleHeartBtn() {
  appState.currentLiked = !appState.currentLiked;
  const btn = document.getElementById("likeToggleBtn");
  if (btn) {
    btn.classList.toggle("active", appState.currentLiked);
    btn.textContent = appState.currentLiked ? "♥ Liked" : "♡ Like";
  }
}

// ============================================================================
// BOOTSTRAP DATA (From Python Backend or Fallback State)
// ============================================================================
async function loadBootstrap() {
  try {
    const res = await fetch("/api/bootstrap");
    if (!res.ok) throw new Error("Backend offline");
    const data = await res.json();
    appState = { ...appState, ...data, backendAvailable: true };
  } catch (err) {
    console.warn("Local mode active instead of server connection:", err);
    appState.backendAvailable = false;
    initFallbackLocalState();
  }
  renderAll();
}

function initFallbackLocalState() {
  const saved = localStorage.getItem("soundboxd_state_v1");
  if (saved) {
    appState = { ...appState, ...JSON.parse(saved), backendAvailable: false };
    return;
  }
  appState.tracks = [
    {
      id: "seed-daft-punk-veridis-quo",
      title: "Veridis Quo",
      artist: "Daft Punk",
      album: "Discovery",
      release_year: 2001,
      genre: "Electronic / French House",
      cover_url: "https://is1-ssl.mzstatic.com/image/thumb/Music115/v4/f8/43/20/f84320f0-589c-46b3-f9b8-69d35b1c5a74/696998568228.jpg/600x600bb.jpg",
      preview_url: "",
      avg_rating: 5.0,
      review_count: 1,
      likes_count: 1,
      histogram: { "0.5": 0, "1.0": 0, "1.5": 0, "2.0": 0, "2.5": 0, "3.0": 0, "3.5": 0, "4.0": 0, "4.5": 0, "5.0": 1 },
      in_listenlist: false,
    },
    {
      id: "seed-baris-manco-donence",
      title: "Dönence",
      artist: "Barış Manço",
      album: "Sözüm Meclisten Dışarı",
      release_year: 1981,
      genre: "Anatolian Rock / Synth Prog",
      cover_url: "https://is1-ssl.mzstatic.com/image/thumb/Music124/v4/7b/43/87/7b4387d0-9a10-2e30-3109-646311f93d05/cover.jpg/600x600bb.jpg",
      preview_url: "",
      avg_rating: 5.0,
      review_count: 1,
      likes_count: 1,
      histogram: { "0.5": 0, "1.0": 0, "1.5": 0, "2.0": 0, "2.5": 0, "3.0": 0, "3.5": 0, "4.0": 0, "4.5": 0, "5.0": 1 },
      in_listenlist: false,
    },
    {
      id: "seed-radiohead-weird-fishes",
      title: "Weird Fishes / Arpeggi",
      artist: "Radiohead",
      album: "In Rainbows",
      release_year: 2007,
      genre: "Art Rock / Indie",
      cover_url: "https://is1-ssl.mzstatic.com/image/thumb/Music126/v4/dd/50/c7/dd50c790-99d7-6f58-8789-c71c68c1a2c3/634904032463.png/600x600bb.jpg",
      preview_url: "",
      avg_rating: 4.5,
      review_count: 1,
      likes_count: 1,
      histogram: { "0.5": 0, "1.0": 0, "1.5": 0, "2.0": 0, "2.5": 0, "3.0": 0, "3.5": 0, "4.0": 0, "4.5": 1, "5.0": 0 },
      in_listenlist: false,
    },
    {
      id: "seed-frank-ocean-nights",
      title: "Nights",
      artist: "Frank Ocean",
      album: "Blonde",
      release_year: 2016,
      genre: "Alternative R&B",
      cover_url: "https://is1-ssl.mzstatic.com/image/thumb/Music115/v4/c9/f0/37/c9f0377b-399b-964a-d48e-52340b75e95a/859718120263_cover.jpg/600x600bb.jpg",
      preview_url: "",
      avg_rating: 5.0,
      review_count: 1,
      likes_count: 1,
      histogram: { "0.5": 0, "1.0": 0, "1.5": 0, "2.0": 0, "2.5": 0, "3.0": 0, "3.5": 0, "4.0": 0, "4.5": 0, "5.0": 1 },
      in_listenlist: false,
    },
  ];
  appState.favorites = appState.tracks.slice(0, 4).map((t, i) => ({ ...t, slot: i + 1 }));
  appState.reviews = [
    {
      id: 1,
      track_id: "seed-daft-punk-veridis-quo",
      track_title: "Veridis Quo",
      track_artist: "Daft Punk",
      track_cover: appState.tracks[0].cover_url,
      release_year: 2001,
      username: "batin",
      rating: 5.0,
      liked: 1,
      review_text: "That baroque synth melody playing while driving alone on the highway at 3 AM... Daft Punk's most emotional masterpiece.",
      listen_date: "2026-11-10",
      tags: "night-drive,synth,masterpiece",
      ai_moderated_by: "Gemini 3.8 Flash",
    },
  ];
}

// ============================================================================
// RENDERING FUNCTIONS
// ============================================================================
function renderAll() {
  renderTopFour();
  renderTracksGrid(appState.tracks);
  renderRecentReviews();
  renderDiaryTable();
  renderListenlist();
  renderCustomLists();
}

function renderTopFour() {
  const container = document.getElementById("topFourGrid");
  if (!container) return;
  container.innerHTML = appState.favorites
    .slice(0, 4)
    .map(
      (fav, idx) => `
      <div class="fav-item" onclick="openTrackModal('${fav.id}')" title="${fav.title} — ${fav.artist}">
        <span class="fav-slot-tag">#${fav.slot || idx + 1}</span>
        <img src="${fav.cover_url}" alt="${fav.title}" onerror="this.src='https://placehold.co/400x400/1b2228/00e054?text=Music'" />
      </div>
    `
    )
    .join("");
}

let displayedTrackKeys = new Set();
let displayedAlbumKeys = new Set();
let tracksScrollPage = 0;
let albumsScrollPage = 0;
let tracksScrollLoading = false;
let albumsScrollLoading = false;
let currentTracksQuery = "";
let currentAlbumsQuery = "";

function trackCardHtml(t) {
  const avg = t.avg_rating && t.avg_rating > 0 ? `${t.avg_rating.toFixed(1)} ★` : "New";
  return `
      <div class="track-card">
        <div class="poster-wrap" onclick="openTrackModal('${escapeHtml(t.id)}')">
          <img src="${t.cover_url}" alt="${escapeHtml(t.title)}" loading="lazy" onerror="this.src='https://placehold.co/400x400/1b2228/00e054?text=Larpmaxxing'" />
          <span class="rating-pill-corner">${avg}</span>
          <div class="poster-overlay">
            <div class="overlay-actions">
              <button class="btn-overlay" onclick="event.stopPropagation(); quickPlayPreview('${escapeHtml(t.id)}')">
                ▶ Preview
              </button>
              <button class="btn-overlay" onclick="event.stopPropagation(); openTrackModal('${escapeHtml(t.id)}')">
                ★ Rate
              </button>
            </div>
          </div>
        </div>
        <div class="card-info" onclick="openTrackModal('${escapeHtml(t.id)}')">
          <div class="card-title" title="${escapeHtml(t.title)}">${escapeHtml(t.title)}</div>
          <div class="card-artist" title="${escapeHtml(t.artist)}">${escapeHtml(t.artist)}</div>
          <div class="card-meta-row">
            <span>${t.release_year || ""}</span>
            <span>💬 ${t.review_count || 0} • ♥ ${t.likes_count || 0}</span>
          </div>
        </div>
      </div>
    `;
}

function renderTracksGrid(tracks, targetId = "tracksGrid", append = false) {
  const grid = document.getElementById(targetId);
  if (!grid) return;

  if (targetId === "tracksGrid" && !append) {
    displayedTrackKeys.clear();
  }

  if (!append && (!tracks || tracks.length === 0)) {
    grid.innerHTML = `<p style="color:var(--text-secondary);">No tracks found yet. Use the search bar above to find any song.</p>`;
    return;
  }

  const toRender = [];
  for (const t of tracks || []) {
    if (targetId === "tracksGrid") {
      const sig = `${(t.title || "").toLowerCase()}|${(t.artist || "").toLowerCase()}`;
      if (displayedTrackKeys.has(t.id) || displayedTrackKeys.has(sig)) continue;
      displayedTrackKeys.add(t.id);
      displayedTrackKeys.add(sig);
    }
    toRender.push(t);
  }

  const html = toRender.map(trackCardHtml).join("");
  if (append) {
    grid.insertAdjacentHTML("beforeend", html);
  } else {
    grid.innerHTML = html;
  }
}

async function loadMoreTracks() {
  if (tracksScrollLoading || currentTracksQuery === "__TOP__") return;
  const discoverPanel = document.getElementById("tab-discover");
  if (!discoverPanel || !discoverPanel.classList.contains("active")) return;

  tracksScrollLoading = true;
  const loadingEl = document.getElementById("tracksLoadingText");
  if (loadingEl) loadingEl.style.display = "inline-block";

  try {
    const page = tracksScrollPage++;
    const res = await fetch(`/api/discover/more?type=tracks&page=${page}&q=${encodeURIComponent(currentTracksQuery)}`);
    if (res.ok) {
      const data = await res.json();
      const items = data.results || [];
      if (items.length > 0) {
        const existingIds = new Set(appState.tracks.map((t) => t.id));
        items.forEach((it) => {
          if (!existingIds.has(it.id)) appState.tracks.push(it);
        });
        renderTracksGrid(items, "tracksGrid", true);
      }
    }
  } catch (_) {
  } finally {
    tracksScrollLoading = false;
    if (loadingEl) loadingEl.style.display = "none";
  }
}

function renderRecentReviews() {
  const el = document.getElementById("recentReviewsList");
  if (!el) return;
  el.innerHTML = appState.reviews
    .slice(0, 10)
    .map((r) => {
      return `
      <div class="review-card" onclick="openTrackModal('${escapeHtml(r.track_id)}')" title="${escapeHtml(r.review_text || "")}" style="cursor:pointer;">
        <img class="review-card-cover" src="${r.track_cover}" alt="${escapeHtml(r.track_title)}" onerror="this.src='https://placehold.co/200x200/1b2228/00e054?text=♪'" />
        <div class="review-card-body">
          <div class="review-header">
            <span class="review-track-title">
              ${escapeHtml(r.track_title)}
            </span>
            <span>
              <span class="review-stars">${formatStars(r.rating)}</span>
              ${r.liked ? '<span class="review-heart">♥</span>' : ""}
            </span>
          </div>
          <p class="review-text">${r.review_text ? escapeHtml(r.review_text) : "<em>Rated</em>"}</p>
          <div class="review-footer">
            <span>${escapeHtml(r.track_artist)}</span>
            <span>@${escapeHtml(r.username)}</span>
          </div>
        </div>
      </div>
    `;
    })
    .join("");
}

function renderDiaryTable() {
  const tbody = document.getElementById("diaryTableBody");
  if (!tbody) return;
  tbody.innerHTML = appState.reviews
    .map((r) => {
      const tags = (r.tags || "")
        .split(",")
        .filter(Boolean)
        .map((tg) => `<span class="tag-chip">#${escapeHtml(tg.trim())}</span>`)
        .join("");
      return `
      <tr>
        <td style="white-space:nowrap;color:var(--text-secondary);">${escapeHtml(r.listen_date || "2026-11-11")}</td>
        <td>
          <img class="diary-cover" src="${r.track_cover}" alt="" onclick="openTrackModal('${r.track_id}')" style="cursor:pointer;" />
        </td>
        <td>
          <strong style="cursor:pointer;" onclick="openTrackModal('${r.track_id}')">${escapeHtml(r.track_title)}</strong><br/>
          <span style="color:var(--text-secondary);font-size:0.78rem;">${escapeHtml(r.track_artist)}</span>
        </td>
        <td>${r.release_year || ""}</td>
        <td><span class="review-stars">${formatStars(r.rating)}</span> <small>(${r.rating})</small></td>
        <td>${r.liked ? '<span class="review-heart">♥</span>' : "—"}</td>
        <td>
          <div style="margin-bottom:4px;">${escapeHtml(r.review_text || "")}</div>
          <div>${tags}</div>
        </td>
      </tr>
    `;
    })
    .join("");
}

function renderListenlist() {
  const badge = document.getElementById("listenlistBadge");
  if (badge) badge.textContent = appState.listenlist.length;
  renderTracksGrid(appState.listenlist, "listenlistGrid");
}

function renderCustomLists() {
  const container = document.getElementById("customListsContainer");
  if (!container) return;

  if (!appState.custom_lists || appState.custom_lists.length === 0) {
    container.innerHTML = `
      <div class="lists-empty-state">
        <div style="font-size:2.2rem;margin-bottom:8px;">📁</div>
        <h3 style="color:#fff;font-size:1.15rem;margin-bottom:6px;">No Curated Lists Yet</h3>
        <p style="color:var(--text-muted);font-size:0.85rem;margin-bottom:16px;">Create your first Letterboxd-style track list to share your favorite songs and albums.</p>
        <button type="button" class="btn-primary" onclick="openCreateListModal()" style="padding:9px 20px;font-size:0.88rem;cursor:pointer;">+ Create New List</button>
      </div>
    `;
    return;
  }

  container.innerHTML = appState.custom_lists
    .map((lst) => {
      const strip = (lst.tracks || [])
        .slice(0, 6)
        .map((t) => `<img src="${t.cover_url}" alt="${escapeHtml(t.title)}" title="${escapeHtml(t.title)} - ${escapeHtml(t.artist)}" onclick="openTrackModal('${t.id}')" style="cursor:pointer;" />`)
        .join("");
      const safeTitle = escapeHtml(lst.title || "Untitled List");
      return `
      <div class="list-card" id="listCard_${lst.id}">
        <div class="list-card-header">
          <h3 class="list-card-title">${safeTitle}</h3>
          <button type="button" class="btn-delete-list" title="Delete list" onclick="confirmDeleteList(${lst.id}, '${safeTitle.replace(/'/g, "\\'")}')">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>
            <span>Delete</span>
          </button>
        </div>
        <p class="list-card-desc">${escapeHtml(lst.description || "")}</p>
        <div class="list-posters-strip">${strip || '<span style="font-size:0.75rem;color:var(--text-muted);">Empty list</span>'}</div>
        <div class="list-card-footer">
          Curated by <strong>@${escapeHtml(lst.created_by || "batin")}</strong> • ${(lst.tracks || []).length} track${(lst.tracks || []).length === 1 ? '' : 's'}
        </div>
      </div>
    `;
    })
    .join("");
}

async function confirmDeleteList(listId, listTitle) {
  if (!confirm(`Are you sure you want to delete the list "${listTitle}"?`)) {
    return;
  }
  try {
    const res = await fetch("/api/lists/delete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id: listId }),
    });
    const data = await res.json().catch(() => ({}));
    if (res.ok && data.ok) {
      showToast(`✓ List "${listTitle}" deleted.`);
      await loadBootstrap();
    } else {
      showToast(data.error || "Failed to delete list.");
    }
  } catch (err) {
    showToast("Network error deleting list.");
  }
}

// ============================================================================
// SEARCH & FILTERS (Live iTunes Public Catalog + Local Ratings)
// ============================================================================
async function performLiveSearch(query) {
  cancelSuggestionsAndHide();
  if (!query || !query.trim()) {
    currentTracksQuery = "";
    tracksScrollPage = 0;
    document.getElementById("tracksGridTitle").textContent = "POPULAR TRACKS";
    renderTracksGrid(appState.tracks);
    return;
  }

  currentTracksQuery = query.trim();
  tracksScrollPage = 0;
  switchTab("discover");
  const titleEl = document.getElementById("tracksGridTitle");
  titleEl.textContent = `SEARCHING CATALOG FOR "${query}"...`;

  try {
    if (appState.backendAvailable) {
      const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
      const data = await res.json();
      if (data.results && data.results.length > 0) {
        // Merge into appState.tracks so modals can open them
        const existingIds = new Set(appState.tracks.map((t) => t.id));
        data.results.forEach((r) => {
          if (!existingIds.has(r.id)) appState.tracks.unshift(r);
        });
        titleEl.textContent = `SEARCH RESULTS FOR "${query.toUpperCase()}" (${data.results.length} TRACKS)`;
        renderTracksGrid(data.results);
        return;
      }
    }

    // Fallback direct browser fetch to iTunes API if server is offline
    const res = await fetch(`https://itunes.apple.com/search?term=${encodeURIComponent(query)}&entity=song&limit=12`);
    const data = await res.json();
    const mapped = (data.results || []).map((item) => ({
      id: `itunes-${item.trackId}`,
      title: item.trackName,
      artist: item.artistName,
      album: item.collectionName || "Single",
      release_year: item.releaseDate ? parseInt(item.releaseDate.slice(0, 4), 10) : 2022,
      genre: item.primaryGenreName || "Music",
      cover_url: (item.artworkUrl100 || "").replace("100x100bb", "600x600bb"),
      preview_url: item.previewUrl || "",
      avg_rating: 0,
      review_count: 0,
      likes_count: 0,
      histogram: { "0.5": 0, "1.0": 0, "1.5": 0, "2.0": 0, "2.5": 0, "3.0": 0, "3.5": 0, "4.0": 0, "4.5": 0, "5.0": 0 },
    }));
    mapped.forEach((m) => {
      if (!appState.tracks.find((x) => x.id === m.id)) appState.tracks.unshift(m);
    });
    titleEl.textContent = `SEARCH RESULTS FOR "${query.toUpperCase()}" (${mapped.length} TRACKS)`;
    renderTracksGrid(mapped);
  } catch (e) {
    titleEl.textContent = `RESULTS FOR "${query}"`;
    const filtered = appState.tracks.filter(
      (t) =>
        t.title.toLowerCase().includes(query.toLowerCase()) ||
        t.artist.toLowerCase().includes(query.toLowerCase())
    );
    renderTracksGrid(filtered);
  }
}

function filterTracks(mode, btnEl) {
  document.querySelectorAll(".filter-bar .chip").forEach((b) => b.classList.remove("active"));
  if (btnEl) btnEl.classList.add("active");

  if (mode === "top") {
    currentTracksQuery = "__TOP__";
    document.getElementById("tracksGridTitle").textContent = "HIGHEST RATED TRACKS (4.5★+)";
    renderTracksGrid(appState.tracks.filter((t) => (t.avg_rating || 0) >= 4.5));
  } else {
    currentTracksQuery = "";
    tracksScrollPage = 0;
    document.getElementById("tracksGridTitle").textContent = "POPULAR TRACKS";
    renderTracksGrid(appState.tracks);
  }
}

function runLivePresetSearch(presetQuery, btnEl) {
  document.querySelectorAll(".filter-bar .chip").forEach((b) => b.classList.remove("active"));
  if (btnEl) btnEl.classList.add("active");
  document.getElementById("globalSearchInput").value = presetQuery;
  performLiveSearch(presetQuery);
}

// ============================================================================
// AUDIO PREVIEW PLAYER (Custom Dark Player Bar with Play/Pause/Stop/Seek/Volume)
// ============================================================================
let currentPlayingTrackId = null;
let currentPlayingUrl = "";
let audioPlayerInitialized = false;

function formatPlayerTime(seconds) {
  const s = Math.max(0, Math.floor(seconds || 0));
  const min = Math.floor(s / 60);
  const sec = String(s % 60).padStart(2, "0");
  return `${min}:${sec}`;
}

function syncPlayerButtonsUI() {
  const audio = document.getElementById("audioElement");
  const isPlaying = audio && !audio.paused && !audio.ended && Boolean(audio.src);

  const playPauseBtn = document.getElementById("playerPlayPauseBtn");
  if (playPauseBtn) {
    playPauseBtn.textContent = isPlaying ? "⏸" : "▶";
  }

  const modalPlayBtn = document.getElementById("modalPlayBtn");
  if (modalPlayBtn && appState.currentModalTrack) {
    const isThisModalTrack =
      currentPlayingTrackId === appState.currentModalTrack.id ||
      (appState.currentModalTrack.preview_url && currentPlayingUrl === appState.currentModalTrack.preview_url);
    if (isThisModalTrack && isPlaying) {
      modalPlayBtn.textContent = "⏸ Pause Preview";
    } else if (isThisModalTrack && audio && audio.paused && audio.currentTime > 0) {
      modalPlayBtn.textContent = "▶ Resume Preview";
    } else {
      modalPlayBtn.textContent = "▶ Play Preview";
    }
  }
}

function initAudioElementListeners() {
  if (audioPlayerInitialized) return;
  const audio = document.getElementById("audioElement");
  if (!audio) return;
  audioPlayerInitialized = true;
  audio.volume = 0.85;

  audio.addEventListener("play", syncPlayerButtonsUI);
  audio.addEventListener("pause", syncPlayerButtonsUI);
  audio.addEventListener("ended", () => {
    syncPlayerButtonsUI();
    const seek = document.getElementById("playerSeekSlider");
    if (seek) seek.value = 0;
    const cur = document.getElementById("playerCurrentTime");
    if (cur) cur.textContent = "0:00";
  });
  audio.addEventListener("loadedmetadata", () => {
    const dur = audio.duration && isFinite(audio.duration) ? audio.duration : 30;
    const seek = document.getElementById("playerSeekSlider");
    if (seek) seek.max = dur;
    const durEl = document.getElementById("playerDuration");
    if (durEl) durEl.textContent = formatPlayerTime(dur);
  });
  audio.addEventListener("timeupdate", () => {
    const seek = document.getElementById("playerSeekSlider");
    if (seek) seek.value = audio.currentTime || 0;
    const cur = document.getElementById("playerCurrentTime");
    if (cur) cur.textContent = formatPlayerTime(audio.currentTime || 0);
  });
}

function toggleAudioPlayPause() {
  initAudioElementListeners();
  const audio = document.getElementById("audioElement");
  if (!audio || !audio.src) return;
  if (audio.paused) {
    audio.play().catch(() => {});
  } else {
    audio.pause();
  }
  syncPlayerButtonsUI();
}

function seekAudioPreview(val) {
  const audio = document.getElementById("audioElement");
  if (!audio || !audio.src) return;
  audio.currentTime = parseFloat(val) || 0;
}

function setAudioVolume(val) {
  const audio = document.getElementById("audioElement");
  if (!audio) return;
  const v = parseFloat(val);
  audio.volume = v;
  audio.muted = v === 0;
  const muteBtn = document.getElementById("playerMuteBtn");
  if (muteBtn) muteBtn.textContent = audio.muted ? "🔇" : "🔊";
}

function toggleAudioMute() {
  const audio = document.getElementById("audioElement");
  if (!audio) return;
  audio.muted = !audio.muted;
  const muteBtn = document.getElementById("playerMuteBtn");
  if (muteBtn) muteBtn.textContent = audio.muted ? "🔇" : "🔊";
}

function openCurrentlyPlayingModal() {
  if (currentPlayingTrackId) {
    openTrackModal(currentPlayingTrackId);
  }
}

async function quickPlayPreview(trackId) {
  initAudioElementListeners();
  let track = appState.tracks.find((t) => t.id === trackId);
  if (!track && appState.currentModalTrack && appState.currentModalTrack.id === trackId) {
    track = appState.currentModalTrack;
  }
  if (!track) return;

  const audio = document.getElementById("audioElement");
  const bar = document.getElementById("audioPlayerBar");

  // If this exact track is already loaded in the player, toggle Play / Pause!
  if (currentPlayingTrackId === track.id && audio.src && !bar.classList.contains("hidden")) {
    toggleAudioPlayPause();
    return;
  }

  // If curated seed track doesn't have preview_url cached yet, fetch it on the fly from iTunes
  if (!track.preview_url) {
    try {
      const q = encodeURIComponent(`${track.title} ${track.artist}`);
      const r = await fetch(`https://itunes.apple.com/search?term=${q}&entity=song&limit=1`);
      const d = await r.json();
      if (d.results && d.results[0] && d.results[0].previewUrl) {
        track.preview_url = d.results[0].previewUrl;
      }
    } catch (_) {}
  }

  if (!track.preview_url) {
    showToast("No 30s audio preview available for this track.");
    return;
  }

  currentPlayingTrackId = track.id;
  currentPlayingUrl = track.preview_url;
  document.getElementById("playerCover").src = track.cover_url;
  document.getElementById("playerTitle").textContent = track.title;
  document.getElementById("playerArtist").textContent = `${track.artist}${track.album ? " • " + track.album : ""}`;
  bar.classList.remove("hidden");
  audio.src = track.preview_url;
  audio.play().catch(() => {});
  syncPlayerButtonsUI();
}

function stopAudioPreview() {
  const audio = document.getElementById("audioElement");
  if (audio) {
    audio.pause();
    audio.currentTime = 0;
  }
  currentPlayingTrackId = null;
  currentPlayingUrl = "";
  const bar = document.getElementById("audioPlayerBar");
  if (bar) bar.classList.add("hidden");
  syncPlayerButtonsUI();
}

// ============================================================================
// TRACK MODAL, HISTOGRAM & REVIEW SUBMISSION
// ============================================================================
async function openTrackModal(trackId) {
  let track = appState.tracks.find((t) => t.id === trackId);
  if (appState.backendAvailable) {
    try {
      const res = await fetch(`/api/track?id=${encodeURIComponent(trackId)}`);
      if (res.ok) {
        track = await res.json();
      }
    } catch (_) {}
  }
  if (!track) return;
  appState.currentModalTrack = track;

  document.getElementById("modalCover").src = track.cover_url;
  document.getElementById("modalGenreBadge").textContent = track.genre || "Music";
  document.getElementById("modalTitle").textContent = track.title;
  document.getElementById("modalArtist").textContent = track.artist;
  document.getElementById("modalAlbum").textContent = track.album || "Single";
  document.getElementById("modalYear").textContent = track.release_year || "";
  document.getElementById("listenDateInput").value = new Date().toISOString().slice(0, 10);
  document.getElementById("reviewTextInput").value = "";
  document.getElementById("reviewTagsInput").value = "";
  document.getElementById("modalAiHelperOutput").classList.add("hidden");

  const listenBtn = document.getElementById("modalListenlistBtn");
  listenBtn.textContent = track.in_listenlist ? "✓ In Playlist (Remove)" : "+ Add to Playlist";

  renderModalHistogram(track);
  renderModalReviews(track);
  syncPlayerButtonsUI();

  document.getElementById("trackModal").classList.remove("hidden");
}

function closeTrackModal() {
  document.getElementById("trackModal").classList.add("hidden");
}

function openQuickLogModal() {
  if (appState.tracks.length > 0) {
    openTrackModal(appState.tracks[0].id);
  }
}

function playCurrentModalPreview() {
  if (appState.currentModalTrack) {
    quickPlayPreview(appState.currentModalTrack.id);
  }
}

function renderModalHistogram(track) {
  const avgEl = document.getElementById("modalAvgRating");
  avgEl.textContent = track.avg_rating ? `${track.avg_rating.toFixed(2)} ★ (${track.review_count} votes)` : "No ratings yet";

  const barsEl = document.getElementById("modalHistogramBars");
  const hist = track.histogram || {};
  const steps = ["0.5", "1.0", "1.5", "2.0", "2.5", "3.0", "3.5", "4.0", "4.5", "5.0"];
  const maxVal = Math.max(1, ...steps.map((s) => hist[s] || 0));

  barsEl.innerHTML = steps
    .map((s) => {
      const cnt = hist[s] || 0;
      const pct = Math.max(6, Math.round((cnt / maxVal) * 100));
      return `
      <div class="hist-bar-col" title="${s}★: ${cnt} votes">
        <div class="hist-bar" style="height:${pct}%;opacity:${cnt > 0 ? 1 : 0.25}"></div>
        <span class="hist-label">${s}</span>
      </div>
    `;
    })
    .join("");
}

function renderModalReviews(track) {
  const listEl = document.getElementById("modalReviewsList");
  const revs = track.reviews || appState.reviews.filter((r) => r.track_id === track.id);
  if (!revs || revs.length === 0) {
    listEl.innerHTML = `<p style="color:var(--text-muted);font-size:0.84rem;">Be the first to write a review for this track!</p>`;
    return;
  }
  listEl.innerHTML = revs
    .map(
      (r) => `
    <div style="background:var(--bg-elevated);border:1px solid var(--border-subtle);border-radius:6px;padding:10px;">
      <div style="display:flex;justify-content:space-between;font-size:0.82rem;margin-bottom:4px;">
        <strong>👤 @${escapeHtml(r.username)}</strong>
        <span class="review-stars">${formatStars(r.rating)} ${r.liked ? '<span class="review-heart">♥</span>' : ""}</span>
      </div>
      <p style="font-size:0.85rem;color:#e2e8f0;">${r.review_text ? escapeHtml(r.review_text) : ""}</p>
      <div style="font-size:0.7rem;color:var(--text-muted);margin-top:4px;">
        📅 ${escapeHtml(r.listen_date || "Today")}
      </div>
    </div>
  `
    )
    .join("");
}

async function submitReviewForm(e) {
  e.preventDefault();
  if (!appState.currentModalTrack) return;

  const t = appState.currentModalTrack;
  const ratingVal = parseFloat(document.getElementById("ratingRangeInput").value);
  const payload = {
    track_id: t.id,
    title: t.title || "Track",
    artist: t.artist || "Artist",
    album: t.album || "Single",
    cover_url: t.cover_url || "",
    preview_url: t.preview_url || "",
    genre: t.genre || "Music",
    release_year: t.release_year || 2024,
    rating: ratingVal,
    liked: appState.currentLiked,
    review_text: document.getElementById("reviewTextInput").value.trim(),
    listen_date: document.getElementById("listenDateInput").value,
    tags: document.getElementById("reviewTagsInput").value.trim(),
    username: "batin",
  };

  try {
    if (appState.backendAvailable) {
      const res = await fetch("/api/review", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        showToast(`✓ Logged ${ratingVal}★ rating for "${t.title}"!`);
        await loadBootstrap();
        await openTrackModal(t.id);
        return;
      }
    }
  } catch (err) {
    console.warn("Backend error, falling back locally:", err);
  }

  // Fallback local save
  appState.reviews.unshift({
    id: Date.now(),
    ...payload,
    track_title: t.title,
    track_artist: t.artist,
    track_cover: t.cover_url,
    release_year: t.release_year,
    tags: payload.tags || "atmospheric,favorite",
    ai_moderated_by: "Gemini 3.8 Flash",
  });
  showToast(`✓ Logged ${ratingVal}★ rating for "${t.title}"!`);
  renderAll();
  closeTrackModal();
}

async function toggleCurrentModalListenlist() {
  if (!appState.currentModalTrack) return;
  if (appState.backendAvailable) {
    const res = await fetch("/api/listenlist/toggle", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ track_id: appState.currentModalTrack.id }),
    });
    const data = await res.json().catch(() => ({}));
    showToast(data.in_listenlist ? `✓ Added "${appState.currentModalTrack.title}" to Playlist!` : `Removed "${appState.currentModalTrack.title}" from Playlist`);
    await loadBootstrap();
    await openTrackModal(appState.currentModalTrack.id);
  }
}

async function setFavoriteSlot(slot) {
  if (!appState.currentModalTrack) return;
  if (appState.backendAvailable) {
    await fetch("/api/favorites/set", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ slot, track_id: appState.currentModalTrack.id }),
    });
    await loadBootstrap();
    showToast(`✓ Favorite slot #${slot} updated to "${appState.currentModalTrack.title}"!`);
  }
}

// ============================================================================
// AI ASSISTANTS IN MODAL & 4-TIER ROUTER TAB (FLASH -> PRO -> CLAUDE -> ARGON)
// ============================================================================
async function callModelRouter(taskType, payload) {
  if (appState.backendAvailable) {
    const res = await fetch("/api/ai/route", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ task_type: taskType, payload }),
    });
    const data = await res.json();
    await loadBootstrap();
    return data;
  }
  return {
    model_name: taskType === "poetic_review" ? "Claude Sonnet 4.5" : taskType === "musical_dna_argon" ? "Gemini 4 Argon" : "Gemini 3.8 Flash",
    model_tier: "Smart Router",
    usage: { total_tokens: 240, saved_argon_tokens: 240 },
    result: { poetic_review: "“A rare recording that slows down the passage of time.”" },
  };
}

async function assistReviewWithClaude() {
  if (!appState.currentModalTrack) return;
  const helperEl = document.getElementById("modalAiHelperOutput");
  helperEl.classList.remove("hidden");
  helperEl.innerHTML = `✒️ Crafting poetic review draft...`;

  const draft = document.getElementById("reviewTextInput").value;
  const data = await callModelRouter("poetic_review", {
    track_title: appState.currentModalTrack.title,
    artist: appState.currentModalTrack.artist,
    genre: appState.currentModalTrack.genre,
    review_text: draft,
  });

  const poetic = data.result.poetic_review || JSON.stringify(data.result);
  document.getElementById("reviewTextInput").value = poetic.replace(/^“|”$/g, "");
  helperEl.innerHTML = `
    <div><strong>✒️ Poetic Review Draft Ready!</strong></div>
    <div style="margin-top:4px;color:#cbd5e1;">Inserted into the review box—edit freely before saving.</div>
  `;
}

async function assistSimilarWithPro() {
  if (!appState.currentModalTrack) return;
  const helperEl = document.getElementById("modalAiHelperOutput");
  helperEl.classList.remove("hidden");
  helperEl.innerHTML = `🎧 Searching live catalog for similar tracks...`;

  const data = await callModelRouter("similar_tracks", {
    track_title: appState.currentModalTrack.title,
    artist: appState.currentModalTrack.artist,
    genre: appState.currentModalTrack.genre,
  });

  const recTracks = (data.result && data.result.recommended_tracks) || [];
  if (recTracks.length > 0) {
    recTracks.forEach((rt) => {
      if (!appState.tracks.find((x) => x.id === rt.id)) {
        appState.tracks.unshift({
          avg_rating: 0,
          review_count: 0,
          likes_count: 0,
          histogram: {},
          ...rt,
        });
      }
    });

    const cardsHtml = recTracks
      .map(
        (rt) => `
      <div style="display:flex;align-items:center;justify-content:space-between;gap:10px;padding:7px 8px;margin-top:6px;background:rgba(15,20,26,0.65);border:1px solid var(--border-subtle);border-radius:6px;">
        <div style="display:flex;align-items:center;gap:9px;min-width:0;cursor:pointer;" onclick="openTrackModal('${escapeHtml(rt.id)}')">
          <img src="${escapeHtml(rt.cover_url || "")}" alt="" style="width:36px;height:36px;border-radius:4px;object-fit:cover;flex-shrink:0;" onerror="this.src='https://placehold.co/80x80/1b2228/00e054?text=♪'" />
          <div style="min-width:0;">
            <div style="font-size:0.82rem;font-weight:700;color:#fff;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${escapeHtml(rt.title)} — <span style="color:var(--lb-green);">${escapeHtml(rt.artist)}</span></div>
            <div style="font-size:0.71rem;color:var(--text-secondary);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${escapeHtml(rt.reason || rt.genre || "")}</div>
          </div>
        </div>
        <div style="display:flex;gap:5px;flex-shrink:0;">
          ${rt.preview_url ? `<button type="button" class="btn-mini-play" onclick="quickPlayPreview('${escapeHtml(rt.id)}')">▶ Play</button>` : ""}
          <button type="button" class="btn-mini-play" onclick="openTrackModal('${escapeHtml(rt.id)}')">★ Rate</button>
        </div>
      </div>`
      )
      .join("");

    helperEl.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <strong>🎧 Similar Tracks from Live Catalog:</strong>
        <button type="button" class="btn-mini-play" onclick="assistSimilarWithPro()" title="Fetch another set of recommendations">🔄 Refresh</button>
      </div>
      <div>${cardsHtml}</div>
    `;
    return;
  }

  const recs = (data.result.recommendations || []).map((r) => `<li>${escapeHtml(r)}</li>`).join("");
  helperEl.innerHTML = `
    <div><strong>🎧 Recommended Similar Tracks:</strong></div>
    <ul style="margin:6px 0 0 18px;">${recs}</ul>
  `;
}

// ============================================================================
// CUSTOM LISTS MODAL (Modern Interactive Track Picker & Selected Shelf)
// ============================================================================
let listModalSelectedTracks = new Map();
let listModalPool = new Map();
let listModalCurrentCandidates = [];
let listSearchTimer = null;

function updateListSelectedTray() {
  const count = listModalSelectedTracks.size;
  const countBadge = document.getElementById("listSelectedCountBadge");
  if (countBadge) {
    countBadge.textContent = `${count} track${count === 1 ? "" : "s"}`;
  }
  const submitBtn = document.getElementById("newListSubmitBtn");
  if (submitBtn) {
    submitBtn.textContent = `Create List (${count} Track${count === 1 ? "" : "s"})`;
  }

  const tray = document.getElementById("listSelectedChipsContainer");
  if (!tray) return;

  if (count === 0) {
    tray.innerHTML = `<span class="list-empty-tray-msg">No tracks added yet. Search and pick songs below.</span>`;
    return;
  }

  tray.innerHTML = Array.from(listModalSelectedTracks.values())
    .map((t) => {
      const cover = t.cover_url || "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=300";
      const safeTitle = escapeHtml(t.title || "Untitled");
      const safeArtist = escapeHtml(t.artist || "Unknown");
      const tid = escapeHtml(t.id);
      return `
        <div class="list-selected-chip" title="${safeTitle} — ${safeArtist}">
          <img class="chip-cover" src="${cover}" alt="${safeTitle}" onerror="this.src='https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=300'" />
          <div class="chip-text">
            <span class="chip-title">${safeTitle}</span>
            <span class="chip-artist">${safeArtist}</span>
          </div>
          <button type="button" class="chip-remove-btn" title="Remove track" onclick="event.stopPropagation(); removeTrackFromListModal('${tid}')">✕</button>
        </div>
      `;
    })
    .join("");
}

function renderListModalCheckboxes(candidateTracks) {
  const box = document.getElementById("newListTrackCheckboxes");
  if (!box) return;

  listModalCurrentCandidates = candidateTracks || [];
  if (listModalCurrentCandidates.length === 0) {
    box.innerHTML = `<div class="list-picker-empty">No matching tracks found. Try searching for another artist or song.</div>`;
    return;
  }

  box.innerHTML = listModalCurrentCandidates
    .map((t) => {
      const isSelected = listModalSelectedTracks.has(t.id);
      const cover = t.cover_url || "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=300";
      const safeTitle = escapeHtml(t.title || "Untitled Track");
      const safeArtist = escapeHtml(t.artist || "Unknown Artist");
      const safeAlbum = escapeHtml(t.album || "");
      const previewUrl = t.preview_url || "";
      const tid = escapeHtml(t.id);

      return `
        <div class="list-picker-card ${isSelected ? "is-selected" : ""}" id="listPickerCard_${tid}" onclick="toggleListModalTrack('${tid}')">
          <div class="list-picker-cover-wrap">
            <img class="list-picker-cover" src="${cover}" alt="${safeTitle}" onerror="this.src='https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=300'" />
            ${
              previewUrl
                ? `<button type="button" class="list-picker-play-btn" title="Play 30s preview" onclick="event.stopPropagation(); quickPlayPreviewDirect('${escapeHtml(previewUrl)}', '${safeTitle}', '${safeArtist}', '${escapeHtml(cover)}')">▶</button>`
                : ""
            }
          </div>
          <div class="list-picker-info">
            <div class="list-picker-title" title="${safeTitle}">${safeTitle}</div>
            <div class="list-picker-artist" title="${safeArtist}">
              ${safeArtist} ${safeAlbum ? `• <span class="list-picker-album">${safeAlbum}</span>` : ""}
            </div>
          </div>
          <button type="button" class="list-picker-btn ${isSelected ? "is-added" : ""}" id="listPickerBtn_${tid}" onclick="event.stopPropagation(); toggleListModalTrack('${tid}')">
            ${isSelected ? "✓ Added" : "+ Add"}
          </button>
        </div>
      `;
    })
    .join("");
}

function toggleListModalTrack(trackId) {
  if (listModalSelectedTracks.has(trackId)) {
    listModalSelectedTracks.delete(trackId);
  } else {
    const tr = listModalPool.get(trackId) || appState.tracks.find((x) => x.id === trackId);
    if (tr) listModalSelectedTracks.set(trackId, tr);
  }

  // Update card UI state without destroying scroll position
  const card = document.getElementById(`listPickerCard_${trackId}`);
  const btn = document.getElementById(`listPickerBtn_${trackId}`);
  const isSelected = listModalSelectedTracks.has(trackId);
  if (card) card.classList.toggle("is-selected", isSelected);
  if (btn) {
    btn.classList.toggle("is-added", isSelected);
    btn.textContent = isSelected ? "✓ Added" : "+ Add";
  }

  updateListSelectedTray();
}

function removeTrackFromListModal(trackId) {
  listModalSelectedTracks.delete(trackId);
  const card = document.getElementById(`listPickerCard_${trackId}`);
  const btn = document.getElementById(`listPickerBtn_${trackId}`);
  if (card) card.classList.remove("is-selected");
  if (btn) {
    btn.classList.remove("is-added");
    btn.textContent = "+ Add";
  }
  updateListSelectedTray();
}

function searchTracksForListModal(query) {
  clearTimeout(listSearchTimer);
  const q = (query || "").trim();
  const clearBtn = document.getElementById("listSearchClearBtn");
  if (clearBtn) clearBtn.classList.toggle("hidden", !q);

  const statusEl = document.getElementById("listCatalogStatus");

  if (!q) {
    if (statusEl) statusEl.textContent = "Library Tracks";
    renderListModalCheckboxes(appState.tracks);
    return;
  }

  if (statusEl) statusEl.textContent = "Searching catalog...";

  const local = appState.tracks.filter(
    (t) =>
      (t.title || "").toLowerCase().includes(q.toLowerCase()) ||
      (t.artist || "").toLowerCase().includes(q.toLowerCase()) ||
      (t.album || "").toLowerCase().includes(q.toLowerCase())
  );
  renderListModalCheckboxes(local);

  listSearchTimer = setTimeout(async () => {
    try {
      const res = await fetch(`/api/suggest?q=${encodeURIComponent(q)}`);
      const data = await res.json();
      const songs = data.songs || [];
      songs.forEach((s) => listModalPool.set(s.id, s));

      const combined = [...local];
      const seen = new Set(local.map((x) => x.id));
      for (const s of songs) {
        if (!seen.has(s.id)) {
          combined.push(s);
          seen.add(s.id);
        }
      }

      if (statusEl) {
        statusEl.textContent = `${combined.length} results found`;
      }
      renderListModalCheckboxes(combined);
    } catch (_) {
      if (statusEl) statusEl.textContent = "Live search unavailable";
    }
  }, 130);
}

function clearListModalSearch() {
  const searchEl = document.getElementById("listTrackSearchInput");
  if (searchEl) searchEl.value = "";
  const clearBtn = document.getElementById("listSearchClearBtn");
  if (clearBtn) clearBtn.classList.add("hidden");
  const statusEl = document.getElementById("listCatalogStatus");
  if (statusEl) statusEl.textContent = "Library Tracks";
  renderListModalCheckboxes(appState.tracks);
}

function openCreateListModal() {
  listModalSelectedTracks.clear();
  listModalPool.clear();
  appState.tracks.forEach((t) => listModalPool.set(t.id, t));

  const titleEl = document.getElementById("newListTitle");
  if (titleEl) titleEl.value = "";
  const descEl = document.getElementById("newListDesc");
  if (descEl) descEl.value = "";

  const searchEl = document.getElementById("listTrackSearchInput");
  if (searchEl) searchEl.value = "";
  const clearBtn = document.getElementById("listSearchClearBtn");
  if (clearBtn) clearBtn.classList.add("hidden");
  const statusEl = document.getElementById("listCatalogStatus");
  if (statusEl) statusEl.textContent = "Library Tracks";

  updateListSelectedTray();
  renderListModalCheckboxes(appState.tracks);
  document.getElementById("listModal").classList.remove("hidden");
}

function closeCreateListModal() {
  document.getElementById("listModal").classList.add("hidden");
}

async function submitNewList(e) {
  e.preventDefault();
  const title = document.getElementById("newListTitle").value.trim();
  const description = document.getElementById("newListDesc").value.trim();

  if (listModalSelectedTracks.size === 0) {
    showToast("Please select at least 1 track to create your list!");
    return;
  }

  const checked = Array.from(listModalSelectedTracks.keys());
  const tracksMeta = Array.from(listModalSelectedTracks.values());

  if (appState.backendAvailable) {
    try {
      const res = await fetch("/api/lists/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, description, track_ids: checked, tracks_meta: tracksMeta }),
      });
      if (res.ok) {
        showToast(`✓ Created list "${title}" with ${checked.length} tracks!`);
        await loadBootstrap();
      } else {
        showToast("Error creating list, please try again.");
      }
    } catch (err) {
      showToast("Network error creating list.");
    }
  }
  closeCreateListModal();
}

// ============================================================================
// ALBUM MODE (ALBUM RATING & TRACKLIST)
// ============================================================================
async function loadAlbums(btnEl) {
  if (btnEl) {
    document.querySelectorAll("#tab-albums .filter-bar .chip").forEach((b) => b.classList.remove("active"));
    btnEl.classList.add("active");
    currentAlbumsQuery = "";
    albumsScrollPage = 0;
  }
  if (appState.backendAvailable) {
    try {
      const res = await fetch("/api/albums");
      const data = await res.json();
      appState.albums = data.albums || [];
    } catch (_) {}
  }
  renderAlbumsGrid(appState.albums, false);
}

function albumCardHtml(a) {
  const avg = a.avg_rating && a.avg_rating > 0 ? `${a.avg_rating.toFixed(1)} ★` : "New";
  return `
      <div class="track-card">
        <div class="poster-wrap" onclick="openAlbumModal('${escapeHtml(a.id)}')">
          <img src="${a.cover_url}" alt="${escapeHtml(a.title)}" loading="lazy" onerror="this.src='https://placehold.co/400x400/1b2228/00e054?text=Album'" />
          <span class="rating-pill-corner">${avg}</span>
          <div class="poster-overlay">
            <div class="overlay-actions">
              <button class="btn-overlay" onclick="event.stopPropagation(); openAlbumModal('${escapeHtml(a.id)}')">
                💿 View & Rate Album
              </button>
            </div>
          </div>
        </div>
        <div class="card-info" onclick="openAlbumModal('${escapeHtml(a.id)}')">
          <div class="card-title" title="${escapeHtml(a.title)}"><strong>${escapeHtml(a.title)}</strong></div>
          <div class="card-artist" title="${escapeHtml(a.artist)}">${escapeHtml(a.artist)}</div>
          <div class="card-meta-row">
            <span>${escapeHtml(a.release_year || "")} • ${a.track_count || 10} Tracks</span>
            <span>💬 ${a.review_count || 0}</span>
          </div>
        </div>
      </div>
    `;
}

function renderAlbumsGrid(albums, append = false) {
  const grid = document.getElementById("albumsGrid");
  if (!grid) return;
  if (!append) {
    displayedAlbumKeys.clear();
  }
  if (!append && (!albums || albums.length === 0)) {
    grid.innerHTML = `<p style="color:var(--text-secondary);">No albums found.</p>`;
    return;
  }

  const toRender = [];
  for (const a of albums || []) {
    const sig = `${(a.title || "").toLowerCase()}|${(a.artist || "").toLowerCase()}`;
    if (displayedAlbumKeys.has(a.id) || displayedAlbumKeys.has(sig)) continue;
    displayedAlbumKeys.add(a.id);
    displayedAlbumKeys.add(sig);
    toRender.push(a);
  }

  const html = toRender.map(albumCardHtml).join("");
  if (append) {
    grid.insertAdjacentHTML("beforeend", html);
  } else {
    grid.innerHTML = html;
  }
}

async function loadMoreAlbums() {
  if (albumsScrollLoading) return;
  const albumsPanel = document.getElementById("tab-albums");
  if (!albumsPanel || !albumsPanel.classList.contains("active")) return;

  albumsScrollLoading = true;
  const loadingEl = document.getElementById("albumsLoadingText");
  if (loadingEl) loadingEl.style.display = "inline-block";

  try {
    const page = albumsScrollPage++;
    const res = await fetch(`/api/discover/more?type=albums&page=${page}&q=${encodeURIComponent(currentAlbumsQuery)}`);
    if (res.ok) {
      const data = await res.json();
      const items = data.results || [];
      if (items.length > 0) {
        const existingIds = new Set(appState.albums.map((a) => a.id));
        items.forEach((it) => {
          if (!existingIds.has(it.id)) appState.albums.push(it);
        });
        renderAlbumsGrid(items, true);
      }
    }
  } catch (_) {
  } finally {
    albumsScrollLoading = false;
    if (loadingEl) loadingEl.style.display = "none";
  }
}

async function searchAlbumsDirect(query, btnEl) {
  if (btnEl) {
    document.querySelectorAll("#tab-albums .filter-bar .chip").forEach((b) => b.classList.remove("active"));
    btnEl.classList.add("active");
  }
  currentAlbumsQuery = query || "";
  albumsScrollPage = 0;
  if (appState.backendAvailable) {
    const res = await fetch(`/api/albums/search?q=${encodeURIComponent(query)}`);
    const data = await res.json();
    if (data.results) {
      renderAlbumsGrid(data.results, false);
    }
  }
}

async function openAlbumModal(albumId) {
  if (appState.backendAvailable) {
    try {
      const res = await fetch(`/api/album?id=${encodeURIComponent(albumId)}`);
      if (res.ok) {
        const album = await res.json();
        appState.currentModalAlbum = album;

        document.getElementById("albumModalCover").src = album.cover_url;
        document.getElementById("albumModalTitle").textContent = album.title;
        document.getElementById("albumModalArtist").textContent = album.artist;
        document.getElementById("albumModalYear").textContent = album.release_year || "";
        document.getElementById("albumModalTrackCount").textContent = album.track_count || (album.tracks || []).length;
        document.getElementById("albumModalGenre").textContent = album.genre || "Music";

        const avgScore = album.avg_rating ? `${album.avg_rating.toFixed(1)} ★` : "No Ratings Yet";
        document.getElementById("albumModalAvgRating").textContent = avgScore;

        const trackAvgEl = document.getElementById("albumModalTrackAvgScore");
        if (album.avg_track_score) {
          trackAvgEl.textContent = `${album.avg_track_score} ★`;
        } else {
          trackAvgEl.textContent = "— (Tracks not rated yet)";
        }

        renderAlbumTracklist(album.tracks || []);
        renderAlbumHistogram(album.histogram || {});
        renderAlbumReviews(album.reviews || []);

        document.getElementById("albumModal").classList.remove("hidden");
      }
    } catch (err) {
      console.error(err);
    }
  }
}

function renderAlbumTracklist(tracks) {
  const box = document.getElementById("albumTracklistTable");
  if (!box) return;
  if (!tracks || tracks.length === 0) {
    box.innerHTML = `<div style="padding:12px;color:var(--text-muted);">Tracklist could not be loaded.</div>`;
    return;
  }

  box.innerHTML = tracks
    .map((t) => {
      const min = Math.floor(t.duration_sec / 60);
      const sec = String(t.duration_sec % 60).padStart(2, "0");
      const safeTitle = (t.title || "").replace(/'/g, "\\'");
      const safeArtist = ((appState.currentModalAlbum && appState.currentModalAlbum.artist) || "").replace(/'/g, "\\'");
      const safeCover = (appState.currentModalAlbum && appState.currentModalAlbum.cover_url) || "";
      const rText = t.rating
        ? `<button class="btn-mini-play" style="color:var(--lb-green);border-color:rgba(0,224,84,0.4);" onclick="rateTrackFromAlbum('${t.id}', '${safeTitle}', '${t.preview_url || ""}')">${t.rating}★</button>`
        : `<button class="btn-mini-play" onclick="rateTrackFromAlbum('${t.id}', '${safeTitle}', '${t.preview_url || ""}')">★ Rate</button>`;
      return `
      <div class="album-track-row">
        <div class="album-track-left" onclick="quickPlayPreviewDirect('${t.preview_url}', '${safeTitle}', '${safeArtist}', '${safeCover}')">
          <span class="album-track-num">${t.track_number}</span>
          <strong>${escapeHtml(t.title)}</strong>
        </div>
        <div class="album-track-right">
          <span style="color:var(--text-muted);font-size:0.74rem;">${min}:${sec}</span>
          ${t.preview_url ? `<button class="btn-mini-play" onclick="quickPlayPreviewDirect('${t.preview_url}', '${safeTitle}', '${safeArtist}', '${safeCover}')">▶ Play</button>` : ""}
          <span style="min-width:52px;text-align:right;">${rText}</span>
        </div>
      </div>
    `;
    })
    .join("");
}

function rateTrackFromAlbum(trackId, title, previewUrl) {
  const a = appState.currentModalAlbum || {};
  if (!appState.tracks.find((x) => x.id === trackId)) {
    appState.tracks.unshift({
      id: trackId,
      title: title,
      artist: a.artist || "Artist",
      album: a.title || "Album",
      release_year: a.release_year || 2024,
      genre: a.genre || "Music",
      cover_url: a.cover_url || "",
      preview_url: previewUrl || "",
      avg_rating: 0,
      review_count: 0,
      histogram: {},
    });
  }
  closeAlbumModal();
  openTrackModal(trackId);
}

function quickPlayPreviewDirect(url, title, artist, cover) {
  initAudioElementListeners();
  if (!url) {
    showToast("No audio preview available for this track.");
    return;
  }
  const bar = document.getElementById("audioPlayerBar");
  const audio = document.getElementById("audioElement");

  if (currentPlayingUrl === url && audio.src && !bar.classList.contains("hidden")) {
    toggleAudioPlayPause();
    return;
  }

  currentPlayingTrackId = null;
  currentPlayingUrl = url;
  document.getElementById("playerCover").src = cover;
  document.getElementById("playerTitle").textContent = title;
  document.getElementById("playerArtist").textContent = `${artist}`;
  bar.classList.remove("hidden");
  audio.src = url;
  audio.play().catch(() => {});
  syncPlayerButtonsUI();
}

function renderAlbumHistogram(hist) {
  const barsEl = document.getElementById("albumModalHistogramBars");
  if (!barsEl) return;
  const steps = ["0.5", "1.0", "1.5", "2.0", "2.5", "3.0", "3.5", "4.0", "4.5", "5.0"];
  const maxVal = Math.max(1, ...steps.map((s) => hist[s] || 0));

  barsEl.innerHTML = steps
    .map((s) => {
      const cnt = hist[s] || 0;
      const pct = Math.max(6, Math.round((cnt / maxVal) * 100));
      return `
      <div class="hist-bar-col" title="${s}★: ${cnt} votes">
        <div class="hist-bar" style="height:${pct}%;opacity:${cnt > 0 ? 1 : 0.25}"></div>
        <span class="hist-label">${s}</span>
      </div>
    `;
    })
    .join("");
}

function renderAlbumReviews(reviews) {
  const box = document.getElementById("albumReviewsList");
  if (!box) return;
  if (!reviews || reviews.length === 0) {
    box.innerHTML = `<p style="color:var(--text-muted);font-size:0.82rem;">Be the first to review this album!</p>`;
    return;
  }

  box.innerHTML = reviews
    .map(
      (r) => `
    <div style="background:var(--bg-elevated);border:1px solid var(--border-subtle);border-radius:6px;padding:10px;">
      <div style="display:flex;justify-content:space-between;font-size:0.82rem;margin-bottom:4px;">
        <strong>👤 @${escapeHtml(r.username)}</strong>
        <span class="review-stars">${formatStars(r.rating)} ${r.liked ? '<span class="review-heart">♥</span>' : ""}</span>
      </div>
      <p style="font-size:0.85rem;color:#e2e8f0;">${r.review_text ? escapeHtml(r.review_text) : ""}</p>
      <div style="font-size:0.7rem;color:var(--text-muted);margin-top:4px;">
        📅 ${escapeHtml(r.listen_date || "Today")}
      </div>
    </div>
  `
    )
    .join("");
}

function updateAlbumStarDisplay(val) {
  const disp = document.getElementById("albumStarDisplay");
  if (disp) {
    disp.textContent = `${formatStars(val)} (${parseFloat(val).toFixed(1)})`;
  }
}

function toggleAlbumLikeBtn() {
  appState.albumLiked = !appState.albumLiked;
  const btn = document.getElementById("albumLikeBtn");
  if (btn) {
    btn.classList.toggle("active", appState.albumLiked);
    btn.textContent = appState.albumLiked ? "♥ Favorite Album" : "♡ Like";
  }
}

async function submitAlbumReviewForm(e) {
  e.preventDefault();
  if (!appState.currentModalAlbum) return;

  const a = appState.currentModalAlbum;
  const ratingVal = parseFloat(document.getElementById("albumRatingRange").value);
  const payload = {
    album_id: a.id,
    title: a.title || "Album",
    artist: a.artist || "Artist",
    genre: a.genre || "Music",
    cover_url: a.cover_url || "",
    release_year: a.release_year || 2024,
    track_count: a.track_count || 10,
    rating: ratingVal,
    liked: appState.albumLiked,
    review_text: document.getElementById("albumReviewInput").value.trim(),
    listen_date: new Date().toISOString().slice(0, 10),
    username: "batin",
  };

  try {
    if (appState.backendAvailable) {
      await fetch("/api/album/review", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      showToast(`✓ Logged ${ratingVal}★ rating for "${a.title}"!`);
      await openAlbumModal(a.id);
      await loadAlbums();
    }
  } catch (err) {
    console.error(err);
  }
}

function closeAlbumModal() {
  document.getElementById("albumModal").classList.add("hidden");
}

// ============================================================================
// TAB SWITCHING & INITIALIZATION
// ============================================================================
function switchTab(tabName) {
  document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
  document.querySelectorAll(".nav-tab").forEach((b) => b.classList.remove("active"));

  const target = document.getElementById(`tab-${tabName}`);
  if (target) target.classList.add("active");

  const btn = document.querySelector(`.nav-tab[data-tab="${tabName}"]`);
  if (btn) btn.classList.add("active");

  if (tabName === "albums") {
    loadAlbums().then(() => loadMoreAlbums());
  }
}

// ============================================================================
// SEARCH SUGGESTIONS (instant real-time typeahead while typing)
// ============================================================================
let suggestTimer = null;
let suggestSeq = 0;
let suggestAbort = null;
let suggestItems = [];
let suggestActive = -1;
let searchSubmitted = false;
const clientSuggestCache = new Map();

function hideSuggestions() {
  const box = document.getElementById("searchSuggestions");
  if (box) box.classList.add("hidden");
  suggestActive = -1;
}

function cancelSuggestionsAndHide() {
  searchSubmitted = true;
  clearTimeout(suggestTimer);
  suggestSeq++;
  if (suggestAbort) {
    try {
      suggestAbort.abort();
    } catch (_) {}
    suggestAbort = null;
  }
  hideSuggestions();
}

function getLocalMatches(query) {
  const q = query.toLowerCase();
  const matchesPrefix = (str) => {
    const s = (str || "").toLowerCase();
    return s.startsWith(q) || s.includes(" " + q);
  };
  const songs = (appState.tracks || [])
    .filter((t) => matchesPrefix(t.title) || matchesPrefix(t.artist))
    .slice(0, 2);
  const albums = (appState.albums || [])
    .filter((a) => matchesPrefix(a.title) || matchesPrefix(a.artist))
    .slice(0, 2);
  return { songs, albums };
}

function renderSuggestions(data, query, isLoadingLive = false) {
  if (searchSubmitted) return;
  const box = document.getElementById("searchSuggestions");
  if (!box) return;
  const songs = data.songs || [];
  const albums = data.albums || [];
  suggestItems = [
    ...songs.map((s) => ({ type: "song", data: s })),
    ...albums.map((a) => ({ type: "album", data: a })),
  ];
  suggestActive = -1;

  if (suggestItems.length === 0) {
    box.innerHTML = isLoadingLive
      ? `<div class="suggest-empty">🔍 Finding suggestions for "${escapeHtml(query)}"...</div>`
      : `<div class="suggest-empty">No results found for "${escapeHtml(query)}"</div>`;
    box.classList.remove("hidden");
    return;
  }

  const row = (item, idx) => {
    const d = item.data;
    const sub = item.type === "song" ? `Track • ${d.artist}` : `Album • ${d.artist}`;
    return `
      <div class="suggest-item" data-idx="${idx}">
        <img src="${escapeHtml(d.cover_url || "")}" alt="" onerror="this.src='https://placehold.co/80x80/1b2228/00e054?text=♪'" />
        <div class="suggest-text">
          <div class="suggest-title">${escapeHtml(d.title)}</div>
          <div class="suggest-sub">${escapeHtml(sub)}</div>
        </div>
      </div>`;
  };

  let html = "";
  if (songs.length) {
    html += `<div class="suggest-group">TRACKS</div>`;
    html += songs.map((_, i) => row(suggestItems[i], i)).join("");
  }
  if (albums.length) {
    html += `<div class="suggest-group">ALBUMS</div>`;
    html += albums.map((_, i) => row(suggestItems[songs.length + i], songs.length + i)).join("");
  }
  box.innerHTML = html;
  box.classList.remove("hidden");
}

function mergeSuggestResults(localData, liveData) {
  const seenSongs = new Set();
  const songs = [];
  for (const s of [...(liveData.songs || []), ...(localData.songs || [])]) {
    const key = `${(s.title || "").toLowerCase()}|${(s.artist || "").toLowerCase()}`;
    if (!seenSongs.has(key) && songs.length < 7) {
      seenSongs.add(key);
      songs.push(s);
    }
  }
  const seenAlbums = new Set();
  const albums = [];
  for (const a of [...(liveData.albums || []), ...(localData.albums || [])]) {
    const key = `${(a.title || "").toLowerCase()}|${(a.artist || "").toLowerCase()}`;
    if (!seenAlbums.has(key) && albums.length < 4) {
      seenAlbums.add(key);
      albums.push(a);
    }
  }
  return { songs, albums };
}

async function fetchSuggestions(query) {
  if (searchSubmitted) return;
  const key = query.toLowerCase();
  if (clientSuggestCache.has(key)) {
    const curVal = (document.getElementById("globalSearchInput")?.value || "").trim();
    if (!searchSubmitted && curVal) {
      renderSuggestions(clientSuggestCache.get(key), curVal, false);
    }
    return;
  }

  if (suggestAbort) {
    try {
      suggestAbort.abort();
    } catch (_) {}
  }
  const ctrl = new AbortController();
  suggestAbort = ctrl;

  try {
    const res = await fetch(`/api/suggest?q=${encodeURIComponent(query)}`, { signal: ctrl.signal });
    const liveData = await res.json();
    if (searchSubmitted) return;
    const input = document.getElementById("globalSearchInput");
    const curVal = (input ? input.value : "").trim();
    if (!curVal) {
      hideSuggestions();
      return;
    }
    const merged = mergeSuggestResults(getLocalMatches(curVal), liveData);
    clientSuggestCache.set(key, merged);
    // Render immediately while user is typing (even if they typed 1-2 more letters while in flight)
    if (curVal.toLowerCase().startsWith(key) || key.startsWith(curVal.toLowerCase())) {
      renderSuggestions(merged, curVal, false);
    }
  } catch (_) {}
}

function selectSuggestion(idx) {
  const item = suggestItems[idx];
  if (!item) return;
  cancelSuggestionsAndHide();
  const input = document.getElementById("globalSearchInput");
  if (item.type === "song") {
    const s = item.data;
    if (!appState.tracks.find((t) => t.id === s.id)) {
      appState.tracks.unshift({
        avg_rating: 0,
        review_count: 0,
        histogram: {},
        ...s,
        cover_url: (s.cover_url || "").replace("300x300bb", "600x600bb"),
      });
    }
    if (input) input.value = "";
    openTrackModal(s.id);
  } else {
    if (input) input.value = "";
    openAlbumModal(item.data.id);
  }
}

function highlightSuggestion() {
  document.querySelectorAll("#searchSuggestions .suggest-item").forEach((el) => {
    el.classList.toggle("active", Number(el.dataset.idx) === suggestActive);
  });
}

document.addEventListener("DOMContentLoaded", () => {
  const searchInput = document.getElementById("globalSearchInput");
  const searchBtn = document.getElementById("globalSearchBtn");
  const box = document.getElementById("searchSuggestions");

  if (searchInput) {
    searchInput.addEventListener("input", () => {
      const q = searchInput.value.trim();
      clearTimeout(suggestTimer);
      if (q.length < 1) {
        cancelSuggestionsAndHide();
        return;
      }
      searchSubmitted = false;
      // 1. Show instant local matches (or loading state) in 0ms while typing!
      const cached = clientSuggestCache.get(q.toLowerCase());
      if (cached) {
        renderSuggestions(cached, q, false);
        return;
      }
      const local = getLocalMatches(q);
      renderSuggestions(local, q, true);

      // 2. Fetch live catalog matches with minimal 80ms debounce while typing
      suggestTimer = setTimeout(() => fetchSuggestions(q), 80);
    });

    searchInput.addEventListener("keydown", (e) => {
      const open = box && !box.classList.contains("hidden") && suggestItems.length > 0;
      if (e.key === "ArrowDown" && open) {
        e.preventDefault();
        suggestActive = (suggestActive + 1) % suggestItems.length;
        highlightSuggestion();
      } else if (e.key === "ArrowUp" && open) {
        e.preventDefault();
        suggestActive = (suggestActive - 1 + suggestItems.length) % suggestItems.length;
        highlightSuggestion();
      } else if (e.key === "Enter") {
        e.preventDefault();
        if (open && suggestActive >= 0) {
          selectSuggestion(suggestActive);
        } else {
          const val = searchInput.value;
          cancelSuggestionsAndHide();
          searchInput.blur();
          performLiveSearch(val);
        }
      } else if (e.key === "Escape") {
        cancelSuggestionsAndHide();
      }
    });

    searchInput.addEventListener("focus", () => {
      const q = searchInput.value.trim();
      if (q.length >= 1 && !searchSubmitted) {
        const local = clientSuggestCache.get(q.toLowerCase()) || getLocalMatches(q);
        renderSuggestions(local, q, false);
      }
    });
  }

  if (box) {
    // mousedown fires before the input's blur, so the click is not lost
    box.addEventListener("mousedown", (e) => {
      const el = e.target.closest(".suggest-item");
      if (el) {
        e.preventDefault();
        selectSuggestion(Number(el.dataset.idx));
      }
    });
  }

  document.addEventListener("click", (e) => {
    if (!e.target.closest(".search-box")) hideSuggestions();
  });

  if (searchBtn) {
    searchBtn.addEventListener("click", () => {
      const val = searchInput.value;
      cancelSuggestionsAndHide();
      performLiveSearch(val);
    });
  }

  // Infinite scroll via IntersectionObserver + scroll listener fallback
  const tracksSentinel = document.getElementById("tracksInfiniteSentinel");
  const albumsSentinel = document.getElementById("albumsInfiniteSentinel");
  if ("IntersectionObserver" in window) {
    const obs = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            if (entry.target.id === "tracksInfiniteSentinel") loadMoreTracks();
            if (entry.target.id === "albumsInfiniteSentinel") loadMoreAlbums();
          }
        });
      },
      { rootMargin: "500px" }
    );
    if (tracksSentinel) obs.observe(tracksSentinel);
    if (albumsSentinel) obs.observe(albumsSentinel);
  }

  window.addEventListener(
    "scroll",
    () => {
      if (tracksSentinel) {
        const rect = tracksSentinel.getBoundingClientRect();
        if (rect.top < window.innerHeight + 500) loadMoreTracks();
      }
      if (albumsSentinel) {
        const rect = albumsSentinel.getBoundingClientRect();
        if (rect.top < window.innerHeight + 500) loadMoreAlbums();
      }
    },
    { passive: true }
  );

  loadBootstrap().then(() => {
    // Immediately load the first discovery batch so the initial grid is extra rich
    loadMoreTracks();
  });
});
