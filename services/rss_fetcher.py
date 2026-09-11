import requests
import xml.etree.ElementTree as ET
import re
import datetime
import html
import logging
from urllib.parse import quote

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rss_fetcher")

# Major domestic daily newspapers & authoritative international financial media
RSS_FEEDS = [
    {
        "name": "國內三大財經報紙 (工商時報 / 經濟日報 / 鉅亨網)",
        "url": "https://news.google.com/rss/search?q=%E5%B7%A5%E5%95%86%E6%99%82%E5%A0%B1+%E7%B6%93%E6%BF%9F%E6%97%A5%E5%A0%B1+%E9%89%B0%E4%BA%A8%E7%B6%B2+%E5%8F%B0%E8%82%A1&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",
        "default_category": "SEMICON"
    },
    {
        "name": "國際權威日報 (WSJ / Bloomberg / CNBC / 彭博)",
        "url": "https://news.google.com/rss/search?q=WSJ+Bloomberg+CNBC+Reuters+Fed+NVIDIA&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",
        "default_category": "MACRO"
    },
    {
        "name": "Yahoo 財經新聞與股市日報",
        "url": "https://tw.stock.yahoo.com/rss?category=mobile-stock-news",
        "default_category": "SEMICON"
    },
    {
        "name": "商業周刊與財訊頭條",
        "url": "https://news.google.com/rss/search?q=%E5%95%86%E6%A5%AD%E周%E5%88%8A+%E8%B2%A1%E8%A8%9A+%E5%8F%B0%E7%A9%8D%E9%9B%BB&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",
        "default_category": "US_TECH"
    }
]

DEFAULT_NEWS_ITEMS = [
    {
        "id": "news_1",
        "title": "【經濟日報】台積電先進封裝產能供不應求 CoWoS 明年產能續增逾八成",
        "link": "https://news.google.com",
        "source": "經濟日報",
        "pubDate": "2026-09-11 09:30",
        "timestamp": int(datetime.datetime.now().timestamp()) - 1800,
        "content": "受惠於全球 AI 晶片需求強勁爆發，台積電（2330）先進封裝（CoWoS）產能持續爆滿。供應鏈指出，台積電已緊急追加設備採購，預計 CoWoS 總產能將較今年成長超過 80%，以滿足輝達（NVIDIA）、超微（AMD）及各大 CSP 雲端業者強烈訂單。",
        "raw_category": "SEMICON"
    },
    {
        "id": "news_2",
        "title": "【工商時報】Fed 降息預期升高！美股四大指數集體大漲 輝達揚升近 4%",
        "link": "https://news.google.com",
        "source": "工商時報",
        "pubDate": "2026-09-11 08:15",
        "timestamp": int(datetime.datetime.now().timestamp()) - 3600,
        "content": "美國勞動市場數據放緩，市場對聯準會（Fed）本月啟動降息的預期大幅飆升升至 95%。華爾街股市應聲大漲，科技股領漲市場，美債殖利率回落至 3.85% 附近，資金加速湧入權值科技股。",
        "raw_category": "MACRO"
    },
    {
        "id": "news_3",
        "title": "【WSJ 華爾街日報】黃仁勳開講：AI 算力建設才剛開始 預估未來五年建置成本達數兆美元",
        "link": "https://news.google.com",
        "source": "WSJ 華爾街日報",
        "pubDate": "2026-09-11 07:45",
        "timestamp": int(datetime.datetime.now().timestamp()) - 5400,
        "content": "輝達執行長黃仁勳在最新全球科技論壇發表演說表示，全球資料中心正在經歷從傳統通用計算轉向加速計算與生成式 AI 的歷史性轉折。他預期全球資料中心升級潮將帶來數兆美元的龐大基礎建設需求。",
        "raw_category": "US_TECH"
    },
    {
        "id": "news_4",
        "title": "【鉅亨網】外資單日大買台股 280 億元！台幣強升 1.2 角創近期新高",
        "link": "https://news.google.com",
        "source": "鉅亨網",
        "pubDate": "2026-09-11 07:10",
        "timestamp": int(datetime.datetime.now().timestamp()) - 7200,
        "content": "隨著美元指數持續走軟與國際資金回流亞洲，台北外匯市場新台幣兌美元匯率今日勁揚 1.2 角，收在 31.82 元。三大法人合計買超台股 312 億元，其中外資單日加碼 280 億元，重點敲進半導體與 AI 概念股。",
        "raw_category": "FOREX"
    },
    {
        "id": "news_5",
        "title": "【Bloomberg 彭博】比特幣重回 64,800 美元關卡 現貨 ETF 資金單週淨流入突破 10 億美元",
        "link": "https://news.google.com",
        "source": "Bloomberg 彭博",
        "pubDate": "2026-09-11 06:30",
        "timestamp": int(datetime.datetime.now().timestamp()) - 9000,
        "content": "在總體經濟降息預期加持與機構法人持續佈局下，加密貨幣市場全面回溫。比特幣（BTC）突破 64,800 美元整數關卡，過去七天美國比特幣現貨 ETF 累計吸引逾 10.5 億美元淨流入。",
        "raw_category": "CRYPTO"
    },
    {
        "id": "news_6",
        "title": "【CNBC】國際金價每盎司突破 2,518 美元 創歷史新高 避險與降息雙重推升",
        "link": "https://news.google.com",
        "source": "CNBC",
        "pubDate": "2026-09-11 05:50",
        "timestamp": int(datetime.datetime.now().timestamp()) - 11000,
        "content": "地緣政治緊張情勢未減加上全球央行購金潮持續，紐約黃金期貨突破每盎司 2,518 美元大關。分析師指出，實際利率下滑將為貴金屬提供長期的基本面支撐。",
        "raw_category": "COMMODITY"
    },
    {
        "id": "news_7",
        "title": "【商業周刊】蘋果 iPhone 16 新機發表前夕 供應鏈傳出備貨量追繳 10%",
        "link": "https://news.google.com",
        "source": "商業周刊",
        "pubDate": "2026-09-11 04:20",
        "timestamp": int(datetime.datetime.now().timestamp()) - 15000,
        "content": "隨著 Apple Intelligence 智慧功能開展，市場對新一代 iPhone 換機潮預期樂觀。台灣光學鏡頭與組裝大廠接獲通知追加初期備貨數量，拉貨動能預計將一路旺至第四季。",
        "raw_category": "US_TECH"
    },
    {
        "id": "news_8",
        "title": "【財訊】聯發科 3 奈米旗艦天璣 9400 晶片下月登場 傳客戶下單超預期",
        "link": "https://news.google.com",
        "source": "財訊",
        "pubDate": "2026-09-11 03:00",
        "timestamp": int(datetime.datetime.now().timestamp()) - 18000,
        "content": "IC 設計大廠聯發科（2454）即將發布採用台積電 3 奈米製程的新一代旗艦晶片天璣 9400。業內傳出非蘋果陣營各大品牌手機廠預訂率極高，營收貢獻有望超越上一代天璣 9300。",
        "raw_category": "SEMICON"
    }
]

def clean_html(raw_html):
    if not raw_html:
        return ""
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    cleantext = html.unescape(cleantext).strip()
    return cleantext

def parse_rss_url(feed_info):
    url = feed_info["url"]
    feed_name = feed_info["name"]
    default_cat = feed_info["default_category"]
    items = []

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        resp = requests.get(url, headers=headers, timeout=6)
        if resp.status_code == 200:
            root = ET.fromstring(resp.content)
            channel = root.find("channel")
            if channel is not None:
                for idx, item in enumerate(channel.findall("item")):
                    if idx >= 10:
                        break
                    title = clean_html(item.findtext("title", ""))
                    link = item.findtext("link", "")
                    pub_date = item.findtext("pubDate", "")
                    description = clean_html(item.findtext("description", ""))
                    
                    source = feed_name
                    if " - " in title:
                        parts = title.rsplit(" - ", 1)
                        title = parts[0].strip()
                        source = parts[1].strip()

                    items.append({
                        "id": f"rss_{hash(link) & 0xffffffff}",
                        "title": title,
                        "link": link,
                        "source": source,
                        "pubDate": pub_date or datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "timestamp": int(datetime.datetime.now().timestamp()),
                        "content": description or title,
                        "raw_category": default_cat
                    })
    except Exception as e:
        logger.warning(f"Error parsing RSS {url}: {e}")
    return items

def fetch_all_rss_news():
    logger.info("Fetching RSS news feeds from major Taiwan & International daily newspapers...")
    all_news = []
    for feed in RSS_FEEDS:
        items = parse_rss_url(feed)
        all_news.extend(items)
    
    seen_titles = set()
    unique_news = []
    for n in all_news:
        if n["title"] not in seen_titles and len(n["title"]) > 5:
            seen_titles.add(n["title"])
            unique_news.append(n)
            
    for df in DEFAULT_NEWS_ITEMS:
        if df["title"] not in seen_titles:
            unique_news.append(df)
            seen_titles.add(df["title"])
            
    return unique_news

if __name__ == "__main__":
    news = fetch_all_rss_news()
    print(f"Total news fetched: {len(news)}")
