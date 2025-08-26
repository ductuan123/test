import requests
import os
import json
from dotenv import load_dotenv

# Load biến môi trường
load_dotenv("config.env")

API_BASE = "https://gw.motp.vn/MOTP"


def get_balance():
    token = os.getenv("MOTP_TOKEN")
    if not token:
        return {"error": True, "message": "Thiếu MOTP_TOKEN"}

    url = f"{API_BASE}/GetBalance"
    params = {"token": token}
    try:
        res = requests.get(url, params=params, timeout=10)
        data = res.json()

        # Data ở đây là string JSON → parse tiếp
        if "Data" in data and isinstance(data["Data"], str):
            data["Data"] = json.loads(data["Data"])

        return data
    except Exception as e:
        return {"error": True, "message": str(e)}


def get_service():
    token = os.getenv("MOTP_TOKEN")
    if not token:
        return {"error": True, "message": "Thiếu MOTP_TOKEN"}

    url = f"{API_BASE}/GetService"
    params = {"token": token}
    try:
        res = requests.get(url, params=params, timeout=10)
        data = res.json()

        if "Data" in data and isinstance(data["Data"], str):
            data["Data"] = json.loads(data["Data"])

        return data
    except Exception as e:
        return {"error": True, "message": str(e)}


def send_to_telegram(msg: str):
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

    # --- Lấy dịch vụ khả dụng ---
    service_result = get_service()
    if not service_result.get("error"):
        services = service_result.get("Data", [])
        if isinstance(services, list):
            msg = "🛠️ Dịch vụ khả dụng (A):\n"
            for idx, svc in enumerate(services, 1):
                if svc.get("Status") == "A":
                    msg += f"{idx}. [{svc.get('ServiceCode')}] {svc.get('ServiceName')}\n"
            send_to_telegram(msg.strip())
