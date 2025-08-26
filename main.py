import requests
import os
from dotenv import load_dotenv
import logging

# Load biến môi trường từ file config.env
load_dotenv("config.env")

# Logging cấu hình
logging.basicConfig(
    filename='motp_bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def get_balance():
    """
    Gọi API GetBalance từ MOTP và trả về kết quả JSON.
    """
    token = os.getenv("MOTP_TOKEN")
    if not token:
        logging.error("Không tìm thấy MOTP_TOKEN trong config.env")
        return {"error": True, "message": "Thiếu token"}

    url = "https://gw.motp.vn/MOTP/GetBalance"
    params = {"token": token}

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Lỗi khi gọi API MOTP: {e}")
        return {"error": True, "message": str(e)}
    except ValueError:
        return {"error": True, "message": "Không thể phân tích JSON từ server"}


def send_to_telegram(message):
    """
    Gửi một tin nhắn đến Telegram thông qua Bot API.
    """
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        logging.error("Thiếu TELEGRAM_BOT_TOKEN hoặc TELEGRAM_CHAT_ID trong config.env")
        return

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
        logging.info("Đã gửi tin nhắn thành công đến Telegram.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Lỗi khi gửi tin nhắn Telegram: {e}")


if __name__ == "__main__":
    # Debug thử xem có load đúng không
    print("MOTP_TOKEN =", os.getenv("MOTP_TOKEN"))
    print("TELEGRAM_BOT_TOKEN =", os.getenv("TELEGRAM_BOT_TOKEN"))
    print("TELEGRAM_CHAT_ID =", os.getenv("TELEGRAM_CHAT_ID"))

    result = get_balance()

    if "error" in result and result["error"]:
        send_to_telegram(f"❌ Lỗi khi lấy số dư MOTP: {result['message']}")
    else:
        balance = result.get("Balance", "Không rõ")
        send_to_telegram(f"💰 Số dư tài khoản MOTP: `{balance}`")
