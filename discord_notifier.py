import requests
import json
import logging
import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("discord_notifier")

SPIDEY_RED = 0xE23636
VENOM_BLUE = 0x00D2FF
NEUTRAL_YELLOW = 0xF59E0B

def send_discord_test(webhook_url):
    """Sends a quick verification message to the Discord channel."""
    if not webhook_url or not ("discord.com/api/webhooks" in webhook_url or "discordapp.com/api/webhooks" in webhook_url):
        return False, "Webhook 網址格式錯誤，必須包含 discord.com/api/webhooks"

    payload = {
        "username": "🕷️ 蜘蛛感應戰情室",
        "embeds": [
            {
                "title": "🎉 Discord 晨報推播連線成功！",
                "description": "恭喜！您的 Discord Webhook 已成功綁定【蜘蛛感應 - 每日財金戰情室】。\n系統將在每日預定時間自動推送最新市場情報與晨報到此頻道。",
                "color": VENOM_BLUE,
                "fields": [
                    {"name": "⏰ 狀態", "value": "連線正常 / 即時推播就緒", "inline": True},
                    {"name": "📅 測試時間", "value": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "inline": True}
                ],
                "footer": {"text": "🕷️ 蜘蛛感應戰情室 • Discord 即時推播"}
            }
        ]
    }

    try:
        resp = requests.post(webhook_url.strip(), json=payload, timeout=10)
        if resp.status_code in (200, 204):
            logger.info("Successfully sent test message to Discord!")
            return True, "測試訊息已成功推播至 Discord！請查看頻道。"
        elif resp.status_code == 401:
            err = "Discord 拒絕存取 (401 Unauthorized)：您的 Webhook 網址似乎被截斷或不完整。請在 Discord 點擊「複製 Webhook 網址」按鈕重新複製完整網址！"
            logger.error(f"Discord test failed: {err} (Raw: {resp.text})")
            return False, err
        elif resp.status_code == 404:
            err = "找不到該 Webhook (404 Not Found)：該 Webhook 可能已被刪除，請重新在 Discord 建立一個新的 Webhook。"
            logger.error(f"Discord test failed: {err}")
            return False, err
        else:
            err = f"Discord 回應錯誤 (HTTP {resp.status_code}): {resp.text}"
            logger.error(f"Discord test failed: {err}")
            return False, err
    except Exception as e:
        logger.error(f"Error sending Discord test: {e}")
        return False, f"連線至 Discord 失敗: {str(e)}"

def send_discord_briefing(webhook_url, briefing, market_data=None):
    """Formats the executive briefing into a Discord Embed and posts it."""
    if not webhook_url or not ("discord.com/api/webhooks" in webhook_url or "discordapp.com/api/webhooks" in webhook_url):
        return False, "Discord Webhook 網址無效"

    title = briefing.get("title", "🕷️ 蜘蛛感應 • 每日財金晨報")
    date_str = briefing.get("date", datetime.datetime.now().strftime("%Y-%m-%d"))
    sentiment = briefing.get("overall_sentiment", "中性觀望")
    gauge = briefing.get("sentiment_gauge", 50)
    exec_summary = briefing.get("executive_summary", "")

    # Pick embed color based on sentiment
    if "多" in sentiment or "Bullish" in sentiment:
        color = 0x10B981 # emerald green
    elif "空" in sentiment or "Risk-Off" in sentiment:
        color = SPIDEY_RED # red
    else:
        color = VENOM_BLUE # cyan / neutral

    fields = [
        {
            "name": "📊 市場情緒氣壓計",
            "value": f"**{sentiment}** (信心指數: `{gauge}%`)",
            "inline": False
        },
        {
            "name": "📝 重點精華導讀",
            "value": exec_summary[:1000] if exec_summary else "今日市場焦點彙整中...",
            "inline": False
        }
    ]

    # Add 3 Focus Themes
    themes = briefing.get("top_3_focus_themes", [])
    if themes:
        theme_texts = []
        for t in themes:
            theme_texts.append(f"**{t.get('theme', '')}**\n> {t.get('desc', '')}")
        fields.append({
            "name": "🔥 今日三大核心焦點",
            "value": "\n\n".join(theme_texts)[:1020],
            "inline": False
        })

    # Add Risk Warnings
    risks = briefing.get("risk_warnings", [])
    if risks:
        fields.append({
            "name": "⚠️ 風險提示",
            "value": "\n".join(risks)[:1020],
            "inline": False
        })

    payload = {
        "username": "🕷️ 蜘蛛感應戰情室",
        "embeds": [
            {
                "title": f"🕷️ 每日財經與加密情報晨報 ({date_str})",
                "color": color,
                "fields": fields,
                "footer": {"text": "🕷️ 蜘蛛感應 • 每日自動化晨報服務"},
                "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
            }
        ]
    }

    try:
        resp = requests.post(webhook_url.strip(), json=payload, timeout=12)
        if resp.status_code in (200, 204):
            logger.info("Successfully sent Morning Briefing to Discord!")
            return True, "晨報已成功推送至 Discord！"
        elif resp.status_code == 401:
            err = "Discord 拒絕存取 (401 Unauthorized)：您的 Webhook 網址不完整。請在 Discord 點擊「複製 Webhook 網址」按鈕取得完整網址！"
            logger.error(f"Discord push briefing failed: {err}")
            return False, err
        else:
            err = f"Discord 回應錯誤 (HTTP {resp.status_code}): {resp.text}"
            logger.error(f"Discord push briefing failed: {err}")
            return False, err
    except Exception as e:
        logger.error(f"Error sending briefing to Discord: {e}")
        return False, f"連線至 Discord 失敗: {str(e)}"
