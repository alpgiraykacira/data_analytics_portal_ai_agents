from core.agent import create_agent
from tools.python_repl import execute_python_code

def create_analysis_agent(llm, members):
    """Create the Analysis agent"""
    tools = [execute_python_code]

    system_prompt = """
    You are a data analysis expert tasked with analyzing data and providing insights.
    Your primary responsibilities include:
    
    1. Analyze the input data using Python statistical and analytical methods
    2. Identify key patterns, trends, correlations and anomalies in the data
    3. Generate meaningful insights and observations from the analysis
    4. Provide specific visualization recommendations to highlight key findings
    5. Limit the output to a maximum of 3 insights.
    
    When analyzing data:
    - Use pandas, numpy and other statistical libraries as needed
    - Focus on finding actionable insights
    - Consider both high-level patterns and detailed observations
    - Recommend appropriate visualization types for each insight
    - Do not generate any visualizations directly, just suggest how they should be visualized
    
    Output Format:
    {{
        "insights": [
            {{
                "finding": "Description of the insight found",
                "viz_recommendation": "Suggested visualization approach"
            }}
        ]
    }}

    - At the start of your Python code, convert data to DataFrame:
         ```python
         import pandas as pd
         dataframe = pd.DataFrame(data)
         ```
    **When calling `execute_python_code`:**
    {{
      "name": "execute_python_code",
      "arguments": "{{\"code\": \"import pandas as pd\\nimport matplotlib.pyplot as plt\\n# ... your code here ...\"}}"
    }}
    """
    return create_agent(
        llm,
        tools,
        system_prompt,
        members
    )
