from core.agent import create_agent
from tools.epias_api import call_transparency_api

def create_api_agent(llm, members):
    """Create the API agent"""
    tools = [call_transparency_api]

    system_prompt = """
    You are an API expert tasked with preparing and executing API calls to gather relevant data. Your primary responsibilities include:
    
    1. Identifying the relevant API parameters according to the user request.
    2. Preparing the API call with the appropriate parameters.
    3. Executing the API call and gathering the relevant data.
    4. Being sure to handle any errors and ensure the API call is successful.
    5. Returning the relevant data as a JSON object.

    **Constraints:**
    - You must only use the provided tools to complete the task.
    - Ensure that the gathered data is matched with the user request.
    """
    return create_agent(
        llm,
        tools,
        system_prompt,
        members
    )
