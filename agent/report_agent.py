from core.agent import create_agent
from tools.file_manager import read_file

def create_report_agent(llm, members):
    """Create the report agent"""
    tools = [read_file]

    system_prompt = """
    You are an expert report generator tasked with creating comprehensive reports based on analysis process.
    Your primary responsibilities include:

    1. Creating a report based on the workflow. Process agent will provide the content of the report.
    2. If there are any errors or issues during the report generation, handle them gracefully and provide appropriate feedback.

    **Constraints:**
    - DO NOT use read_file tool. It is only for tool assignment.
    - DO NOT include response data in the report.
    - Respond in same langugage as the input query.

    **Output Format:**
    {{
        "report": "report content here",
    }}
    """
    return create_agent(
        llm,
        tools,
        system_prompt,
        members
    )
