# api/dhan_client.py

import os
import requests
from dotenv import load_dotenv

load_dotenv()

class DhanClient:
    def __init__(self, client_id: str, access_token: str, base_url: str = "https://api.dhan.co"):
        self.client_id = client_id
        self.access_token = access_token
        self.base_url = base_url.rstrip("/")

    def get_headers(self):
        return {
            "accept": "application/json",
            "access-token": self.access_token,
            "client-id": self.client_id
        }

    def get(self, endpoint: str, params: dict = None):
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = requests.get(url, headers=self.get_headers(), params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print("Response text:", response.text)
            raise Exception(f"GET {url} failed: {e}")

    def post(self, endpoint: str, payload: dict):
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = requests.post(url, headers=self.get_headers(), json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"POST {url} failed: {e}")

    def validate_session(self):
        try:
            self.get("v2/profile")
            return True
        except:
            return False


# ✅ DhanClientFactory
def get_trading_client():
    return DhanClient(
        client_id=os.getenv("DHAN_TRADING_CLIENT_ID"),
        access_token=os.getenv("DHAN_TRADING_ACCESS_TOKEN"),
        base_url=os.getenv("DHAN_BASE_URL", "https://api.dhan.co")
    )

def get_data_client():
    return DhanClient(
        client_id=os.getenv("DHAN_DATA_CLIENT_ID"),
        access_token=os.getenv("DHAN_DATA_ACCESS_TOKEN"),
        base_url=os.getenv("DHAN_BASE_URL", "https://api.dhan.co")
    )
