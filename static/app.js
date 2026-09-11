// Daily Finance Hub - Multi-Platform Stock Links (財報狗, 富果 Fugle, 籌碼K線 CMoney)
let currentCategory = "ALL";
let currentSentiment = "ALL";
let currentImpact = "ALL";
let searchQuery = "";
let activeWatchlistTag = "";

let rawNewsData = [];
let marketData = [];
let briefingData = {};
let watchlist = [];

document.addEventListener("DOMContentLoaded", () => {
  lucide.createIcons();
  initEventListeners();
  loadAllData();

  // Auto refresh every 5 minutes
  setInterval(() => {
    loadAllData(false);
  }, 5 * 60 * 1000);
});

function initEventListeners() {
  // Refresh Button
  document.getElementById("btn-refresh-data").addEventListener("click", () => {
    triggerManualRefresh();
  });

  // Export Modal Buttons
  document.getElementById("btn-export-modal").addEventListener("click", () => {
    openExportModal();
  });
  document.getElementById("close-modal-btn").addEventListener("click", closeExportModal);
  document.getElementById("close-modal-footer").addEventListener("click", closeExportModal);
  document.getElementById("copy-export-btn").addEventListener("click", copyExportContent);

  // Export Format Tabs
  document.getElementById("tab-fmt-markdown").addEventListener("click", (e) => switchExportFormat(e, "markdown"));
  document.getElementById("tab-fmt-telegram").addEventListener("click", (e) => switchExportFormat(e, "telegram"));
  document.getElementById("tab-fmt-line").addEventListener("click", (e) => switchExportFormat(e, "line"));

  // Category Tabs
  document.querySelectorAll("#category-tabs .tab-btn").forEach(btn => {
    btn.addEventListener("click", (e) => {
      document.querySelectorAll("#category-tabs .tab-btn").forEach(b => b.classList.remove("active"));
      e.target.classList.add("active");
      currentCategory = e.target.getAttribute("data-cat");
      renderNewsFeed();
    });
  });

  // Search Input
  document.getElementById("news-search-input").addEventListener("input", (e) => {
    searchQuery = e.target.value.toLowerCase().trim();
    renderNewsFeed();
  });

  // Sentiment Filter
  document.getElementById("sentiment-select").addEventListener("change", (e) => {
    currentSentiment = e.target.value;
    renderNewsFeed();
  });

  // Impact Filter
  document.getElementById("impact-select").addEventListener("change", (e) => {
    currentImpact = e.target.value;
    renderNewsFeed();
  });
}

async function loadAllData(showSpin = true) {
  if (showSpin) {
    document.getElementById("spin-icon").classList.add("spinning");
  }
  try {
    const [mRes, nRes, bRes, wRes] = await Promise.all([
      fetch("/api/market").then(r => r.json()),
      fetch("/api/news").then(r => r.json()),
      fetch("/api/briefing").then(r => r.json()),
      fetch("/api/watchlist").then(r => r.json()),
    ]);

    if (mRes.status === "success") marketData = mRes.data;
    if (nRes.status === "success") rawNewsData = nRes.data;
    if (bRes.status === "success") briefingData = bRes.data;
    if (wRes.status === "success") watchlist = wRes.data;

    document.getElementById("last-updated-time").innerText = `最後更新：${nRes.last_updated || new Date().toLocaleTimeString()}`;

    renderMarketCards();
    renderBriefingPanel();
    renderWatchlistTags();
    renderNewsFeed();
  } catch (err) {
    console.error("Error loading data:", err);
  } finally {
    if (showSpin) {
      setTimeout(() => {
        document.getElementById("spin-icon").classList.remove("spinning");
      }, 500);
    }
  }
}

async function triggerManualRefresh() {
  document.getElementById("spin-icon").classList.add("spinning");
  try {
    await fetch("/api/refresh", { method: "POST" });
    await loadAllData(false);
  } catch (e) {
    console.error("Manual refresh failed:", e);
  } finally {
    document.getElementById("spin-icon").classList.remove("spinning");
  }
}

/* Render Market Cards as Interactive Multi-Platform Hub (財報狗, 富果 Fugle, 籌碼K線, TradingView) */
function renderMarketCards() {
  const container = document.getElementById("market-cards-container");
  if (!marketData || marketData.length === 0) {
    container.innerHTML = `<div style="color:var(--text-muted);">載入中...</div>`;
    return;
  }

  container.innerHTML = marketData.map(item => {
    const isUp = item.status === "UP";
    const sign = isUp ? "+" : "";
    const changeClass = isUp ? "UP" : "DOWN";
    const detailUrl = item.detail_url || "#";
    const links = item.platform_links || [];

    const platformBadgesHtml = links.map(p => `
      <a href="${p.url}" target="_blank" class="platform-badge-link" title="開啟 ${p.label}">
        ${p.label} ↗
      </a>
    `).join("");

    return `
      <div class="market-card">
        <div class="market-head">
          <a href="${detailUrl}" target="_blank" class="market-name-link" title="開啟分析">
            ${item.name}
          </a>
        </div>

        <a href="${detailUrl}" target="_blank" class="market-price-link" title="點擊查看分析數據">
          <div class="market-price-row">
            <span class="market-price">${item.price.toLocaleString()}</span>
            <span class="market-change ${changeClass}">${sign}${item.change_pct}%</span>
          </div>
        </a>

        <!-- Quick Platform Direct Links Bar -->
        <div class="platform-links-row">
          ${platformBadgesHtml}
        </div>
      </div>
    `;
  }).join("");
}

/* Render Briefing Panel */
function renderBriefingPanel() {
  if (!briefingData || !briefingData.title) return;

  document.getElementById("briefing-date").innerText = briefingData.date || "";

  // Sentiment Badge & Gauge
  const badgeEl = document.getElementById("sentiment-badge-tag");
  badgeEl.innerText = briefingData.overall_sentiment || "中性觀望";
  badgeEl.className = `sentiment-badge ${briefingData.sentiment_class || "neutral"}`;

  const gaugeFill = document.getElementById("gauge-bar-fill");
  gaugeFill.style.width = `${briefingData.sentiment_gauge || 50}%`;

  // Executive Summary Text
  document.getElementById("exec-summary-text").innerText = briefingData.executive_summary || "";

  // Focus Themes
  const themesContainer = document.getElementById("focus-themes-container");
  themesContainer.innerHTML = (briefingData.top_3_focus_themes || []).map(t => `
    <div class="focus-theme-item">
      <div class="focus-theme-title">${t.theme}</div>
      <div class="focus-theme-desc">${t.desc}</div>
    </div>
  `).join("");

  // Risk Warnings
  const riskContainer = document.getElementById("risk-warnings-container");
  riskContainer.innerHTML = (briefingData.risk_warnings || []).map(r => `
    <div style="margin-bottom:4px;">${r}</div>
  `).join("");
}

/* Render Watchlist Tags */
function renderWatchlistTags() {
  const container = document.getElementById("watchlist-tags-container");
  if (!watchlist || watchlist.length === 0) return;

  container.innerHTML = watchlist.map(tag => {
    const isActive = activeWatchlistTag === tag;
    return `
      <span class="tag-pill ${isActive ? 'active' : ''}" onclick="toggleWatchlistTag('${tag}')">
        🕷️ ${tag}
      </span>
    `;
  }).join("");
}

function toggleWatchlistTag(tag) {
  if (activeWatchlistTag === tag) {
    activeWatchlistTag = "";
  } else {
    activeWatchlistTag = tag;
  }
  renderWatchlistTags();
  renderNewsFeed();
}

/* Render News Feed */
function renderNewsFeed() {
  const container = document.getElementById("news-feed-container");

  let filtered = rawNewsData.filter(item => {
    // Category filter
    if (currentCategory !== "ALL" && item.category !== currentCategory) return false;

    // Sentiment filter
    if (currentSentiment !== "ALL" && item.sentiment !== currentSentiment) return false;

    // Impact filter
    if (currentImpact !== "ALL" && item.impact !== currentImpact) return false;

    // Watchlist Tag filter
    if (activeWatchlistTag) {
      const text = `${item.title} ${item.content}`.toLowerCase();
      if (!text.includes(activeWatchlistTag.toLowerCase())) return false;
    }

    // Search Query filter
    if (searchQuery) {
      const text = `${item.title} ${item.content} ${item.source}`.toLowerCase();
      if (!text.includes(searchQuery)) return false;
    }

    return true;
  });

  if (filtered.length === 0) {
    container.innerHTML = `
      <div class="news-card" style="text-align:center; padding:40px; color:var(--text-muted);">
        <i data-lucide="search-x" style="font-size:32px; margin-bottom:10px; display:block;"></i>
        找不到符合篩選條件的財經新聞與情報
      </div>
    `;
    lucide.createIcons();
    return;
  }

  container.innerHTML = filtered.map(item => {
    const sentimentPill = item.sentiment === "BULLISH" 
      ? `<span class="sentiment-badge bullish">📈 利多</span>`
      : item.sentiment === "BEARISH"
      ? `<span class="sentiment-badge bearish">📉 利空</span>`
      : `<span class="sentiment-badge neutral">⚖️ 中立</span>`;

    const impactPill = item.impact === "HIGH" 
      ? `<span class="pill-impact HIGH">🔴 高影響力</span>`
      : `<span class="pill-impact">🟡 中影響力</span>`;

    const bullets = (item.ai_summary || []).map(b => `
      <div class="bullet-item">${b}</div>
    `).join("");

    return `
      <article class="news-card">
        <div class="news-meta-row">
          <div class="news-source-time">
            <span style="font-weight:700; color:var(--spidey-cyan);">${item.source}</span>
            <span>•</span>
            <span>${item.pubDate}</span>
          </div>
          <div class="news-tags">
            <span class="pill-cat">${item.category}</span>
            ${impactPill}
            ${sentimentPill}
          </div>
        </div>

        <a href="${item.link}" target="_blank" class="news-title-link">
          ${item.title}
        </a>

        <div class="ai-bullets">
          ${bullets}
        </div>
      </article>
    `;
  }).join("");

  lucide.createIcons();
}

/* Export Modal Logic */
let currentFormat = "markdown";

function openExportModal() {
  document.getElementById("export-modal").classList.add("active");
  fetchExportFormat("markdown");
}

function closeExportModal() {
  document.getElementById("export-modal").classList.remove("active");
}

function switchExportFormat(e, format) {
  document.querySelectorAll("#export-modal .category-tabs .tab-btn").forEach(b => b.classList.remove("active"));
  e.target.classList.add("active");
  currentFormat = format;
  fetchExportFormat(format);
}

async function fetchExportFormat(format) {
  const codeBox = document.getElementById("export-code-content");
  codeBox.innerText = "生成格式中...";
  try {
    const res = await fetch("/api/export", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ format: format })
    }).then(r => r.json());

    if (res.status === "success") {
      codeBox.innerText = res.content;
    }
  } catch (err) {
    codeBox.innerText = "無法生成推播內容";
  }
}

function copyExportContent() {
  const content = document.getElementById("export-code-content").innerText;
  navigator.clipboard.writeText(content).then(() => {
    const copyBtn = document.getElementById("copy-export-btn");
    const origText = copyBtn.innerHTML;
    copyBtn.innerHTML = `✓ 已複製至剪貼簿！`;
    setTimeout(() => {
      copyBtn.innerHTML = origText;
    }, 2000);
  });
}
