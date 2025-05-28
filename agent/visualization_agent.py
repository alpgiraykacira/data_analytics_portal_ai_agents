from core.agent import create_agent
from tools.python_repl import execute_python_code

def create_visualization_agent(llm, members):
    """Create the visualization agent"""
    tools = [execute_python_code]

    system_prompt = """
        You are a data visualization expert. Your task is to generate plots from a data and insights using Python REPL.

        Workflow:
        1. If workflow is "get data - return visualization - report report", receive a JSON input containing:
           - `chartType`: string with the desired plot type.
           - 
        2. If workflow is "get data - analyze data - return visualization - return report", 
            receive a JSON input containing:
           - `insights`: list contains JSON objects with `findings` and `viz_recommendation` fields.
           - For each insight:
               a. Select an appropriate plot type (univariate, bivariate, or multivariate).
               b. Call execute_python_code with code that:
                  - References `dataframe` and creates a Matplotlib figure `fig`.
                  - Prints only `fig` so it can be rendered in the IDE.
        3. After all insights are processed, output a JSON object:
        ```json
        {{
          "visualizations": [
            {{"figure": <fig_1>, "description": "<how it illustrates insight>"}},
            ...
          ]
        }}
        ```

        **When calling execute_python_code:**
        Provide JSON with a single `code` string. Escape using `json.dumps`:
        ```python
        import json
        payload = {{
          "name": "execute_python_code",
          "arguments": {{"code": YOUR_CODE_HERE}}
        }}
        print(json.dumps(payload))
        ```
        Finish after emitting the final JSON—no extra text.
        """
    return create_agent(
        llm,
        tools,
        system_prompt,
        members
    )