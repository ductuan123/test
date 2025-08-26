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
    3: ("000222", "Sms-hi88", 1000),
    4: ("000217", "SMS-Shbet", 500),
    5: ("000216", "68GB", 1000),
    6: ("000204", "VIC88 - Perfy", 500),
    7: ("000202", "F168", 500),
    8: ("000201", "Thiso reward", 500),
    9: ("000187", "Zalopay", 500),
    10: ("000186", "Bất cứ dịch vụ nào cũng được", 500),
    11: ("000185", "Udemi", 500),
    12: ("000184", "Tony", 500),
    13: ("000182", "WhatsApp", 500),
    14: ("000181", "Yahoo", 500),
    15: ("000180", "AMAZON JP", 500),
    16: ("000179", "PAYPAY", 500),
    17: ("000178", "Line", 500),
    18: ("000177", "TikTok", 500),
    19: ("000176", "Medicare.vn", 500),
    20: ("000175", "Bumble", 500),
    21: ("000174", "Hinge", 500),
    22: ("000173", "BRAX", 500),
    23: ("000172", "AIO", 500),
    24: ("000171", "AIA Vietnam", 500),
    25: ("000170", "Telegram", 3000),
    26: ("000169", "WhatsApp", 500),
    27: ("000168", "Facebook", 3000),
    28: ("000166", "Viber", 500),
    29: ("000165", "Twitter", 500),
    30: ("000163", "Zalo", 500),
    31: ("000162", "Wechat", 500),
    32: ("000161", "Okvip", 1000),
    33: ("000142", "sonnguyen_test", 1000),
    34: ("000141", "Thiennv_Testdichvu", 1000),
    35: ("000101", "Luckylotter", 500),
    36: ("000082", "Tinder", 500),
    37: ("000081", "bet88", 500),
    38: ("000061", "Shopee / ShopeePay", 500),
    39: ("000021", "Tiki", 500),
    40: ("000002", "Gmail/Google", 500),
    41: ("000001", "Khác", 500),
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


def send_to_telegram(msg, chat_id):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"})
    except Exception as e:
        print("❌ Lỗi gửi Telegram:", e)


def check_history_loop_with_otp(service_id, transaction_code, chat_id):
    """Kiểm tra lịch sử SMS, gửi OTP mới về Telegram (gọn)"""
    sent_codes = set()
    while True:
        history = get_history(service_id, transaction_code)
        if not history.get("error") and isinstance(history.get("Data"), dict):
            data = history["Data"]
            phone = data.get("RentalPhoneNumber", "Không rõ")
            otp = data.get("Code") or data.get("TransDetail")
            if otp and otp not in sent_codes:
                sent_codes.add(otp)
                send_to_telegram(f"📱 Số: {phone}\n✉️ {otp}", chat_id)
        time.sleep(30)


def handle_rent_service(chat_id, stt):
    """Thuê số trong thread riêng"""
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
        # Chạy check OTP trong thread riêng
        threading.Thread(
            target=check_history_loop_with_otp,
            args=(service_id, transaction, chat_id)
        ).start()
    else:
        send_to_telegram(f"❌ Thuê số thất bại: {rent}", chat_id)


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

    elif text == "/list":
        msg = "📋 *Danh sách dịch vụ:*\n"
        for stt, (service_id, name, price) in SERVICES_LIST.items():
            msg += f"{stt}. {name} - Giá: {price} VND\n"
        send_to_telegram(msg, chat_id)

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
        threading.Thread(target=handle_rent_service, args=(chat_id, stt)).start()

    elif text == "/help":
        help_msg = (
            "🤖 Hướng dẫn sử dụng bot:\n"
            "• `/balance` - Xem số dư (chỉ user 7605356455)\n"
            "• `/list` - Hiển thị danh sách dịch vụ\n"
            "• `/rent <STT>` - Thuê số điện thoại theo STT\n"
            "• Bot check OTP và gửi về Telegram\n"
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
                    text = update["message"].get("text", "").strip()
                    handle_command(chat_id, text)
        except Exception as e:
            print("❌ Lỗi khi lắng nghe:", e)
        time.sleep(2)


if __name__ == "__main__":
    print("🤖 Bot MOTP đã khởi động!")
    listen_commands()
