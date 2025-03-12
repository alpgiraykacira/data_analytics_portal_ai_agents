import requests
import dotenv
import os
from agents import function_tool

dotenv.load_dotenv()

username = os.getenv("EPIAS_USERNAME")
password = os.getenv("EPIAS_PASSWORD")

def get_token(username, password):
    """Authenticate and obtain a Ticket Granting Ticket (TGT)."""
    url = "https://giris.epias.com.tr/cas/v1/tickets"
    body = {"username": username, "password": password}
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "text/plain"
    }
    response = requests.post(url, headers=headers, data=body)
    return response.text

@function_tool
def transparency_agent(method, service, endpoint, body):
    """Make an authenticated request to EPİAŞ Transparency API."""
    tgt = get_token(username, password)
    host = "https://seffaflik.epias.com.tr/"
    url = host + service + endpoint
    headers = {
        "Accept-Language": "en",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "TGT": tgt
    }
    response = requests.request(method, url, headers=headers, json=body)
    return response.json()