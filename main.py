import requests
import logging

# Logging cấu hình
logging.basicConfig(
    filename='motp_bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Token cố định
TOKEN = "2A987C9227E011AD7B64372D32FF931D2F17D6D3"

def get_balance():
    """
    Gọi API GetBalance từ MOTP với token cố định và trả về JSON.
    """
    url = f"https://gw.motp.vn/MOTP/GetBalance?token={TOKEN}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Lỗi khi gọi API MOTP: {e}")
        return {"error": True, "message": str(e)}
    except ValueError:
        return {"error": True, "message": "Không thể phân tích JSON từ server"}


if __name__ == "__main__":
    result = get_balance()
    print("Kết quả API MOTP:", result)

    if "error" in result and result["error"]:
        print("❌ Lỗi khi lấy số dư:", result["message"])
    else:
        balance = result.get("Balance", "Không rõ")
        print(f"💰 Số dư tài khoản MOTP: {balance}")
