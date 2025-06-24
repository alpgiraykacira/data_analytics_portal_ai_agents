from core.agent import create_agent
from tools.epias_api import call_transparency_api
import json

def create_api_agent(llm, members):
    """Create the API agent"""
    tools = [call_transparency_api]

    system_prompt = """
    You are an API expert agent. Your job is to:
    
    1. Look at the retrieval_state to find the API call specifications
    2. Execute each API call using the call_transparency_api tool
    3. Return the combined results in the required format
    
    The retrieval_state contains a JSON with "api_calls" array. Each item has:
    - method: HTTP method (GET/POST)
    - service: Always "/electricity-service"  
    - endpoint: The API endpoint path
    - body: Dictionary with request parameters
    
    IMPORTANT: When calling call_transparency_api, you must pass each parameter separately:
    - method as string
    - service as string  
    - endpoint as string
    - body as dictionary
    
    Do NOT try to pass the entire API call object as a single parameter.
    
    Steps to follow:
    1. Parse the retrieval_state JSON
    2. For each API call in the array:
       - Extract method, service, endpoint, body
       - Call: call_transparency_api(method=method, service=service, endpoint=endpoint, body=body)
    3. Collect all responses
    4. Combine the "items" from all responses
    5. Return: compact_json:{{"items":[...combined_items...]}}
    
    Always start by examining what's in the retrieval_state.
    """
    
    return create_agent(
        llm,
        tools,
        system_prompt,
        members
    )