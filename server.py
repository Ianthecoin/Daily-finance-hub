import http.server
import socketserver
import json
import os
import urllib.parse
import threading
import time
import logging

from services.market_fetcher import fetch_all_market_data
from services.rss_fetcher import fetch_all_rss_news
from services.ai_analyzer import analyze_news_list, generate_executive_briefing

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("server")

PORT = 8080
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

# In-memory store
DATA_CACHE = {
    "market": [],
    "news": [],
    "briefing": {},
    "watchlist": ["工商時報", "台積電", "Fed 降息", "輝達", "鴻海", "VIX"],
    "last_updated": ""
}

def refresh_all_data():
    logger.info("--- Refreshing all market intelligence data ---")
    market = fetch_all_market_data()
    raw_news = fetch_all_rss_news()
    analyzed_news = analyze_news_list(raw_news)
    briefing = generate_executive_briefing(analyzed_news, market)
    
    DATA_CACHE["market"] = market
    DATA_CACHE["news"] = analyzed_news
    DATA_CACHE["briefing"] = briefing
    DATA_CACHE["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
    logger.info("--- Data refresh completed ---")

# Initial data load
refresh_all_data()

class FinanceHubHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path

        if path == "/":
            self.path = "/index.html"
            return super().do_GET()

        if path == "/api/market":
            self.send_json_response({"status": "success", "data": DATA_CACHE["market"], "last_updated": DATA_CACHE["last_updated"]})
            return

        if path == "/api/news":
            # Optional category query
            query = urllib.parse.parse_qs(parsed_path.query)
            cat = query.get("category", [None])[0]
            news_list = DATA_CACHE["news"]
            if cat and cat != "ALL":
                news_list = [n for n in news_list if n.get("category") == cat]
            self.send_json_response({"status": "success", "count": len(news_list), "data": news_list, "last_updated": DATA_CACHE["last_updated"]})
            return

        if path == "/api/briefing":
            self.send_json_response({"status": "success", "data": DATA_CACHE["briefing"], "last_updated": DATA_CACHE["last_updated"]})
            return

        if path == "/api/watchlist":
            self.send_json_response({"status": "success", "data": DATA_CACHE["watchlist"]})
            return

        # Serve static files
        return super().do_GET()

    def do_POST(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path

        content_length = int(self.headers.get("Content-Length", 0))
        body_bytes = self.rfile.read(content_length) if content_length > 0 else b""
        body_json = {}
        if body_bytes:
            try:
                body_json = json.loads(body_bytes.decode("utf-8"))
            except Exception:
                pass

        if path == "/api/refresh":
            refresh_all_data()
            self.send_json_response({"status": "success", "message": "資料重新抓取與分析完成", "last_updated": DATA_CACHE["last_updated"]})
            return

        if path == "/api/watchlist":
            keywords = body_json.get("keywords", [])
            if isinstance(keywords, list):
                DATA_CACHE["watchlist"] = keywords
            self.send_json_response({"status": "success", "data": DATA_CACHE["watchlist"]})
            return

        if path == "/api/export":
            export_type = body_json.get("format", "markdown")
            content = self.generate_export_format(export_type)
            self.send_json_response({"status": "success", "format": export_type, "content": content})
            return

        self.send_error(404, "Endpoint Not Found")

    def generate_export_format(self, export_type):
        briefing = DATA_CACHE["briefing"]
        news = DATA_CACHE["news"][:5]
        date_str = briefing.get("date", "")

        if export_type == "telegram":
            msg = f"📊 *【每日財經晨報】* ({date_str})\n"
            msg += f"🔥 *市場情緒*：{briefing.get('overall_sentiment', '')}\n\n"
            msg += f"📝 *摘要速覽*：\n{briefing.get('executive_summary', '')}\n\n"
            msg += "📌 *三大核心議題*：\n"
            for t in briefing.get("top_3_focus_themes", []):
                msg += f"• *{t['theme']}*\n  _{t['desc']}_\n"
            msg += "\n⚡ *重點新聞快訊*：\n"
            for n in news:
                icon = "📈" if n["sentiment"] == "BULLISH" else ("📉" if n["sentiment"] == "BEARISH" else "⚖️")
                msg += f"{icon} [{n['title']}]({n['link']})\n"
            return msg

        if export_type == "line":
            msg = f"🟢【每日財經晨報】({date_str})\n"
            msg += f"情緒：{briefing.get('overall_sentiment', '')}\n\n"
            msg += f"重點簡述：\n{briefing.get('executive_summary', '')}\n\n"
            msg += "三大焦點：\n"
            for t in briefing.get("top_3_focus_themes", []):
                msg += f"▸ {t['theme']}\n"
            msg += "\n熱門焦點：\n"
            for n in news:
                msg += f"・{n['title']}\n"
            return msg

        # Default Markdown
        md = f"# 📊 每日財經與市場情報晨報 ({date_str})\n\n"
        md += f"**整體市場情緒**：`{briefing.get('overall_sentiment', '')}` (指標分數: {briefing.get('sentiment_gauge', 50)}/100)\n\n"
        md += f"## 💡 執行摘要\n{briefing.get('executive_summary', '')}\n\n"
        md += "## 🔥 當日三大焦點議題\n"
        for t in briefing.get("top_3_focus_themes", []):
            md += f"### {t['theme']}\n{t['desc']}\n\n"
        md += "## ⚡ 高影響力財經新聞與 AI 摘要\n"
        for n in news:
            icon = "🟢 利多" if n["sentiment"] == "BULLISH" else ("🔴 利空" if n["sentiment"] == "BEARISH" else "⚪ 中立")
            md += f"### [{n['title']}]({n['link']}) ({icon})\n"
            md += f"- **來源**：{n['source']} | **時間**：{n['pubDate']}\n"
            for sum_line in n.get("ai_summary", []):
                md += f"- {sum_line}\n"
            md += "\n"
        return md

    def send_json_response(self, data_dict):
        content = json.dumps(data_dict, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

def start_background_scheduler(interval_seconds=900):
    def scheduler_loop():
        while True:
            time.sleep(interval_seconds)
            try:
                logger.info("Executing scheduled background auto-refresh...")
                refresh_all_data()
            except Exception as e:
                logger.error(f"Error in background auto-refresh: {e}")
                
    t = threading.Thread(target=scheduler_loop, daemon=True)
    t.start()
    logger.info(f"Background auto-refresh scheduler started (Interval: {interval_seconds}s)")

def run_server():
    start_background_scheduler(900)  # Auto refresh every 15 mins
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), FinanceHubHandler) as httpd:
        logger.info(f"Server starting on http://localhost:{PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    run_server()

