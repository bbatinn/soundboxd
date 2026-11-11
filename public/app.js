// ============================================================================
// SOUNDBOXD — Frontend Application & 4-Tier AI Model Router Client
// Hierarchy: 1. Gemini Flash -> 2. Gemini Pro -> 3. Claude Sonnet 4.5 -> 4. Gemini 4 Argon (LAST/ULTIMATE)
// ============================================================================

let appState = {
  tracks: [],
  reviews: [],
  favorites: [],
  listenlist: [],
  custom_lists: [],
  token_summary: [],
  recent_token_logs: [],
  currentModalTrack: null,
  currentLiked: true,
  backendAvailable: true,
};

// Format numeric rating (0.5 - 5.0) to Letterboxd stars "★★★★½"
function formatStars(rating) {
  const num = parseFloat(rating) || 0;
  const full = Math.floor(num);
  const half = num - full >= 0.5 ? "½" : "";
  return "★".repeat(full) + half;
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
    btn.textContent = appState.currentLiked ? "♥ Beğendim" : "♡ Beğen";
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
    console.warn("Sunucu bağlantısı yerine yerel mod aktif:", err);
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
      review_text: "Gece 3'te otobanda tek başına sürerken çalan o barok synth melodisi... Daft Punk'ın en duygusal başyapıtı.",
      listen_date: "2026-11-10",
      tags: "gece-surusu,synth,bas-yapit",
      ai_moderated_by: "Gemini 3.8 Flash",
    },
  ];
  appState.token_summary = [
    { model_tier: "Tier 1: Hızlı/Ekonomik", model_name: "Gemini 3.8 Flash", calls: 2, total_tokens: 400, saved_argon: 400 },
    { model_tier: "Tier 2: Dengeli Analiz", model_name: "Gemini 2.5 Pro", calls: 1, total_tokens: 610, saved_argon: 610 },
    { model_tier: "Tier 3: Edebi & Yaratıcı", model_name: "Claude Sonnet 4.5", calls: 1, total_tokens: 790, saved_argon: 790 },
    { model_tier: "Tier 4: Zirve Sentez (En Değerli)", model_name: "Gemini 4 Argon", calls: 1, total_tokens: 1300, saved_argon: 0 },
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
  renderTokenRouterStats();
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

function renderTracksGrid(tracks, targetId = "tracksGrid") {
  const grid = document.getElementById(targetId);
  if (!grid) return;
  if (!tracks || tracks.length === 0) {
    grid.innerHTML = `<p style="color:var(--text-secondary);">Henüz şarkı bulunamadı. Yukarıdaki arama çubuğundan dilediğin şarkıyı arayabilirsin.</p>`;
    return;
  }

  grid.innerHTML = tracks
    .map((t) => {
      const avg = t.avg_rating && t.avg_rating > 0 ? `${t.avg_rating.toFixed(1)} ★` : "Yeni";
      return `
      <div class="track-card">
        <div class="poster-wrap" onclick="openTrackModal('${t.id}')">
          <img src="${t.cover_url}" alt="${t.title}" loading="lazy" onerror="this.src='https://placehold.co/400x400/1b2228/00e054?text=Soundboxd'" />
          <span class="rating-pill-corner">${avg}</span>
          <div class="poster-overlay">
            <div class="overlay-actions">
              <button class="btn-overlay" onclick="event.stopPropagation(); quickPlayPreview('${t.id}')">
                ▶ Dinle
              </button>
              <button class="btn-overlay" onclick="event.stopPropagation(); openTrackModal('${t.id}')">
                ★ Puanla
              </button>
            </div>
          </div>
        </div>
        <div class="card-info" onclick="openTrackModal('${t.id}')">
          <div class="card-title" title="${t.title}">${t.title}</div>
          <div class="card-artist" title="${t.artist}">${t.artist}</div>
          <div class="card-meta-row">
            <span>${t.release_year || ""}</span>
            <span>💬 ${t.review_count || 0} • ♥ ${t.likes_count || 0}</span>
          </div>
        </div>
      </div>
    `;
    })
    .join("");
}

function renderRecentReviews() {
  const el = document.getElementById("recentReviewsList");
  if (!el) return;
  el.innerHTML = appState.reviews
    .slice(0, 8)
    .map((r) => {
      const tags = (r.tags || "")
        .split(",")
        .filter(Boolean)
        .map((tg) => `<span class="tag-chip">#${tg.trim()}</span>`)
        .join("");
      return `
      <div class="review-card">
        <img class="review-card-cover" src="${r.track_cover}" alt="${r.track_title}" onclick="openTrackModal('${r.track_id}')" onerror="this.src='https://placehold.co/200x200/1b2228/00e054?text=♪'" />
        <div class="review-card-body">
          <div class="review-header">
            <span class="review-track-title" onclick="openTrackModal('${r.track_id}')">
              ${r.track_title} <small style="color:var(--text-secondary);">(${r.track_artist})</small>
            </span>
            <span>
              <span class="review-stars">${formatStars(r.rating)}</span>
              ${r.liked ? '<span class="review-heart">♥</span>' : ""}
            </span>
          </div>
          <p class="review-text">${r.review_text || "<em>Sadece puan verildi.</em>"}</p>
          <div class="review-footer">
            <div>${tags}</div>
            <span>👤 @${r.username} • ⚡ ${r.ai_moderated_by || "Gemini Flash"}</span>
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
        .map((tg) => `<span class="tag-chip">#${tg.trim()}</span>`)
        .join("");
      return `
      <tr>
        <td style="white-space:nowrap;color:var(--text-secondary);">${r.listen_date || "2026-11-11"}</td>
        <td>
          <img class="diary-cover" src="${r.track_cover}" alt="" onclick="openTrackModal('${r.track_id}')" style="cursor:pointer;" />
        </td>
        <td>
          <strong style="cursor:pointer;" onclick="openTrackModal('${r.track_id}')">${r.track_title}</strong><br/>
          <span style="color:var(--text-secondary);font-size:0.78rem;">${r.track_artist}</span>
        </td>
        <td>${r.release_year || ""}</td>
        <td><span class="review-stars">${formatStars(r.rating)}</span> <small>(${r.rating})</small></td>
        <td>${r.liked ? '<span class="review-heart">♥</span>' : "—"}</td>
        <td>
          <div style="margin-bottom:4px;">${r.review_text || ""}</div>
          <div>${tags}</div>
        </td>
        <td><span class="tag-chip" style="color:var(--lb-green);">${r.ai_moderated_by || "Gemini Flash"}</span></td>
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
  container.innerHTML = (appState.custom_lists || [])
    .map((lst) => {
      const strip = (lst.tracks || [])
        .slice(0, 5)
        .map((t) => `<img src="${t.cover_url}" alt="${t.title}" title="${t.title} - ${t.artist}" onclick="openTrackModal('${t.id}')" style="cursor:pointer;" />`)
        .join("");
      return `
      <div class="list-card">
        <h3>${lst.title}</h3>
        <p style="font-size:0.83rem;color:var(--text-secondary);margin-top:4px;">${lst.description || ""}</p>
        <div class="list-posters-strip">${strip}</div>
        <div style="font-size:0.74rem;color:var(--text-muted);">
          Küratör: <strong>@${lst.created_by || "batin"}</strong> • ${(lst.tracks || []).length} şarkı
        </div>
      </div>
    `;
    })
    .join("");
}

function renderTokenRouterStats() {
  const tbody = document.getElementById("tokenSummaryBody");
  if (tbody) {
    tbody.innerHTML = (appState.token_summary || [])
      .map(
        (row) => `
      <tr>
        <td><strong>${row.model_tier}</strong></td>
        <td>${row.model_name}</td>
        <td>${row.calls}</td>
        <td>${row.total_tokens} token</td>
        <td style="color:var(--lb-green);font-weight:700;">
          ${row.saved_argon > 0 ? `+${row.saved_argon} Argon Tokenı Korundu` : "Zirve Sentezde Kullanıldı"}
        </td>
      </tr>
    `
      )
      .join("");
  }

  const recentEl = document.getElementById("recentTokenLogs");
  if (recentEl) {
    recentEl.innerHTML = (appState.recent_token_logs || [])
      .map(
        (lg) => `
      <div class="token-log-item">
        <div>
          <strong>${lg.model_name}</strong> — <span style="color:var(--text-secondary);">${lg.task_type}</span>
        </div>
        <div style="font-family:'JetBrains Mono',monospace;color:var(--lb-blue);">
          ${lg.prompt_tokens + lg.completion_tokens} tok
        </div>
      </div>
    `
      )
      .join("");
  }
}

// ============================================================================
// SEARCH & FILTERS (Live iTunes Public Catalog + Local Ratings)
// ============================================================================
async function performLiveSearch(query) {
  if (!query || !query.trim()) {
    document.getElementById("tracksGridTitle").textContent = "POPÜLER & KÜRATÖRLÜ ŞARKILAR";
    renderTracksGrid(appState.tracks);
    return;
  }

  switchTab("discover");
  const titleEl = document.getElementById("tracksGridTitle");
  titleEl.textContent = `"${query}" İÇİN CANLI KATALOG ARANIYOR...`;

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
        titleEl.textContent = `"${query.toUpperCase()}" ARAMA SONUÇLARI (${data.results.length} ŞARKI)`;
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
    titleEl.textContent = `"${query.toUpperCase()}" ARAMA SONUÇLARI (${mapped.length} ŞARKI)`;
    renderTracksGrid(mapped);
  } catch (e) {
    titleEl.textContent = `"${query}" SONUÇLARI`;
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
    document.getElementById("tracksGridTitle").textContent = "EN YÜKSEK PUANLI ŞARKILAR (4.5★+)";
    renderTracksGrid(appState.tracks.filter((t) => (t.avg_rating || 0) >= 4.5));
  } else {
    document.getElementById("tracksGridTitle").textContent = "POPÜLER & KÜRATÖRLÜ ŞARKILAR";
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
// AUDIO PREVIEW PLAYER (30-Second Legal Stream via Official Metadata)
// ============================================================================
async function quickPlayPreview(trackId) {
  let track = appState.tracks.find((t) => t.id === trackId);
  if (!track) return;

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
    alert("Bu parça için 30sn önizleme bulunamadı, ancak detay sayfasından puanlayabilirsin.");
    return;
  }

  const bar = document.getElementById("audioPlayerBar");
  const audio = document.getElementById("audioElement");
  document.getElementById("playerCover").src = track.cover_url;
  document.getElementById("playerTitle").textContent = track.title;
  document.getElementById("playerArtist").textContent = `${track.artist} • ${track.album} (30sn Yasal Önizleme)`;
  bar.classList.remove("hidden");
  audio.src = track.preview_url;
  audio.play().catch(() => {});
}

function stopAudioPreview() {
  const audio = document.getElementById("audioElement");
  audio.pause();
  document.getElementById("audioPlayerBar").classList.add("hidden");
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
  listenBtn.textContent = track.in_listenlist ? "✓ Dinleme Listemde (Çıkar)" : "+ Dinleme Listeme Ekle";

  renderModalHistogram(track);
  renderModalReviews(track);

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
  avgEl.textContent = track.avg_rating ? `${track.avg_rating.toFixed(2)} ★ (${track.review_count} oy)` : "Henüz puan yok";

  const barsEl = document.getElementById("modalHistogramBars");
  const hist = track.histogram || {};
  const steps = ["0.5", "1.0", "1.5", "2.0", "2.5", "3.0", "3.5", "4.0", "4.5", "5.0"];
  const maxVal = Math.max(1, ...steps.map((s) => hist[s] || 0));

  barsEl.innerHTML = steps
    .map((s) => {
      const cnt = hist[s] || 0;
      const pct = Math.max(6, Math.round((cnt / maxVal) * 100));
      return `
      <div class="hist-bar-col" title="${s}★: ${cnt} oy">
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
    listEl.innerHTML = `<p style="color:var(--text-muted);font-size:0.84rem;">Bu şarkı için ilk incelemeyi sen yaz!</p>`;
    return;
  }
  listEl.innerHTML = revs
    .map(
      (r) => `
    <div style="background:var(--bg-elevated);border:1px solid var(--border-subtle);border-radius:6px;padding:10px;">
      <div style="display:flex;justify-content:space-between;font-size:0.82rem;margin-bottom:4px;">
        <strong>👤 @${r.username}</strong>
        <span class="review-stars">${formatStars(r.rating)} ${r.liked ? '<span class="review-heart">♥</span>' : ""}</span>
      </div>
      <p style="font-size:0.85rem;color:#e2e8f0;">${r.review_text || ""}</p>
      <div style="font-size:0.7rem;color:var(--text-muted);margin-top:4px;">
        📅 ${r.listen_date || ""} • ⚡ Denetim: ${r.ai_moderated_by || "Gemini 3.8 Flash"}
      </div>
    </div>
  `
    )
    .join("");
}

async function submitReviewForm(e) {
  e.preventDefault();
  if (!appState.currentModalTrack) return;

  const payload = {
    track_id: appState.currentModalTrack.id,
    rating: parseFloat(document.getElementById("ratingRangeInput").value),
    liked: appState.currentLiked,
    review_text: document.getElementById("reviewTextInput").value.trim(),
    listen_date: document.getElementById("listenDateInput").value,
    tags: document.getElementById("reviewTagsInput").value.trim(),
    username: "batin",
  };

  if (appState.backendAvailable) {
    const res = await fetch("/api/review", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (res.ok) {
      await loadBootstrap();
      await openTrackModal(appState.currentModalTrack.id);
      return;
    }
  }

  // Fallback local save
  appState.reviews.unshift({
    id: Date.now(),
    ...payload,
    track_title: appState.currentModalTrack.title,
    track_artist: appState.currentModalTrack.artist,
    track_cover: appState.currentModalTrack.cover_url,
    release_year: appState.currentModalTrack.release_year,
    tags: payload.tags || "atmosferik,favori",
    ai_moderated_by: "Gemini 3.8 Flash",
  });
  renderAll();
  closeTrackModal();
}

async function toggleCurrentModalListenlist() {
  if (!appState.currentModalTrack) return;
  if (appState.backendAvailable) {
    await fetch("/api/listenlist/toggle", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ track_id: appState.currentModalTrack.id }),
    });
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
    alert(`#${slot} numaralı favori şarkın "${appState.currentModalTrack.title}" olarak güncellendi!`);
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
    result: { poetic_review: "“Bu parça zamanın akışını yavaşlatan nadir kayıtlar arasında.”" },
  };
}

async function assistReviewWithClaude() {
  if (!appState.currentModalTrack) return;
  const helperEl = document.getElementById("modalAiHelperOutput");
  helperEl.classList.remove("hidden");
  helperEl.innerHTML = `✒️ <strong>Claude Sonnet 4.5 (Tier 3)</strong> edebi inceleme kurguluyor (Argon tokenları korunuyor)...`;

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
    <div><strong>✒️ ${data.model_name} (${data.model_tier})</strong> tarafından üretildi (${data.usage.total_tokens} token • <strong>+${data.usage.saved_argon_tokens} Argon tokenı korundu</strong>):</div>
    <div style="margin-top:4px;color:#cbd5e1;">İnceleme metni kutuya aktarıldı, dilediğin gibi düzenleyebilirsin!</div>
  `;
}

async function assistSimilarWithPro() {
  if (!appState.currentModalTrack) return;
  const helperEl = document.getElementById("modalAiHelperOutput");
  helperEl.classList.remove("hidden");
  helperEl.innerHTML = `🔷 <strong>Gemini 2.5 Pro (Tier 2)</strong> akustik benzerlik analizi yapıyor...`;

  const data = await callModelRouter("similar_tracks", {
    track_title: appState.currentModalTrack.title,
    artist: appState.currentModalTrack.artist,
    genre: appState.currentModalTrack.genre,
  });

  const recs = (data.result.recommendations || []).map((r) => `<li>${r}</li>`).join("");
  helperEl.innerHTML = `
    <div><strong>🔷 ${data.model_name} (${data.model_tier})</strong> — ${data.result.sonic_signature || ""}</div>
    <ul style="margin:6px 0 0 18px;">${recs}</ul>
  `;
}

async function triggerAiDemo(taskType) {
  const badge = document.getElementById("aiOutputBadge");
  const stat = document.getElementById("aiOutputTokenStat");
  const body = document.getElementById("aiOutputBody");

  badge.textContent = "Yönlendiriliyor...";
  body.innerHTML = "Model Router görev karmaşıklığını analiz ediyor...";

  const sampleTrack = appState.tracks[0] || { title: "Veridis Quo", artist: "Daft Punk", genre: "Electronic" };
  const data = await callModelRouter(taskType, {
    track_title: sampleTrack.title,
    artist: sampleTrack.artist,
    genre: sampleTrack.genre,
    review_text: "Gece sürüşünde dinlerken analog synth katmanları insanı başka bir boyuta taşıyor.",
  });

  badge.textContent = `${data.model_name} • ${data.model_tier}`;
  stat.textContent = data.cached
    ? `⚡ ÖNBELLEKTEN (0 Yeni Token Harcandı!)`
    : `Harcanan: ${data.usage.total_tokens} token | Korunan Argon: +${data.usage.saved_argon_tokens} token`;

  const r = data.result;
  if (taskType === "moderate_and_tag") {
    body.innerHTML = `
      <h4>⚡ ${data.model_name} — Hızlı Denetim & Etiketleme</h4>
      <p style="margin:6px 0;">${r.summary}</p>
      <div><strong>Otomatik Etiketler:</strong> ${(r.suggested_tags || []).map((t) => `<span class="tag-chip">#${t}</span>`).join(" ")}</div>
    `;
  } else if (taskType === "similar_tracks") {
    body.innerHTML = `
      <h4>🔷 ${r.analysis_title}</h4>
      <p style="margin:6px 0;">${r.sonic_signature}</p>
      <ul style="margin-left:18px;">${(r.recommendations || []).map((x) => `<li>${x}</li>`).join("")}</ul>
    `;
  } else if (taskType === "poetic_review") {
    body.innerHTML = `
      <h4>✒️ ${r.editorial_title}</h4>
      <blockquote style="border-left:3px solid var(--tier-claude);padding-left:12px;margin:8px 0;font-style:italic;color:#f8fafc;">
        ${r.poetic_review}
      </blockquote>
      <div style="font-size:0.82rem;color:var(--text-secondary);"><strong>Metafor Eksenleri:</strong> ${r.lyric_metaphor}</div>
    `;
  } else {
    const axesHtml = Object.entries(r.sonic_axes || {})
      .map(
        ([k, v]) => `
        <div style="margin-bottom:6px;">
          <div style="display:flex;justify-content:space-between;font-size:0.8rem;"><span>${k}</span><strong>%${v}</strong></div>
          <div style="background:#1e293b;height:7px;border-radius:4px;overflow:hidden;">
            <div style="background:linear-gradient(90deg,#a855f7,#00e054);width:${v}%;height:100%;"></div>
          </div>
        </div>
      `
      )
      .join("");

    body.innerHTML = `
      <h4>${r.dna_title}</h4>
      <p style="font-size:0.8rem;color:#d8b4fe;margin:4px 0 10px;">🛡️ ${r.pipeline_explanation}</p>
      <div style="background:var(--bg-elevated);padding:12px;border-radius:8px;margin-bottom:12px;">
        <div style="color:var(--lb-green);font-weight:800;margin-bottom:4px;">Müzikal Arketipin: ${r.archetype}</div>
        <p>${r.core_analysis}</p>
      </div>
      <div style="margin-bottom:12px;">${axesHtml}</div>
      <div style="background:rgba(168,85,247,0.15);border:1px solid rgba(168,85,247,0.4);padding:10px;border-radius:6px;">
        <strong>💎 ${r.masterpiece_blindspot}</strong>
      </div>
    `;
  }
}

// ============================================================================
// CUSTOM LISTS MODAL
// ============================================================================
function openCreateListModal() {
  const box = document.getElementById("newListTrackCheckboxes");
  box.innerHTML = appState.tracks
    .map(
      (t) => `
    <label class="checkbox-track-item">
      <input type="checkbox" name="listTrack" value="${t.id}" />
      <span><strong>${t.title}</strong> — ${t.artist}</span>
    </label>
  `
    )
    .join("");
  document.getElementById("listModal").classList.remove("hidden");
}

function closeCreateListModal() {
  document.getElementById("listModal").classList.add("hidden");
}

async function submitNewList(e) {
  e.preventDefault();
  const title = document.getElementById("newListTitle").value.trim();
  const description = document.getElementById("newListDesc").value.trim();
  const checked = Array.from(document.querySelectorAll('input[name="listTrack"]:checked')).map((el) => el.value);

  if (appState.backendAvailable) {
    await fetch("/api/lists/create", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, description, track_ids: checked }),
    });
    await loadBootstrap();
  }
  closeCreateListModal();
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
}

document.addEventListener("DOMContentLoaded", () => {
  const searchInput = document.getElementById("globalSearchInput");
  const searchBtn = document.getElementById("globalSearchBtn");

  if (searchInput) {
    searchInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        performLiveSearch(searchInput.value);
      }
    });
  }
  if (searchBtn) {
    searchBtn.addEventListener("click", () => {
      performLiveSearch(searchInput.value);
    });
  }

  loadBootstrap();
});
