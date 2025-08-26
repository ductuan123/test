import requests
import os
import json
from dotenv import load_dotenv
import logging

# Load biến môi trường
load_dotenv("config.env")

# Logging
logging.basicConfig(
    filename='motp_bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

API_BASE = "https://gw.motp.vn/MOTP"


def call_api(endpoint, token):
    """Hàm gọi API chung"""
    url = f"{API_BASE}/{endpoint}"
    params = {"token": token}
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"🔎 [{endpoint}] status:", response.status_code)
        print(f"🔎 [{endpoint}] raw:", response.text)

        response.raise_for_status()
        result = response.json()

        # Nếu Data là string JSON → parse tiếp
        if "Data" in result and isinstance(result["Data"], str):
            try:
                result["Data"] = json.loads(result["Data"])
            except Exception as e:
                print(f"⚠️ Không parse được Data trong {endpoint}:", e)

        return result
    except Exception as e:
        return {"error": True, "message": str(e)}


def get_balance():
    token = os.getenv("MOTP_TOKEN")
    if not token:
        return {"error": True, "message": "Thiếu MOTP_TOKEN"}
    return call_api("GetBalance", token)


def get_network():
    token = os.getenv("MOTP_TOKEN")
    if not token:
        return {"error": True, "message": "Thiếu MOTP_TOKEN"}
    return call_api("GetNetwork", token)


if __name__ == "__main__":
    # Test GetBalance
    balance_result = get_balance()
    print("📌 Balance result:", balance_result)

    if not balance_result.get("error"):
        balance = balance_result.get("Data", {}).get("Balance")
        if balance:
            print(f"💰 Số dư: {int(balance):,} VNĐ")

    # Test GetNetwork
    network_result = get_network()
    print("📌 Network result:", network_result)

    if not network_result.get("error"):
        data = network_result.get("Data")
        if isinstance(data, list):
            print("🌐 Danh sách nhà mạng khả dụng:")
            for net in data:
                print(f"- {net}")
