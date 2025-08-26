import requests
import os
import json
from dotenv import load_dotenv

# Load biến môi trường
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


def rent_phone_number(service_id=1, type_id=3, phone_number=""):
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
    # --- Lấy số dư ---
    balance_result = get_balance()
    if not balance_result.get("error"):
        balance = balance_result.get("Data", {}).get("Balance", "Không rõ")
        send_to_telegram(f"💰 Số dư tài khoản: *{balance} VND*")
    else:
        send_to_telegram(f"❌ Lỗi khi lấy số dư: {balance_result['message']}")

    # --- Thuê số ---
    rent_result = rent_phone_number(service_id=1, type_id=3)

    if not rent_result.get("error"):
        data = rent_result.get("Data")

        if isinstance(data, dict):
            phone = data.get("PhoneNumber", "Không rõ")
            price = data.get("Price", "Không rõ")
            expired = data.get("ExpiredTime", "Không rõ")

            msg = f"📱 Thuê số điện thoại thành công:\n"
            msg += f"• Số: {phone}\n"
            msg += f"• Giá: {price} VND\n"
            msg += f"• Hết hạn: {expired}"
            send_to_telegram(msg)
        else:
            # Nếu Data không hợp lệ hoặc None
            send_to_telegram(f"⚠️ API không trả dữ liệu thuê số.\nPhản hồi: {rent_result}")
    else:
        send_to_telegram(f"❌ Lỗi khi thuê số: {rent_result['message']}")
