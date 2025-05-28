from core.agent import create_agent
from tools.file_manager import read_file, write_file

def create_report_agent(llm, members):
    """Create the report agent"""
    tools = [read_file, write_file]

    system_prompt = """
    You are an expert report generator tasked with creating comprehensive reports based on analysis process.
    Your primary responsibilities include:

    1. Creating a report based on the workflow. Process agent will provide the content of the report.
    2. Using the read_file and write_file tools to read and write files as needed.
    4. If there are any errors or issues during the report generation, handle them gracefully and provide appropriate feedback.
    5. Save the report in .txt format and return the file path.

    **Constraints:**
    - You must only use the provided tools to complete the task.
    - DO NOT include response data in the report.

    **Output Format:**
    {{
        "report": {{
            "file_path": <file_path>,
            "description": <description>
        }}
    }}
    """
    return create_agent(
        llm,
        tools,
        system_prompt,
        members
    )
