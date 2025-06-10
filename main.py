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
                "process_state": "",
                "process_decision": "",
                "query_state": "",
                "retrieval_state": "",
                "api_state": "",
                "analysis_state": "",
                "visualization_state": "",
                "report_state": "",
                "sender": "",
            },
            {"configurable": {"thread_id": "1"}, "recursion_limit": 30},
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
    Intent: "EDA". 2025 yılı Mayıs ayının ilk 2 günü her saat için piyasa takas fiyatının (TRY) 3000+ olma durumunu inceleyeceğim. 0-23 arası her bir saatte kaç tane 3000+ fiyat varsa bunu bir grafik şeklinde göster.
    '''
    system.run(user_input)


if __name__ == "__main__":
    main()
