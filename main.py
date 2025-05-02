import dotenv
from logger import setup_logger
from langchain_core.messages import HumanMessage
from core.workflow import Workflow
from core.llm import LLM

dotenv.load_dotenv()

class DataAnalyticsPortal:
    def __init__(self):
        self.logger = setup_logger()
        self.llm = LLM()
        self.workflow = Workflow(
            llms=self.llm.get_models(),
        )

    def run(self, user_input: str) -> None:
        """Run the system with user input"""
        graph = self.workflow.get_graph()
        events = graph.stream(
            {
                "messages": [HumanMessage(content=user_input)],
                "process_decision": "",
                "process": "",
                "api_state": "",
                "visualization_state": "",
                "report_section": "",
                "last_sender": "",
            },
            {"configurable": {"thread_id": "1"}, "recursion_limit": 20},
            stream_mode="values",
            debug=False
        )

        for event in events:
            message = event["messages"][-1]
            if isinstance(message, tuple):
                print(message, end='', flush=True)
            else:
                message.pretty_print()


def main():
    system = DataAnalyticsPortal()

    user_input = '''
    Make an API call with following parameters:
        - method="POST",
        - service="electricity-service",
        - endpoint="/v1/markets/dam/data/mcp",
        - body={
            "startDate": "2024-01-01T00:00:00+03:00",
            "endDate": "2024-01-02T00:00:00+03:00"
}
    Use machine learning to perform data analysis and write complete graphical reports
    '''
    system.run(user_input)


if __name__ == "__main__":
    main()
