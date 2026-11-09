import re
import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ai_analyzer")

KEYWORDS = {
    "CRYPTO": ["SEC", "Gensler", "CFTC", "律動", "BlockBeats", "theblockbeats", "CoinDesk", "Cointelegraph", "Decrypt", "比特幣", "BTC", "乙太幣", "ETH", "加密貨幣", "加密資產", "ETF", "區塊鏈", "Binance", "Coinbase", "Solana", "SOL", "監管", "主席", "訴訟", "Kalshi"],
    "SEMICON": ["台積電", "CoWoS", "先進封裝", "半導體", "晶片", "聯發科", "2330", "2454", "3奈米", "代工", "ASM", "ASML", "日月光", "鴻海", "2317", "BigGo", "BigGo財經"],
    "US_TECH": ["輝達", "NVIDIA", "NVDA", "蘋果", "Apple", "AAPL", "黃仁勳", "Microsoft", "微軟", "特斯拉", "Tesla", "超微", "AMD", "Google", "Amazon", "CSP"],
    "MACRO": ["Fed", "聯準會", "降息", "升息", "通膨", "CPI", "PPI", "非農", "失業率", "鮑爾", "Powell", "殖利率", "經濟", "GDP", "VIX", "恐慌指數"],
    "FOREX": ["台幣", "新台幣", "外資", "三大法人", "匯率", "美元指數", "DXY", "央行", "買超", "賣超", "匯市"],
    "COMMODITY": ["黃金", "Gold", "原油", "Crude", "WTI", "布蘭特", "貴金屬", "銅價", "天然氣"]
}

BULLISH_WORDS = ["大漲", "勁揚", "飆升", "買超", "新高", "爆滿", "追加", "優於預期", "成長", "利多", "突破", "淨流入", "大增", "強勢", "漲", "上揚", "獲利", "dropped", "gain", "soar", "surge", "surge", "approval", "bull"]
BEARISH_WORDS = ["大跌", "重挫", "賣超", "新低", "放緩", "下修", "衰退", "利空", "跌破", "流出", "大減", "弱勢", "跌", "重創", "下滑", "虧損", "警訊", "drop", "plunge", "sued", "crackdown", "bear"]
HIGH_IMPACT_WORDS = ["SEC", "Gensler", "Fed", "降息", "台積電", "輝達", "黃仁勳", "歷史新高", "280億", "暴漲", "重挫", "CoWoS", "先進封裝", "失業率", "工商時報", "經濟日報", "WSJ", "CoinDesk", "Cointelegraph", "律動", "BlockBeats", "BigGo"]

# Simple translation helper dictionary for common crypto & SEC phrases
TRANSLATION_DICT = {
    "ex-sec acting chair": "前 SEC 代理主席",
    "agency dropped crypto cases": "監管機構撤銷加密貨幣訴訟",
    "to avoid issues with credibility": "以維護公信力與司法誠信",
    "sec": "美國證券交易委員會 (SEC)",
    "cftc": "美國商品期貨交易委員會 (CFTC)",
    "bitcoin": "比特幣 (Bitcoin)",
    "ethereum": "以太坊 (Ethereum)",
    "etf": "現貨 ETF",
    "fed": "美聯準會 (Fed)",
    "crypto": "加密資產/區塊鏈",
    "court": "法院",
    "judge": "法官",
    "approval": "核准通過",
    "lawsuit": "法律訴訟"
}

def translate_english_crypto_title(title):
    if not title:
        return ""
    # If title is mostly ASCII English
    if sum(1 for c in title if ord(c) < 128) > len(title) * 0.6:
        translated_parts = []
        lower_t = title.lower()
        
        # Build contextual Chinese subtitle
        context = ""
        if "sec" in lower_t:
            context += "【SEC 監管動態】"
        elif "cftc" in lower_t:
            context += "【CFTC 期貨監管】"
        elif "bitcoin" in lower_t or "btc" in lower_t:
            context += "【比特幣焦點】"
        elif "etf" in lower_t:
            context += "【ETF 資金流向】"
        else:
            context += "【全球加密頭條】"
            
        # Match keywords for translation
        matched_meaning = title
        if "dropped" in lower_t and "crypto" in lower_t:
            matched_meaning = "美 SEC 傳出撤銷部分加密貨幣執法訴訟，市場監管放鬆預期升溫"
        elif "kalshi" in lower_t:
            matched_meaning = "預測市場 Kalshi 監管爭議引發美議員與法院高度關注"
        elif "approval" in lower_t:
            matched_meaning = "最新監管文件釋出利多批准訊號"
        elif "dead" in lower_t or "found" in lower_t:
            matched_meaning = "區塊鏈風險投資界引發重大關注事件"

        return f"{context} {matched_meaning} ({title})"
    return title

def analyze_single_news(item):
    text = f"{item.get('title', '')} {item.get('content', '')}"
    
    # 1. Classification
    cat_scores = {cat: 0 for cat in KEYWORDS}
    raw_cat = item.get("raw_category")
    if raw_cat in cat_scores:
        cat_scores[raw_cat] += 3

    for cat, kw_list in KEYWORDS.items():
        for kw in kw_list:
            if kw.lower() in text.lower():
                cat_scores[cat] += 1
                
    best_cat = max(cat_scores, key=cat_scores.get)
    if cat_scores[best_cat] == 0:
        best_cat = item.get("raw_category", "MACRO")
        
    # 2. Sentiment Analysis
    bull_count = sum(1 for w in BULLISH_WORDS if w.lower() in text.lower())
    bear_count = sum(1 for w in BEARISH_WORDS if w.lower() in text.lower())
    
    if bull_count > bear_count:
        sentiment = "BULLISH"
        score = min(0.9, 0.4 + (bull_count - bear_count) * 0.15)
    elif bear_count > bull_count:
        sentiment = "BEARISH"
        score = max(-0.9, -0.4 - (bear_count - bull_count) * 0.15)
    else:
        sentiment = "NEUTRAL"
        score = 0.0

    # 3. Impact Rating
    impact_count = sum(1 for w in HIGH_IMPACT_WORDS if w.lower() in text.lower())
    if impact_count >= 2 or "SEC" in text or "Fed" in text or "台積電" in text or "輝達" in text:
        impact = "HIGH"
    elif impact_count == 1:
        impact = "MEDIUM"
    else:
        impact = "LOW"
        
    # 4. Generate AI Title & Summary (3-Tier Professional Analysis)
    raw_title = item.get("title", "")
    display_title = translate_english_crypto_title(raw_title)
    content = item.get("content", "")
    
    bullet1 = f"🔹 【事實摘要】{display_title[:80]}"
    if len(content) > 30:
        bullet2 = f"💡 【市場影響】{content[:95]}..."
    else:
        bullet2 = f"💡 【市場影響】此事件對 {best_cat} 領域與機構資金布局具顯著驅動效果。"
    bullet3 = f"🎯 【後續關注】持續追蹤美 SEC 官方合規公告、機構持倉變動與籌碼進出。"

    return {
        **item,
        "title": display_title,
        "raw_title": raw_title,
        "category": best_cat,
        "sentiment": sentiment,
        "sentiment_score": round(score, 2),
        "impact": impact,
        "ai_summary": [bullet1, bullet2, bullet3]
    }

def analyze_news_list(news_items):
    logger.info("Analyzing news items with AI intelligence engine...")
    analyzed = [analyze_single_news(item) for item in news_items]
    impact_order = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
    # Strictly sort by real-time timestamp descending (newest first)
    analyzed.sort(key=lambda x: (x.get("timestamp", 0), impact_order.get(x.get("impact"), 1)), reverse=True)
    return analyzed

def generate_executive_briefing(analyzed_news, market_data):
    logger.info("Synthesizing Executive Morning Briefing...")
    
    scores = [n["sentiment_score"] for n in analyzed_news]
    avg_score = (sum(scores) / len(scores)) if scores else 0.2
    gauge_val = int(50 + (avg_score * 40))
    
    if gauge_val >= 75:
        overall_sentiment = "樂觀偏多 (Bullish Sentiment)"
        sentiment_class = "bullish"
    elif gauge_val >= 55:
        overall_sentiment = "溫和偏多 (Moderately Bullish)"
        sentiment_class = "bullish"
    elif gauge_val >= 45:
        overall_sentiment = "中性觀望 (Neutral / Sideways)"
        sentiment_class = "neutral"
    else:
        overall_sentiment = "謹慎避險 (Cautious / Risk-Off)"
        sentiment_class = "bearish"
        
    date_str = datetime.datetime.now().strftime("%Y 年 %m 月 %d 日")
    
    # Extract live market highlights for cross-linking
    m_dict = {m.get("symbol"): m for m in (market_data or [])}
    btc_m = m_dict.get("BTC", {})
    tsmc_m = m_dict.get("2330.TW", {})
    nvda_m = m_dict.get("NVDA", {})
    
    # Dynamically extract top event titles to bind events to daily market swings
    top_news = analyzed_news[:3] if analyzed_news else []
    headline_summaries = []
    for n in top_news:
        t = n.get("raw_title") or n.get("title") or ""
        t_clean = re.sub(r"^[【\[].*?[】\]]\s*", "", t).strip()
        if t_clean:
            headline_summaries.append(t_clean[:40])
            
    summary_connector = "、".join(headline_summaries[:2]) if headline_summaries else "市場最新熱門事件與監管消息"
    
    btc_info = f"比特幣 {btc_m.get('price_str', '$--')} ({btc_m.get('change_str', '持平')})" if btc_m else "加密貨幣大盤"
    tsmc_info = f"台積電 {tsmc_m.get('price_str', '$--')} ({tsmc_m.get('change_str', '持平')})" if tsmc_m else "台股權值"
    nvda_info = f"輝達 {nvda_m.get('price_str', '$--')} ({nvda_m.get('change_str', '持平')})" if nvda_m else "美股 AI 巨頭"
    
    exec_summary = (
        f"【重點整理】今日市場聚焦於「{summary_connector}」等即時消息動態。"
        f"即時行情連動反應：{btc_info}、{tsmc_info}、{nvda_info}。"
        f"外資與機構資金正密切評估重大事件對後續各族群籌碼面與總體流動性之實質牽動。"
    )
    
    # Synthesize Category Focus Themes
    crypto_news = next((n for n in analyzed_news if n.get("category") == "CRYPTO"), None)
    tech_news = next((n for n in analyzed_news if n.get("category") in ("SEMICON", "US_TECH")), None)
    macro_news = next((n for n in analyzed_news if n.get("category") == "MACRO"), None)
    
    crypto_desc = (crypto_news.get("title", "") + " — " + crypto_news.get("content", "")[:60]) if crypto_news else "美 SEC 與 CFTC 對加密資產政策與合規指引持續明朗化，機構現貨 ETF 資金流向牽動幣價表現。"
    tech_desc = (tech_news.get("title", "") + " — " + tech_news.get("content", "")[:60]) if tech_news else "全球 AI 算力供應鏈與半導體先進製程（CoWoS）需求熱絡，科技權值股高檔震盪牽動大盤。"
    macro_desc = (macro_news.get("title", "") + " — " + macro_news.get("content", "")[:60]) if macro_news else "美聯準會 (Fed) 利率路徑與通膨就業數據公布，美債殖利率與美元指數震盪左右全球資金風向。"

    briefing = {
        "title": f"🕷️ 蜘蛛感應 • 全球財經與加密監管情報晨報 ({date_str})",
        "date": date_str,
        "overall_sentiment": overall_sentiment,
        "sentiment_class": sentiment_class,
        "sentiment_gauge": gauge_val,
        "executive_summary": exec_summary,
        "top_3_focus_themes": [
            {
                "theme": "1. 🪙 加密資產與現貨 ETF / 監管動向",
                "desc": crypto_desc
            },
            {
                "theme": "2. 💻 AI 算力供應鏈與半導體權值",
                "desc": tech_desc
            },
            {
                "theme": "3. 🏛️ 美聯準會 (Fed) 政策風向與總體經濟",
                "desc": macro_desc
            }
        ],
        "key_takeaways": [
            "【即時事件連動】當日熱門新聞與突發話題直接反映於盤面波動，宜嚴控風險與倉位。",
            "【機構資金流向】現貨 ETF 與三大法人資金偏好明確，具基本面支撐之強勢族群相對抗跌。",
            "【流動性與政策】留意各國監管裁決與央行利率決策公布前後之波動加劇機會。"
        ],
        "risk_warnings": [
            "⚠️ 風險提示：密切關注當日最新市場事件進展、財報外電與美聯準會官員談話。",
            "⚠️ 提醒投資人留意短期高槓桿與追高回調風險，嚴格執行個人風險管理與停損策略。"
        ]
    }
    
    return briefing
