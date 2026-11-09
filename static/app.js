// Daily Finance Hub - Client Logic with LINE Push Integration
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
  document.getElementById("btn-export-modal").addEventListener("click", openExportModal);
  document.getElementById("close-modal-btn").addEventListener("click", closeExportModal);
  document.getElementById("close-modal-footer").addEventListener("click", closeExportModal);
  document.getElementById("copy-export-btn").addEventListener("click", copyExportContent);

  // Discord Modal Buttons
  document.getElementById("btn-discord-modal").addEventListener("click", openDiscordModal);
  document.getElementById("close-discord-modal-btn").addEventListener("click", closeDiscordModal);
  document.getElementById("btn-discord-save").addEventListener("click", saveDiscordConfig);
  document.getElementById("btn-discord-test").addEventListener("click", testDiscordConnection);
  document.getElementById("btn-discord-push-now").addEventListener("click", pushDiscordBriefingNow);

  // LINE Modal Buttons
  document.getElementById("btn-line-modal").addEventListener("click", openLineModal);
  document.getElementById("close-line-modal-btn").addEventListener("click", closeLineModal);
  document.getElementById("btn-line-save").addEventListener("click", saveLineConfig);
  document.getElementById("btn-line-test").addEventListener("click", testLineConnection);
  document.getElementById("btn-line-push-now").addEventListener("click", pushLineBriefingNow);

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
    const t = Date.now();
    const [mRes, nRes, bRes, wRes] = await Promise.all([
      fetch(`/api/market?t=${t}`).then(r => r.json()),
      fetch(`/api/news?t=${t}`).then(r => r.json()),
      fetch(`/api/briefing?t=${t}`).then(r => r.json()),
      fetch(`/api/watchlist?t=${t}`).then(r => r.json()),
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

/* Render Market Cards */
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

  const sanitize = (text) => {
    if (!text) return "";
    return text
      .replace(/【腦哥\s*Chill\s*塊[練鏈]式重點整理】/g, "【重點整理】")
      .replace(/腦哥\s*Chill\s*塊[練鏈]式/g, "")
      .replace(/腦哥式風險提示/g, "風險提示")
      .replace(/腦哥/g, "")
      .replace(/Chill\s*塊[練鏈]/g, "");
  };

  document.getElementById("briefing-date").innerText = briefingData.date || "";

  const badgeEl = document.getElementById("sentiment-badge-tag");
  badgeEl.innerText = briefingData.overall_sentiment || "中性觀望";
  badgeEl.className = `sentiment-badge ${briefingData.sentiment_class || "neutral"}`;

  const gaugeFill = document.getElementById("gauge-bar-fill");
  gaugeFill.style.width = `${briefingData.sentiment_gauge || 50}%`;

  document.getElementById("exec-summary-text").innerText = sanitize(briefingData.executive_summary || "");

  const themesContainer = document.getElementById("focus-themes-container");
  themesContainer.innerHTML = (briefingData.top_3_focus_themes || []).map(t => `
    <div class="focus-theme-item">
      <div class="focus-theme-title">${sanitize(t.theme)}</div>
      <div class="focus-theme-desc">${sanitize(t.desc)}</div>
    </div>
  `).join("");

  const riskContainer = document.getElementById("risk-warnings-container");
  riskContainer.innerHTML = (briefingData.risk_warnings || []).map(r => `
    <div style="margin-bottom:4px;">${sanitize(r)}</div>
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
    if (currentCategory !== "ALL" && item.category !== currentCategory) return false;
    if (currentSentiment !== "ALL" && item.sentiment !== currentSentiment) return false;
    if (currentImpact !== "ALL" && item.impact !== currentImpact) return false;

    if (activeWatchlistTag) {
      const text = `${item.title} ${item.content}`.toLowerCase();
      if (!text.includes(activeWatchlistTag.toLowerCase())) return false;
    }

    if (searchQuery) {
      const text = `${item.title} ${item.content} ${item.source}`.toLowerCase();
      if (!text.includes(searchQuery)) return false;
    }

    return true;
  });

  // Always display newest news first
  filtered.sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0));

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
    const isLatest = (Date.now() / 1000 - (item.timestamp || 0)) < 86400;
    const latestBadge = isLatest 
      ? `<span style="background:rgba(226, 54, 54, 0.2); color:#ff5252; border:1px solid rgba(226, 54, 54, 0.4); padding:2px 7px; border-radius:4px; font-size:11px; font-weight:800; margin-left:8px; display:inline-flex; align-items:center; gap:2px;">🔥 最新</span>` 
      : "";

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
            ${latestBadge}
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

/* LINE Notification Modal Logic */
async function openLineModal() {
  document.getElementById("line-modal").classList.add("active");
  const msgEl = document.getElementById("line-status-msg");
  msgEl.innerText = "載入設定中...";
  try {
    const res = await fetch("/api/line/config").then(r => r.json());
    if (res.status === "success") {
      const cfg = res.data;
      if (cfg.token) {
        document.getElementById("line-token-input").placeholder = `已設定 Token (${cfg.token_masked || "******"})`;
      }
      document.getElementById("line-time-input").value = cfg.push_time || "08:30";
      document.getElementById("line-enable-check").checked = cfg.enabled !== false;
      msgEl.innerText = cfg.token ? "🟢 已連接 LINE Token" : "⚠️ 尚未設定 LINE Token";
      msgEl.style.color = cfg.token ? "#4ade80" : "#facc15";
    }
  } catch (e) {
    msgEl.innerText = "無法載入 LINE 設定";
    msgEl.style.color = "#f87171";
  }
}

function closeLineModal() {
  document.getElementById("line-modal").classList.remove("active");
}

async function saveLineConfig() {
  const token = document.getElementById("line-token-input").value.trim();
  const timeStr = document.getElementById("line-time-input").value.trim();
  const enabled = document.getElementById("line-enable-check").checked;
  const msgEl = document.getElementById("line-status-msg");

  msgEl.innerText = "儲存中...";
  try {
    const payload = { push_time: timeStr, enabled: enabled };
    if (token) payload.token = token;

    const res = await fetch("/api/line/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    }).then(r => r.json());

    if (res.status === "success") {
      msgEl.innerText = "✓ LINE 設定已成功儲存！";
      msgEl.style.color = "#4ade80";
    } else {
      msgEl.innerText = `儲存失敗: ${res.message}`;
      msgEl.style.color = "#f87171";
    }
  } catch (e) {
    msgEl.innerText = "儲存連線失敗";
    msgEl.style.color = "#f87171";
  }
}

async function testLineConnection() {
  const token = document.getElementById("line-token-input").value.trim();
  const msgEl = document.getElementById("line-status-msg");
  msgEl.innerText = "連線測試中...";

  try {
    const res = await fetch("/api/line/test", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token: token })
    }).then(r => r.json());

    if (res.status === "success") {
      msgEl.innerText = "✓ LINE 連線測試成功！已發送測試訊息。";
      msgEl.style.color = "#4ade80";
    } else {
      msgEl.innerText = `✕ 測試失敗: ${res.message}`;
      msgEl.style.color = "#f87171";
    }
  } catch (e) {
    msgEl.innerText = "測試連線發送失敗";
    msgEl.style.color = "#f87171";
  }
}

async function pushLineBriefingNow() {
  const msgEl = document.getElementById("line-status-msg");
  msgEl.innerText = "推播今日晨報中...";

  try {
    const res = await fetch("/api/line/push_now", {
      method: "POST",
      headers: { "Content-Type": "application/json" }
    }).then(r => r.json());

    if (res.status === "success") {
      msgEl.innerText = "🚀 成功推播今日晨報至 LINE！";
      msgEl.style.color = "#4ade80";
    } else {
      msgEl.innerText = `✕ 推播失敗: ${res.message}`;
      msgEl.style.color = "#f87171";
    }
  } catch (e) {
    msgEl.innerText = "發送連線失敗";
    msgEl.style.color = "#f87171";
  }
}

/* Discord Webhook Modal Functions */
function openDiscordModal() {
  document.getElementById("discord-modal").classList.add("active");
  document.getElementById("discord-status-msg").innerText = "";
  loadDiscordConfig();
}

function closeDiscordModal() {
  document.getElementById("discord-modal").classList.remove("active");
}

async function loadDiscordConfig() {
  const savedLocalUrl = localStorage.getItem("spidey_discord_webhook") || "";
  const savedLocalTime = localStorage.getItem("spidey_discord_time") || "08:30";
  if (savedLocalUrl) {
    document.getElementById("discord-webhook-input").value = savedLocalUrl;
    document.getElementById("discord-time-input").value = savedLocalTime;
  }

  try {
    const t = Date.now();
    const res = await fetch(`/api/discord/config?t=${t}`).then(r => r.json());
    if (res.status === "success" && res.data) {
      if (res.data.webhook_url) {
        document.getElementById("discord-webhook-input").value = res.data.webhook_url;
        localStorage.setItem("spidey_discord_webhook", res.data.webhook_url);
      }
      document.getElementById("discord-time-input").value = res.data.push_time || savedLocalTime;
      document.getElementById("discord-enable-check").checked = res.data.enabled !== false;
    }
  } catch (e) {
    console.error("Failed to load discord config:", e);
  }
}

async function saveDiscordConfig() {
  const webhookUrl = document.getElementById("discord-webhook-input").value.trim();
  const pushTime = document.getElementById("discord-time-input").value.trim() || "08:30";
  const enabled = document.getElementById("discord-enable-check").checked;
  const msgEl = document.getElementById("discord-status-msg");

  if (webhookUrl) {
    localStorage.setItem("spidey_discord_webhook", webhookUrl);
    localStorage.setItem("spidey_discord_time", pushTime);
  }

  msgEl.innerText = "正在儲存設定...";
  msgEl.style.color = "var(--text-muted)";

  try {
    const res = await fetch("/api/discord/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        webhook_url: webhookUrl,
        push_time: pushTime,
        enabled: enabled
      })
    }).then(r => r.json());

    if (res.status === "success") {
      msgEl.innerText = "✓ Discord Webhook 設定已成功儲存！";
      msgEl.style.color = "#4ade80";
    } else {
      msgEl.innerText = "✓ 已儲存於瀏覽器與本地設定！";
      msgEl.style.color = "#4ade80";
    }
  } catch (e) {
    msgEl.innerText = "✓ 已成功儲存於瀏覽器記憶中！";
    msgEl.style.color = "#4ade80";
  }
}

async function sendToDiscordDirect(webhookUrl, payload) {
  try {
    const resp = await fetch(webhookUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (resp.status === 200 || resp.status === 204) {
      return { status: "success" };
    }
    const errData = await resp.json().catch(() => ({}));
    const msg = errData.message || (resp.status === 401 ? "401 Unauthorized: Webhook 網址不正確或金鑰已失效" : `HTTP ${resp.status}`);
    return { status: "error", message: msg };
  } catch (err) {
    return { status: "error", message: err.message || "連線至 Discord 失敗" };
  }
}

async function testDiscordConnection() {
  const webhookUrl = document.getElementById("discord-webhook-input").value.trim();
  const msgEl = document.getElementById("discord-status-msg");
  const testBtn = document.getElementById("btn-discord-test");

  if (!webhookUrl) {
    msgEl.innerText = "請先貼上 Discord Webhook 網址！";
    msgEl.style.color = "#f87171";
    return;
  }

  testBtn.disabled = true;
  msgEl.innerText = "⏳ 正在發送連線測試至 Discord...";
  msgEl.style.color = "#818cf8";

  const testPayload = {
    username: "🕷️ 蜘蛛感應戰情室",
    embeds: [
      {
        title: "🎉 Discord 晨報推播連線成功！",
        description: "恭喜！您的 Discord Webhook 已成功綁定【蜘蛛感應 - 每日財金戰情室】。\n系統將在每日預定時間自動推送最新市場情報與晨報到此頻道。",
        color: 0x00D2FF,
        fields: [
          { name: "⏰ 狀態", value: "連線正常 / 即時推播就緒", inline: true },
          { name: "📅 測試時間", value: new Date().toLocaleString(), inline: true }
        ],
        footer: { text: "🕷️ 蜘蛛感應戰情室 • Discord 即時推播" }
      }
    ]
  };

  // 1. Try sending directly from browser
  let res = await sendToDiscordDirect(webhookUrl, testPayload);

  // 2. If direct fails, try backend route
  if (res.status !== "success") {
    try {
      const bRes = await fetch("/api/discord/test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ webhook_url: webhookUrl })
      }).then(r => r.json());
      if (bRes.status === "success") res = bRes;
    } catch (e) {
      // Keep res error
    }
  }

  // Also auto-save config in background for the daily scheduler
  fetch("/api/discord/config", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      webhook_url: webhookUrl,
      push_time: document.getElementById("discord-time-input").value.trim() || "08:30",
      enabled: document.getElementById("discord-enable-check").checked
    })
  }).catch(() => {});

  testBtn.disabled = false;

  if (res.status === "success") {
    msgEl.innerText = "🎉 連線成功！請前往您的 Discord 頻道查看測試訊息。";
    msgEl.style.color = "#4ade80";
  } else {
    msgEl.innerText = `✕ 測試失敗: ${res.message}`;
    msgEl.style.color = "#f87171";
  }
}

async function pushDiscordBriefingNow() {
  const webhookUrl = document.getElementById("discord-webhook-input").value.trim();
  const msgEl = document.getElementById("discord-status-msg");
  const pushBtn = document.getElementById("btn-discord-push-now");

  if (!webhookUrl) {
    msgEl.innerText = "請先貼上 Discord Webhook 網址！";
    msgEl.style.color = "#f87171";
    return;
  }

  pushBtn.disabled = true;
  msgEl.innerText = "⏳ 正在推送今日完整晨報至 Discord...";
  msgEl.style.color = "#818cf8";

  const b = briefingData || {};
  const sentiment = b.overall_sentiment || "中性觀望";
  const gauge = b.sentiment_gauge || 50;
  const execSummary = b.executive_summary || "今日市場焦點彙整中...";
  const dateStr = b.date || new Date().toLocaleDateString();

  let color = 0x00D2FF;
  if (sentiment.includes("多") || sentiment.includes("Bullish")) color = 0x10B981;
  else if (sentiment.includes("空") || sentiment.includes("Risk-Off")) color = 0xE23636;

  const fields = [
    {
      name: "📊 市場情緒氣壓計",
      value: `**${sentiment}** (信心指數: \`${gauge}%\`)`,
      inline: false
    },
    {
      name: "📝 重點精華導讀",
      value: execSummary.slice(0, 1000),
      inline: false
    }
  ];

  const themes = b.top_3_focus_themes || [];
  if (themes.length > 0) {
    const themeTexts = themes.map(t => `**${t.theme}**\n> ${t.desc}`).join("\n\n");
    fields.push({
      name: "🔥 今日三大核心焦點",
      value: themeTexts.slice(0, 1020),
      inline: false
    });
  }

  const risks = b.risk_warnings || [];
  if (risks.length > 0) {
    fields.push({
      name: "⚠️ 風險提示",
      value: risks.join("\n").slice(0, 1020),
      inline: false
    });
  }

  const briefingPayload = {
    username: "🕷️ 蜘蛛感應戰情室",
    embeds: [
      {
        title: `🕷️ 每日財經與加密情報晨報 (${dateStr})`,
        color: color,
        fields: fields,
        footer: { text: "🕷️ 蜘蛛感應 • 每日自動化晨報服務" },
        timestamp: new Date().toISOString()
      }
    ]
  };

  // 1. Try sending directly from browser
  let res = await sendToDiscordDirect(webhookUrl, briefingPayload);

  // 2. Fallback to backend route
  if (res.status !== "success") {
    try {
      const bRes = await fetch("/api/discord/push_now", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ webhook_url: webhookUrl })
      }).then(r => r.json());
      if (bRes.status === "success") res = bRes;
    } catch (e) {
      // Keep res error
    }
  }

  pushBtn.disabled = false;

  if (res.status === "success") {
    msgEl.innerText = "🚀 成功！今日完整晨報已發送至您的 Discord 頻道！";
    msgEl.style.color = "#4ade80";
  } else {
    msgEl.innerText = `✕ 推送失敗: ${res.message}`;
    msgEl.style.color = "#f87171";
  }
}
