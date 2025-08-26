import requests
import os
import json
from dotenv import load_dotenv

# Load biến môi trường từ file config.env
load_dotenv("config.env")

API_BASE = "https://gw.motp.vn/MOTP"


def call_api(endpoint, params):
    """Hàm gọi API chung"""
    try:
        res = requests.get(f"{API_BASE}/{endpoint}", params=params, timeout=10)
        res.raise_for_status()
        data = res.json()

        # Nếu Data là chuỗi JSON → parse tiếp
        if "Data" in data and isinstance(data["Data"], str):
            try:
                data["Data"] = json.loads(data["Data"])
            except Exception:
                pass
        return data
    except Exception as e:
        return {"error": True, "message": str(e)}


def get_balance():
    """Lấy số dư tài khoản"""
    token = os.getenv("MOTP_TOKEN")
    if not token:
        return {"error": True, "message": "Thiếu MOTP_TOKEN"}
    return call_api("GetBalance", {"token": token})


def rent_phone_number(service_id=1, type_id=1, phone_number=""):
    """Thuê số điện thoại"""
    token = os.getenv("MOTP_TOKEN")
    if not token:
        return {"error": True, "message": "Thiếu MOTP_TOKEN"}

    params = {
        "token": token,
        "serviceID": service_id,
        "type": type_id,
        "phoneNumber": phone_number
    }
    return call_api("RentPhoneNumber", params)


def send_to_telegram(msg: str):
    """Gửi tin nhắn đến Telegram"""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not bot_token or not chat_id:
        return

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"})


if __name__ == "__main__":
    message = ""

    # --- Lấy số dư ---
    balance_result = get_balance()
    if not balance_result.get("error"):
        balance = balance_result.get("Data", {}).get("Balance", "Không rõ")
        message += f"💰 Số dư tài khoản: *{balance} VND*\n\n"
    else:
        message += f"❌ Lỗi khi lấy số dư: {balance_result['message']}\n\n"

    # --- Thuê số ---
    rent_result = rent_phone_number(service_id=1, type_id=1)

    if not rent_result.get("error"):
        data = rent_result.get("Data")

        if isinstance(data, dict):
            phone = data.get("PhoneNumber", "Không rõ")
            price = data.get("Price", "Không rõ")
            expired = data.get("ExpiredTime", "Không rõ")

            message += "📱 *Thuê số thành công:*\n"
            message += f"• Số: {phone}\n"
            message += f"• Giá: {price} VND\n"
            message += f"• Hết hạn: {expired}\n"
        else:
            message += f"⚠️ API không trả dữ liệu thuê số.\nPhản hồi: {rent_result}\n"
    else:
        message += f"❌ Lỗi khi thuê số: {rent_result['message']}\n"

    # --- Gửi gộp ---
    send_to_telegram(message)
