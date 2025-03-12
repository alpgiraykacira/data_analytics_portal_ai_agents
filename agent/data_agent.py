from agents import Agent, FileSearchTool
from tool.epias_api import transparency_agent

data_agent = Agent(
    name="EPİAŞ API Information Retrieval Agent",
    instructions=
    """
    You retrieve information from EPİAŞ documentation and get data from EPİAŞ API.
    User can ask for any information related to electricity.
    Your job is to analyse the user input and decide which endpoint(s) to use and get data via that information.
    You will need to use the File Search tool to find the relevant information in the vector_store.
    You will use the transparency_agent function to get the data.
    The example endpoint usage is as follows:
        data = transparency_agent(
            method="GET",
            service="electricity-service",
            endpoint="/v1/main/province-list",
            body={}
        )
    """,
    model="gpt-4o-mini",
    tools=[
        FileSearchTool(
            vector_store_ids=["vs_67d19a813390819196cfc2ef342a662d"]
        ),
        transparency_agent
    ]
)