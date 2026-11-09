import requests
import json
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("market_fetcher")

# Expanded Multi-Platform Financial Links (富果 Fugle, 籌碼K線 CMoney, TradingView, Yahoo 股市)
SYMBOLS = [
    {
        "symbol": "^TWII", "name": "台股加權指數", "category": "INDEX", "unit": "點",
        "detail_url": "https://tw.stock.yahoo.com/quote/^TWII", "source_label": "Yahoo股市",
        "platform_links": [
            {"label": "Yahoo股市", "url": "https://tw.stock.yahoo.com/quote/^TWII"},
            {"label": "TradingView", "url": "https://www.tradingview.com/symbols/TWII/"}
        ]
    },
    {
        "symbol": "2330.TW", "name": "台積電 (2330)", "category": "TW_STOCK", "unit": "元",
        "detail_url": "https://www.fugle.tw/ai/2330", "source_label": "富果 Fugle",
        "platform_links": [
            {"label": "🐤 富果 Fugle", "url": "https://www.fugle.tw/ai/2330"},
            {"label": "📊 籌碼K線", "url": "https://www.cmoney.tw/forum/stock/2330"},
            {"label": "📈 Yahoo股市", "url": "https://tw.stock.yahoo.com/quote/2330.TW"}
        ]
    },
    {
        "symbol": "2317.TW", "name": "鴻海 (2317)", "category": "TW_STOCK", "unit": "元",
        "detail_url": "https://www.fugle.tw/ai/2317", "source_label": "富果 Fugle",
        "platform_links": [
            {"label": "🐤 富果 Fugle", "url": "https://www.fugle.tw/ai/2317"},
            {"label": "📊 籌碼K線", "url": "https://www.cmoney.tw/forum/stock/2317"},
            {"label": "📈 Yahoo股市", "url": "https://tw.stock.yahoo.com/quote/2317.TW"}
        ]
    },
    {
        "symbol": "2454.TW", "name": "聯發科 (2454)", "category": "TW_STOCK", "unit": "元",
        "detail_url": "https://www.fugle.tw/ai/2454", "source_label": "富果 Fugle",
        "platform_links": [
            {"label": "🐤 富果 Fugle", "url": "https://www.fugle.tw/ai/2454"},
            {"label": "📊 籌碼K線", "url": "https://www.cmoney.tw/forum/stock/2454"},
            {"label": "📈 Yahoo股市", "url": "https://tw.stock.yahoo.com/quote/2454.TW"}
        ]
    },
    {
        "symbol": "NVDA", "name": "輝達 (NVDA)", "category": "US_STOCK", "unit": "美元",
        "detail_url": "https://www.tradingview.com/symbols/NASDAQ-NVDA/", "source_label": "TradingView",
        "platform_links": [
            {"label": "📈 TradingView", "url": "https://www.tradingview.com/symbols/NASDAQ-NVDA/"},
            {"label": "🐤 富果 Fugle", "url": "https://www.fugle.tw"},
            {"label": "📈 Yahoo Finance", "url": "https://finance.yahoo.com/quote/NVDA"}
        ]
    },
    {
        "symbol": "AAPL", "name": "蘋果 (AAPL)", "category": "US_STOCK", "unit": "美元",
        "detail_url": "https://www.tradingview.com/symbols/NASDAQ-AAPL/", "source_label": "TradingView",
        "platform_links": [
            {"label": "📈 TradingView", "url": "https://www.tradingview.com/symbols/NASDAQ-AAPL/"},
            {"label": "🐤 富果 Fugle", "url": "https://www.fugle.tw"},
            {"label": "📈 Yahoo Finance", "url": "https://finance.yahoo.com/quote/AAPL"}
        ]
    },
    {
        "symbol": "^GSPC", "name": "標普 500", "category": "INDEX", "unit": "點",
        "detail_url": "https://www.tradingview.com/symbols/SPX/", "source_label": "TradingView",
        "platform_links": [
            {"label": "TradingView", "url": "https://www.tradingview.com/symbols/SPX/"},
            {"label": "Yahoo", "url": "https://tw.stock.yahoo.com/quote/^GSPC"}
        ]
    },
    {
        "symbol": "^IXIC", "name": "那斯達克", "category": "INDEX", "unit": "點",
        "detail_url": "https://www.tradingview.com/symbols/IXIC/", "source_label": "TradingView",
        "platform_links": [
            {"label": "TradingView", "url": "https://www.tradingview.com/symbols/IXIC/"},
            {"label": "Yahoo", "url": "https://tw.stock.yahoo.com/quote/^IXIC"}
        ]
    },
    {
        "symbol": "^SOX", "name": "費城半導體", "category": "INDEX", "unit": "點",
        "detail_url": "https://www.tradingview.com/symbols/SOX/", "source_label": "TradingView",
        "platform_links": [
            {"label": "TradingView", "url": "https://www.tradingview.com/symbols/SOX/"},
            {"label": "Yahoo", "url": "https://tw.stock.yahoo.com/quote/^SOX"}
        ]
    },
    {
        "symbol": "^VIX", "name": "VIX 恐慌指數", "category": "MACRO", "unit": "點",
        "detail_url": "https://www.tradingview.com/symbols/VIX/", "source_label": "TradingView",
        "platform_links": [
            {"label": "TradingView", "url": "https://www.tradingview.com/symbols/VIX/"},
            {"label": "Yahoo", "url": "https://tw.stock.yahoo.com/quote/^VIX"}
        ]
    },
    {
        "symbol": "DX-Y.NYB", "name": "美元指數 (DXY)", "category": "FOREX", "unit": "點",
        "detail_url": "https://www.tradingview.com/symbols/DXY/", "source_label": "TradingView",
        "platform_links": [
            {"label": "TradingView", "url": "https://www.tradingview.com/symbols/DXY/"},
            {"label": "Yahoo", "url": "https://tw.stock.yahoo.com/quote/DX-Y.NYB"}
        ]
    },
    {
        "symbol": "TWD=X", "name": "美元/台幣", "category": "FOREX", "unit": "元",
        "detail_url": "https://www.tradingview.com/symbols/USDTWD/", "source_label": "TradingView",
        "platform_links": [
            {"label": "TradingView", "url": "https://www.tradingview.com/symbols/USDTWD/"},
            {"label": "Yahoo", "url": "https://tw.stock.yahoo.com/quote/TWD=X"}
        ]
    },
    {
        "symbol": "^TNX", "name": "美10年債殖利率", "category": "BOND", "unit": "%",
        "detail_url": "https://www.tradingview.com/symbols/US10Y/", "source_label": "TradingView",
        "platform_links": [
            {"label": "TradingView", "url": "https://www.tradingview.com/symbols/US10Y/"},
            {"label": "Yahoo", "url": "https://tw.stock.yahoo.com/quote/^TNX"}
        ]
    },
    {
        "symbol": "GC=F", "name": "紐約黃金期貨", "category": "COMMODITY", "unit": "美元",
        "detail_url": "https://www.tradingview.com/symbols/GOLD/", "source_label": "TradingView",
        "platform_links": [
            {"label": "TradingView", "url": "https://www.tradingview.com/symbols/GOLD/"},
            {"label": "Yahoo", "url": "https://tw.stock.yahoo.com/quote/GC=F"}
        ]
    },
    {
        "symbol": "BTC-USD", "name": "比特幣", "category": "CRYPTO", "unit": "美元",
        "detail_url": "https://www.tradingview.com/symbols/BTCUSD/", "source_label": "TradingView",
        "platform_links": [
            {"label": "TradingView", "url": "https://www.tradingview.com/symbols/BTCUSD/"},
            {"label": "Yahoo", "url": "https://tw.stock.yahoo.com/quote/BTC-USD"}
        ]
    }
]

DEFAULT_FALLBACK = SYMBOLS

def fetch_single_yahoo_symbol(target):
    symbol = target["symbol"]
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=2d"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            result = data["chart"]["result"][0]
            meta = result["meta"]
            price = meta.get("regularMarketPrice", 0.0)
            prev_close = meta.get("chartPreviousClose", meta.get("previousClose", price))
            
            if not price or price == 0:
                quote = result["indicators"]["quote"][0]
                closes = [c for c in quote.get("close", []) if c is not None]
                if closes:
                    price = closes[-1]
                    prev_close = closes[0] if len(closes) > 1 else price
            
            change = price - prev_close
            change_pct = (change / prev_close * 100) if prev_close else 0.0
            status = "UP" if change >= 0 else "DOWN"

            return {
                "symbol": symbol,
                "name": target["name"],
                "category": target["category"],
                "unit": target["unit"],
                "detail_url": target.get("detail_url", "#"),
                "source_label": target.get("source_label", "富果 Fugle"),
                "platform_links": target.get("platform_links", []),
                "price": round(price, 2),
                "change": round(change, 2),
                "change_pct": round(change_pct, 2),
                "status": status,
                "high": round(meta.get("regularMarketDayHigh", price * 1.005), 2),
                "low": round(meta.get("regularMarketDayLow", price * 0.995), 2),
            }
    except Exception as e:
        logger.warning(f"Error fetching {symbol} from Yahoo: {e}")
    return None

def fetch_all_market_data():
    results = []
    logger.info("Fetching market data with Fugle, CMoney, Yahoo and StatementDog homepage links...")
    for item in SYMBOLS:
        res = fetch_single_yahoo_symbol(item)
        if res:
            results.append(res)
        else:
            fb = next((f for f in DEFAULT_FALLBACK if f["symbol"] == item["symbol"]), None)
            if fb:
                results.append(fb)
    
    if len(results) < 5:
        return DEFAULT_FALLBACK
    return results

if __name__ == "__main__":
    data = fetch_all_market_data()
    print(json.dumps(data, indent=2, ensure_ascii=False))
