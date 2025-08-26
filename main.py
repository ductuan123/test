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


def get_service():
    token = os.getenv("MOTP_TOKEN")
    if not token:
        return {"error": True, "message": "Thiếu MOTP_TOKEN"}
    return call_api("GetService", token)


if __name__ == "__main__":
    service_result = get_service()
    print("📌 Service result:", service_result)

    if not service_result.get("error"):
        data = service_result.get("Data")
        if isinstance(data, list):
            print("🛠️ Danh sách dịch vụ khả dụng:")
            for idx, svc in enumerate(data, start=1):
                code = svc.get("ServiceCode", "N/A")
                name = svc.get("ServiceName", "N/A")
                status = svc.get("Status", "N/A")
                print(f"{idx}. [{code}] {name} - Trạng thái: {status}")
