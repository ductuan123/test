import requests
import os
import json
from dotenv import load_dotenv

# Load biến môi trường
load_dotenv("config.env")

API_BASE = "https://gw.motp.vn/MOTP"


def get_service():
    token = os.getenv("MOTP_TOKEN")
    if not token:
        return {"error": True, "message": "Thiếu MOTP_TOKEN"}

    url = f"{API_BASE}/GetService"
    params = {"token": token}
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        # Nếu Data là string JSON → parse tiếp
        if "Data" in data and isinstance(data["Data"], str):
            data["Data"] = json.loads(data["Data"])

        return data
    except Exception as e:
        return {"error": True, "message": str(e)}


if __name__ == "__main__":
    service_result = get_service()

    if not service_result.get("error"):
        services = service_result.get("Data", [])
        if isinstance(services, list):
            print("🛠️ Dịch vụ khả dụng (Status = A):")
            for idx, svc in enumerate(services, start=1):
                if svc.get("Status") == "A":   # chỉ lấy dịch vụ dùng được
                    code = svc.get("ServiceCode", "N/A")
                    name = svc.get("ServiceName", "N/A")
                    print(f"{idx}. [{code}] {name}")
        else:
            print("⚠️ Không có danh sách dịch vụ hợp lệ.")
    else:
        print("❌ Lỗi:", service_result["message"])
