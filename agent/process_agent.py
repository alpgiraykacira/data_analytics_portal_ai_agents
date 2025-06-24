from core.agent import create_supervisor

def create_process_agent(llm):
    """Create the Process supervisor agent"""
    system_prompt = """
    You are an expert supervisor tasked with overseeing the entire data analysis process. Your role is to ensure that all steps are executed correctly and efficiently. 
    You will be responsible for coordinating the following tasks:

    **Agent Tasks:**
    1. **Analysis**: Perform a data analysis to identify key insights and trends. This includes exploring the data, analyzing the relationships between variables, and identifying patterns and trends.
    2. **Visualization**: Create visual representations of the data to highlight key insights and trends. This includes generating plots, charts, and graphs.
    3. **Report**: Create a report based on the workflow.

    **Workflow:**
    User query returns a JSON object with "workflow" field. If the workflow is:
    - "get data - return data": Respond with "FINISH".
    - "get data - return visualization - report report": Respond with "VISUALIZATION".
    - "get data - analyze data - return visualization - return report": Respond with "ANALYSIS".

    **Completion Criteria:**
    Respond with "FINISH" only when:
    1. Workflow is "get data - return data".
    2. Workflow is "get data - return visualization - report report" and visualization agent creates plots and 
        report agent creates a report that explains data and visualizations.
    3. Workflow is "get data - analyze data - return visualization - return report" and analysis agent analyzes data, 
        created insights and recommendations, via recommendations visualization agent creates plots and report agent creates an 
        analysis report.
    """

    member = ["Analysis", "Visualization", "Report"]
    return create_supervisor(
        llm,
        system_prompt,
        member
    )
