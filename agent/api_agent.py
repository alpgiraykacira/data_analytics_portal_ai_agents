from core.agent import create_agent
from tools.epias_api import call_transparency_api

def create_api_agent(llm, members):
    """Create the API agent"""
    tools = [call_transparency_api]

    system_prompt = """
        You are an API expert tasked with preparing and executing API calls to gather relevant data.
        Your primary responsibilities include:

        1. Parse the retrieval_state to extract API call specifications.
        2. Execute the call_transparency_api tool with the exact method, service, endpoint, and body parameters.
        3. For multiple API calls, execute them in sequence and combine the results appropriately.
        4. For multiple API calls, if a parameter comes from the previous API call, use its value.
        5. Handle any API errors gracefully and retry with adjusted parameters if necessary.

        **Constraints:**
        - Only use the provided call_transparency_api tool.
        - Always use "/electricity-service" as the service parameter.
        - Do not change or process the response data.
        - Return data in clean, structured JSON.

        **Output Format:**
        ```json
        {{
            "response": <unchanged_response_data_from_API>,
        }}
        ```
        """
    return create_agent(
        llm,
        tools,
        system_prompt,
        members
    )
