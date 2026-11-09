import requests
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("line_notifier")

LINE_BROADCAST_URL = "https://api.line.me/v2/bot/message/broadcast"
LINE_PUSH_URL = "https://api.line.me/v2/bot/message/push"

def send_line_message(token, text_message, user_id=None):
    """
    Sends a text message using LINE Messaging API.
    If user_id is provided, sends to that specific user.
    Otherwise sends a broadcast message to all followers of the LINE Official Account.
    """
    if not token or len(token.strip()) < 10:
        logger.warning("LINE Token is empty or invalid. Skipping LINE push.")
        return False, "Token 未設定或無效"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token.strip()}"
    }

    # Truncate text if exceeds LINE 5000 chars limit
    if len(text_message) > 4900:
        text_message = text_message[:4900] + "\n...(訊息較長，請開啟戰情室觀看完整版)"

    if user_id:
        url = LINE_PUSH_URL
        payload = {
            "to": user_id.strip(),
            "messages": [{"type": "text", "text": text_message}]
        }
    else:
        url = LINE_BROADCAST_URL
        payload = {
            "messages": [{"type": "text", "text": text_message}]
        }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        if resp.status_code == 200:
            logger.info("Successfully sent LINE push message!")
            return True, "推送成功"
        else:
            err_msg = f"HTTP {resp.status_code}: {resp.text}"
            logger.error(f"LINE Push failed: {err_msg}")
            return False, err_msg
    except Exception as e:
        logger.error(f"Error sending LINE push: {e}")
        return False, str(e)

if __name__ == "__main__":
    # Quick test stub
    print("LINE Notifier module ready.")
