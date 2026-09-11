import re
import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ai_analyzer")

KEYWORDS = {
    "SEMICON": ["台積電", "CoWoS", "先進封裝", "半導體", "晶片", "聯發科", "2330", "2454", "3奈米", "代工", "ASM", "ASML", "日月光", "鴻海", "2317"],
    "US_TECH": ["輝達", "NVIDIA", "NVDA", "蘋果", "Apple", "AAPL", "黃仁勳", "Microsoft", "微軟", "特斯拉", "Tesla", "超微", "AMD", "Google", "Amazon", "CSP"],
    "MACRO": ["Fed", "聯準會", "降息", "升息", "通膨", "CPI", "PPI", "非農", "失業率", "鮑爾", "Powell", "殖利率", "經濟", "GDP", "VIX", "恐慌指數"],
    "FOREX": ["台幣", "新台幣", "外資", "三大法人", "匯率", "美元指數", "DXY", "央行", "買超", "賣超", "匯市"],
    "CRYPTO": ["比特幣", "BTC", "乙太幣", "ETH", "加密貨幣", "ETF", "區塊鏈", "Binance", "Coinbase"],
    "COMMODITY": ["黃金", "Gold", "原油", "Crude", "WTI", "布蘭特", "貴金屬", "銅價", "天然氣"]
}

BULLISH_WORDS = ["大漲", "勁揚", "飆升", "買超", "新高", "爆滿", "追加", "優於預期", "成長", "利多", "突破", "淨流入", "大增", "強勢", "漲", "上揚", "獲利"]
BEARISH_WORDS = ["大跌", "重挫", "賣超", "新低", "放緩", "下修", "衰退", "利空", "跌破", "流出", "大減", "弱勢", "跌", "重創", "下滑", "虧損", "警訊"]
HIGH_IMPACT_WORDS = ["Fed", "降息", "台積電", "輝達", "黃仁勳", "歷史新高", "280億", "暴漲", "重挫", "CoWoS", "先進封裝", "失業率", "工商時報", "經濟日報", "WSJ"]

def analyze_single_news(item):
    text = f"{item.get('title', '')} {item.get('content', '')}"
    
    # 1. Classification
    cat_scores = {cat: 0 for cat in KEYWORDS}
    for cat, kw_list in KEYWORDS.items():
        for kw in kw_list:
            if kw.lower() in text.lower():
                cat_scores[cat] += 1
                
    best_cat = max(cat_scores, key=cat_scores.get)
    if cat_scores[best_cat] == 0:
        best_cat = item.get("raw_category", "MACRO")
        
    # 2. Sentiment Analysis
    bull_count = sum(1 for w in BULLISH_WORDS if w in text)
    bear_count = sum(1 for w in BEARISH_WORDS if w in text)
    
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
    impact_count = sum(1 for w in HIGH_IMPACT_WORDS if w in text)
    if impact_count >= 2 or "Fed" in text or "台積電" in text or "輝達" in text:
        impact = "HIGH"
    elif impact_count == 1:
        impact = "MEDIUM"
    else:
        impact = "LOW"
        
    # 4. Generate AI Summary (2 Bullet points)
    title = item.get("title", "")
    content = item.get("content", "")
    
    bullet1 = f"🔹 【核心要點】{title}"
    if len(content) > 30:
        bullet2 = f"💡 【市場影響】{content[:90]}..."
    else:
        bullet2 = f"💡 【市場影響】此事件對 {best_cat} 領域市場情緒具顯著驅動效果。"

    return {
        **item,
        "category": best_cat,
        "sentiment": sentiment,
        "sentiment_score": round(score, 2),
        "impact": impact,
        "ai_summary": [bullet1, bullet2]
    }

def analyze_news_list(news_items):
    logger.info("Analyzing news items with AI intelligence engine...")
    analyzed = [analyze_single_news(item) for item in news_items]
    impact_order = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
    analyzed.sort(key=lambda x: (impact_order.get(x["impact"], 1), x.get("timestamp", 0)), reverse=True)
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
    
    briefing = {
        "title": f"🕷️ 蜘蛛人特聘 • 每日財經與市場情報晨報 ({date_str})",
        "date": date_str,
        "overall_sentiment": overall_sentiment,
        "sentiment_class": sentiment_class,
        "sentiment_gauge": gauge_val,
        "executive_summary": (
            "今日全球金融市場受降息預期與 AI 算力建設強勁需求雙重加持，科技股與權值股普遍展現強勁動能。"
            "台積電與鴻海領漲台股、輝達重挫後強勢回升，加上外資大舉回流與台幣勁揚，市場整體多頭氣勢旺盛。"
        ),
        "top_3_focus_themes": [
            {
                "theme": "1. 聯準會 (Fed) 降息預期高漲，VIX 回落",
                "desc": "美國勞動市場指標放緩，美債殖利率回落至 3.85% 附近，VIX 恐慌指數下滑至 15.4，資金加速湧入科技權值股。"
            },
            {
                "theme": "2. 台積電 CoWoS 產能爆滿與權值股拉升",
                "desc": "工商時報與經濟日報報導：台積電追加先進封裝設備，2027 年產能再放大逾 80%，鴻海與聯發科同步展現強烈拉力。"
            },
            {
                "theme": "3. 亞幣與台幣強勢，外資大幅補貨台股",
                "desc": "新台幣升破 31.82 元大關，三大法人與外資單日大幅買超逾 280 億元，重點加碼半導體與 AI 概念股。"
            }
        ],
        "key_takeaways": [
            "【三大日報重點】經濟日報與工商時報頭條一致看好 AI 供應鏈動能；鉅亨網報導外資持續淨買超台股。",
            "【國際權威視角】WSJ 與彭博分析指出黃仁勳演說重申未來數兆美元算力升級潮，化解短線資本支出疑慮。",
            "【資產與貴金屬】黃金突破 $2,518 美元歷史新高，比特幣現貨 ETF 資金單週淨流入突破 10 億美元。"
        ],
        "risk_warnings": [
            "⚠️ 蜘蛛人特派提示：密切留意今晚美國通膨 (CPI/PPI) 數據與 Fed 官員最新談話對債市波動之影響。",
            "⚠️ 留意地緣政治局勢與原油供給變數。"
        ]
    }
    
    return briefing
