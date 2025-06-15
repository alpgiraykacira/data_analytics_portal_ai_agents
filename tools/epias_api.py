import requests
import dotenv
import os
from langchain.tools import tool
from logger import setup_logger, LogLevelContext
from typing import Dict, Annotated
import json

logger = setup_logger("logs/epias_api.log")

dotenv.load_dotenv()

def get_token(username, password):
    url = "https://giris.epias.com.tr/cas/v1/tickets"
    body = {"username": username, "password": password}
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "text/plain"
    }
    response = requests.post(url, headers=headers, data=body)
    return response.text

username = os.getenv("EPIAS_USERNAME")
password = os.getenv("EPIAS_PASSWORD")

@tool
def call_transparency_api(
        method: Annotated[str, "HTTP method e.g., GET or POST"],
        service: Annotated[str, "This is always '/electricity-service'"],
        endpoint: Annotated[str, "Specify the full endpoint e.g., '/v1/markets/dam/data/mcp'"],
        body: Annotated[dict, "JSON body containing parameters"]
) -> str:
    """
    Calls the EPIAS Transparency API and returns the JSON response
    as a compact string (no spaces, no unnecessary escapes).
    """
    tgt = get_token(username, password)
    host = "https://seffaflik.epias.com.tr"
    url = host + service + endpoint
    headers = {
        "Accept-Language": "en",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "TGT": tgt
    }
    try:
        with LogLevelContext(logger, "DEBUG"):
            logger.debug(f"API call: {method} {endpoint}")
        logger.info(f"API call to {endpoint} - {len(str(body))} bytes")
        response = requests.request(method, url, headers=headers, json=body)
        response.raise_for_status()
        data = response.json()
        # Serialize without spaces or newlines
        compact_json = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
        logger.info(f"API call successful, returning compact JSON: {compact_json}")
        return compact_json

    except Exception as e:
        logger.error(f"Error calling EPIAS API: {e}")
        # Return the error as a compact JSON too
        return json.dumps({"error": str(e)}, separators=(',', ':'), ensure_ascii=False)