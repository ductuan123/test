import requests
import os
import json
import time
import threading
from dotenv import load_dotenv

load_dotenv("config.env")

API_BASE = "https://gw.motp.vn/MOTP"
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
AUTHORIZED_ID = 7605356455  # chỉ user này xem balance

SERVICES_LIST = {
    1: ("000262", "FB88", 1000),
    2: ("000223", "Sms-f8bet", 2000),
    # ... thêm toàn bộ danh sách
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


def send_to_telegram(msg, chat_id=CHAT_ID):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"})
    except Exception as e:
        print("❌ Lỗi gửi Telegram:", e)


def handle_rent_service(chat_id, stt):
    """Xử lý thuê số trong thread riêng"""
    if stt not in SERVICES_LIST:
        send_to_telegram("⚠️ STT không hợp lệ", chat_id)
        return

    service_id, name, price = SERVICES_LIST[stt]
    rent = rent_phone(service_id)
    if not rent.get("error") and isinstance(rent.get("Data"), dict):
        data = rent["Data"]
        phone = data.get("RentalPhoneNumber", "Không rõ")
        transaction = data.get("TransactionCode")
        expired = data.get("ExpiredTime", "Không rõ")
        send_to_telegram(
            f"📱 Thuê số thành công ({name})\n"
            f"• Số: {phone}\n"
            f"• Giá: {price} VND\n"
            f"• Hết hạn: {expired}\n"
            f"• TransactionCode: `{transaction}`",
            chat_id
        )
        # Check SMS và trả lời trong thread riêng
        check_history_loop_with_reply(service_id, transaction, reply_text="Cảm ơn!", chat_id=chat_id)
    else:
        send_to_telegram(f"❌ Thuê số thất bại: {rent}", chat_id)


def check_history_loop_with_reply(service_id, transaction_code, reply_text="Cảm ơn!", chat_id=CHAT_ID):
    sent_codes = set()
    while True:
        history = get_history(service_id, transaction_code)
        if not history.get("error") and isinstance(history.get("Data"), dict):
            data = history["Data"]
            phone = data.get("RentalPhoneNumber", "Không rõ")
            code = data.get("Code") or data.get("TransDetail")
            if code and code not in sent_codes:
                sent_codes.add(code)
                send_to_telegram(f"📖 Tin nhắn mới:\n• Số: {phone}\n• ✉️ {code}", chat_id)
                reply_result = reply_sms(phone, reply_text)
                if not reply_result.get("error"):
                    send_to_telegram(f"✅ Đã trả lời tin nhắn tự động: {reply_text}", chat_id)
                else:
                    send_to_telegram(f"❌ Lỗi khi trả lời: {reply_result.get('message')}", chat_id)
        time.sleep(30)


def handle_command(chat_id, text):
    text = text.strip().lower()
    if text == "/balance":
        if chat_id != AUTHORIZED_ID:
            send_to_telegram("⚠️ Bạn không có quyền xem số dư.", chat_id)
            return
        balance = get_balance()
        if not balance.get("error"):
            bal = balance.get("Data", {}).get("Balance", "Không rõ")
            send_to_telegram(f"💰 Số dư: *{bal} VND*", chat_id)
        else:
            send_to_telegram(f"❌ {balance['message']}", chat_id)

    elif text.startswith("/rent"):
        parts = text.split()
        if len(parts) < 2:
            send_to_telegram("⚠️ Dùng lệnh: `/rent <STT>`", chat_id)
            return
        try:
            stt = int(parts[1])
        except:
            send_to_telegram("⚠️ STT phải là số nguyên", chat_id)
            return
        # Chạy thuê số trong thread riêng để không block bot
        threading.Thread(target=handle_rent_service, args=(chat_id, stt)).start()

    elif text == "/help":
        help_msg = (
            "🤖 Hướng dẫn sử dụng bot:\n"
            "• `/balance` - Xem số dư (chỉ user 7605356455)\n"
            "• `/rent <STT>` - Thuê số điện thoại theo STT\n"
            "• Bot check SMS và trả lời tự động\n"
            "• `/help` - Hướng dẫn sử dụng"
        )
        send_to_telegram(help_msg, chat_id)
    else:
        send_to_telegram("⚡ Lệnh không hợp lệ. Dùng `/help` để xem hướng dẫn.", chat_id)


def listen_commands():
    last_update_id = 0
    while True:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={last_update_id+1}"
        try:
            res = requests.get(url, timeout=20).json()
            for update in res.get("result", []):
                last_update_id = update["update_id"]
                if "message" in update:
                    chat_id = update["message"]["chat"]["id"]
                    text = update["message"].get("text", "").strip().lower()
                    handle_command(chat_id, text)
        except Exception as e:
            print("❌ Lỗi khi lắng nghe:", e)
        time.sleep(2)


if __name__ == "__main__":
    send_to_telegram("🤖 Bot MOTP đã khởi động! Dùng `/help` để xem lệnh.")
    listen_commands()
