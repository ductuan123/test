import requests
import os
import json
import time
from dotenv import load_dotenv

load_dotenv("config.env")

API_BASE = "https://gw.motp.vn/MOTP"
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Danh sách dịch vụ hỗ trợ
SERVICES = {
    "lazada": 1,
    "shopee": 2,
    "tiktok": 3,
    # thêm dịch vụ khác tại đây
}


def call_api(endpoint, params, method="GET"):
    try:
        if method.upper() == "GET":
            res = requests.get(f"{API_BASE}/{endpoint}", params=params, timeout=10)
        else:
            res = requests.post(f"{API_BASE}/{endpoint}", data=params, timeout=10)
        res.raise_for_status()
        data = res.json()
        if "Data" in data and isinstance(data["Data"], str):
            try:
                data["Data"] = json.loads(data["Data"])
            except Exception:
                pass
        return data
    except Exception as e:
        return {"error": True, "message": str(e)}


def get_balance():
    token = os.getenv("MOTP_TOKEN")
    return call_api("GetBalance", {"token": token})


def rent_phone(service_id):
    token = os.getenv("MOTP_TOKEN")
    params = {"token": token, "serviceID": service_id, "type": 1}
    return call_api("RentPhoneNumber", params)


def get_history(service_id, transaction_code):
    token = os.getenv("MOTP_TOKEN")
    params = {"token": token, "serviceID": service_id, "transactionCode": transaction_code}
    return call_api("History", params)


def reply_sms(phone_number, message_text):
    token = os.getenv("MOTP_TOKEN")
    params = {"token": token, "phoneNumber": phone_number, "message": message_text}
    return call_api("ReplySMS", params, method="POST")


def send_to_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
    except Exception as e:
        print("❌ Lỗi gửi Telegram:", e)


def listen_commands():
    """Lắng nghe lệnh từ Telegram liên tục"""
    last_update_id = 0
    while True:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={last_update_id+1}"
        try:
            res = requests.get(url, timeout=20).json()
            for update in res.get("result", []):
                last_update_id = update["update_id"]
                if "message" in update:
                    text = update["message"].get("text", "").strip().lower()
                    handle_command(text)
        except Exception as e:
            print("❌ Lỗi khi lắng nghe:", e)
        time.sleep(2)


def handle_command(text):
    """Xử lý lệnh từ Telegram"""
    if text == "/balance":
        balance = get_balance()
        if not balance.get("error"):
            bal = balance.get("Data", {}).get("Balance", "Không rõ")
            send_to_telegram(f"💰 Số dư: *{bal} VND*")
        else:
            send_to_telegram(f"❌ {balance['message']}")

    elif text.startswith("/rent"):
        parts = text.split()
        if len(parts) < 2:
            send_to_telegram("⚠️ Dùng lệnh: `/rent <tên dịch vụ>`")
            return

        service_name = parts[1]
        service_id = SERVICES.get(service_name)
        if not service_id:
            send_to_telegram("⚠️ Dịch vụ không hợp lệ.")
            return

        rent = rent_phone(service_id)
        if not rent.get("error") and isinstance(rent.get("Data"), dict):
            data = rent["Data"]
            phone = data.get("RentalPhoneNumber", "Không rõ")
            price = data.get("Price", "Không rõ")
            expired = data.get("ExpiredTime", "Không rõ")
            transaction = data.get("TransactionCode")

            send_to_telegram(
                f"📱 *Thuê số thành công ({service_name.title()})*\n"
                f"• Số: {phone}\n"
                f"• Giá: {price} VND\n"
                f"• Hết hạn: {expired}\n"
                f"• TransactionCode: `{transaction}`"
            )

            # Bắt đầu check SMS và trả lời tự động
            check_history_loop_with_reply(service_id, transaction, reply_text="Cảm ơn!")
        else:
            send_to_telegram(f"❌ Thuê số thất bại: {rent}")

    elif text == "/help":
        help_msg = (
            "🤖 *Hướng dẫn sử dụng bot MOTP:*\n"
            "• `/balance` - Xem số dư tài khoản\n"
            "• `/rent <tên dịch vụ>` - Thuê số điện thoại\n"
            "   Ví dụ: `/rent lazada` hoặc `/rent shopee`\n"
            "• Bot sẽ tự động check SMS và trả lời khi có tin nhắn mới"
        )
        send_to_telegram(help_msg)

    else:
        send_to_telegram("⚡ Lệnh không hợp lệ. Dùng `/help` để xem hướng dẫn.")


def check_history_loop_with_reply(service_id, transaction_code, reply_text="Cảm ơn!"):
    """Check lịch sử SMS liên tục và trả lời tự động"""
    sent_codes = set()  # lưu các tin nhắn đã xử lý
    while True:
        history = get_history(service_id, transaction_code)
        if not history.get("error") and isinstance(history.get("Data"), dict):
            data = history["Data"]
            phone = data.get("RentalPhoneNumber", "Không rõ")
            code = data.get("Code") or data.get("TransDetail")

            if code and code not in sent_codes:
                sent_codes.add(code)
                # Gửi tin nhắn về Telegram
                send_to_telegram(f"📖 *Tin nhắn mới:*\n• 📱 Số: {phone}\n• ✉️ {code}")

                # Tự động trả lời
                reply_result = reply_sms(phone, reply_text)
                if not reply_result.get("error"):
                    send_to_telegram(f"✅ Đã trả lời tin nhắn tự động: {reply_text}")
                else:
                    send_to_telegram(f"❌ Lỗi khi trả lời: {reply_result.get('message')}")
        time.sleep(30)


if __name__ == "__main__":
    send_to_telegram("🤖 Bot MOTP đã khởi động! Dùng `/help` để xem lệnh.")
    listen_commands()
