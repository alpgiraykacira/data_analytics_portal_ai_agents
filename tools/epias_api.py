import requests
import dotenv
import os
from langchain_core.tools import tool
from logger import setup_logger
from typing import Dict, Annotated

logger = setup_logger()

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
) -> Dict:
    """
    Calls the EPIAS Transparency API to fetch data using the specified HTTP method, service,
    endpoint, and request body. This function manages token retrieval and constructs the request
    with the necessary headers.

    Args:
        method: HTTP method e.g., GET or POST.
        service: This is always '/electricity-service'.
        endpoint: Specify the full endpoint e.g., '/v1/markets/dam/data/mcp'.
        body: JSON body containing parameters.

    Returns:
        dict: The JSON response from the API.
    """
    tgt = get_token(username, password)
    host = "https://seffaflik.epias.com.tr/"
    url = host + service + endpoint
    headers = {
        "Accept-Language": "en",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "TGT": tgt
    }
    try:
        logger.info(f"Calling EPIAS API: {url}")
        response = requests.request(method, url, headers=headers, json=body)
        logger.info(f"API call completed with status code: {response.status_code}")
        return response.json()
    except Exception as e:
        logger.error(f"Error calling EPIAS API: {str(e)}")
        return {"error": str(e)}