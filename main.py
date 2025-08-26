import requests
import os
import json
import time
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
    token = os.getenv("MOTP_TOKEN")
    if not token:
        return {"error": True, "message": "Thiếu MOTP_TOKEN"}
    return call_api("GetBalance", {"token": token})


def rent_phone_number(service_id=1, type_id=1, phone_number=""):
    token = os.getenv("MOTP_TOKEN")
    if not token:
        return {"error": True, "message": "Thiếu MOTP_TOKEN"}

    params = {"token": token, "serviceID": service_id, "type": type_id, "phoneNumber": phone_number}
    return call_api("RentPhoneNumber", params)


def get_history(service_id=1, transaction_code=""):
    token = os.getenv("MOTP_TOKEN")
    if not token:
        return {"error": True, "message": "Thiếu MOTP_TOKEN"}

    params = {"token": token, "serviceID": service_id, "transactionCode": transaction_code}
    return call_api("History", params)


def send_to_telegram(msg: str):
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
        data = balance_result.get("Data", {})
        balance = data.get("Balance", "Không rõ") if isinstance(data, dict) else "Không rõ"
        message += f"💰 Số dư tài khoản: *{balance} VND*\n\n"
    else:
        message += f"❌ Lỗi khi lấy số dư: {balance_result['message']}\n\n"

    # --- Thuê số ---
    transaction_code = None
    rent_result = rent_phone_number(service_id=1, type_id=1)

    if not rent_result.get("error"):
        data = rent_result.get("Data")
        if isinstance(data, dict):
            rental_phone = data.get("RentalPhoneNumber", "Không rõ")
            price = data.get("Price", "Không rõ")
            expired = data.get("ExpiredTime", "Không rõ")
            transaction_code = data.get("TransactionCode")

            message += "📱 *Thuê số thành công:*\n"
            message += f"• RentalPhoneNumber: {rental_phone}\n"
            message += f"• Giá: {price} VND\n"
            message += f"• Hết hạn: {expired}\n"
            message += f"• TransactionCode: `{transaction_code}`\n\n"
        else:
            message += f"⚠️ API không trả dữ liệu thuê số.\nPhản hồi: {rent_result}\n\n"
    else:
        message += f"❌ Lỗi khi thuê số: {rent_result['message']}\n\n"

    # Gửi thông tin thuê số ngay lập tức
    send_to_telegram(message)

    # --- Vòng lặp kiểm tra lịch sử giao dịch ---
    if transaction_code:
        for i in range(12):  # kiểm tra tối đa 12 lần (tức ~1 phút)
            history_result = get_history(service_id=1, transaction_code=transaction_code)

            if not history_result.get("error"):
                data = history_result.get("Data")
                if isinstance(data, dict):
                    content = data.get("Content", "")
                    status = data.get("Status", "Không rõ")

                    if content:  # nếu đã có nội dung (OTP, SMS...)
                        msg = "📖 *Kết quả lịch sử giao dịch:*\n"
                        msg += f"• TransactionCode: `{transaction_code}`\n"
                        msg += f"• Trạng thái: {status}\n"
                        msg += f"• Nội dung: {content}\n"
                        send_to_telegram(msg)
                        break
            else:
                send_to_telegram(f"❌ Lỗi khi lấy lịch sử: {history_result['message']}")

            time.sleep(5)  # chờ 5s trước khi thử lại
