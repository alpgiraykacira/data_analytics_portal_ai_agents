from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from core.state import State
from core.node import agent_node
from core.router import process_router
from agent.query_agent import create_query_agent
from agent.retrieval_agent import create_retrieval_agent
from agent.api_agent import create_api_agent
from agent.process_agent import create_process_agent
from agent.analysis_agent import create_analysis_agent
from agent.visualization_agent import create_visualization_agent
from agent.report_agent import create_report_agent
from IPython.display import Image, display
from logger import log_performance

class Workflow:
    def __init__(self, llms):
        """
        Initialize the workflow class with language models and working directory.

        Args:
            llms (dict): Dictionary containing language model instances
        """
        self.llms = llms
        self.workflow = None
        self.memory = None
        self.graph = None
        self.members = ["Query", "Retrieval", "API", "Process", "Analysis", "Visualization", "Report"]
        self.agents = self.create_agents()
        self.setup_workflow()

    def create_agents(self):
        """Create all system agents"""
        # Get language models
        llm_fast = self.llms["llm_fast"]
        llm_reasoning = self.llms["llm_reasoning"]
        llm_low = self.llms["llm_low"]
        llm_mid = self.llms["llm_mid"]
        llm_high = self.llms["llm_high"]

        # Create agent dictionary
        agents = {
            "query_agent": create_query_agent(
                llm_mid,
                self.members,
        ),  "retrieval_agent": create_retrieval_agent(
                llm_mid,
                self.members,
        ),  "api_agent": create_api_agent(
                llm_low,
                self.members,
        ),  "process_agent": create_process_agent(
                llm_high
        ),  "analysis_agent": create_analysis_agent(
                llm_mid,
                self.members,
        ),  "visualization_agent": create_visualization_agent(
                llm_high,
                self.members,
        ),  "report_agent": create_report_agent(
                llm_low,
                self.members,
        )}

        return agents

    @log_performance
    def setup_workflow(self):
        """Set up the workflow graph"""
        self.workflow = StateGraph(State)

        # Add nodes
        self.workflow.add_node("Query",
                               lambda state: agent_node(state, self.agents["query_agent"], "query_agent"))
        self.workflow.add_node("Retrieval",
                               lambda state: agent_node(state, self.agents["retrieval_agent"], "retrieval_agent"))
        self.workflow.add_node("API",
                               lambda state: agent_node(state, self.agents["api_agent"], "api_agent"))
        self.workflow.add_node("Process",
                               lambda state: agent_node(state, self.agents["process_agent"], "process_agent"))
        self.workflow.add_node("Analysis",
                               lambda state: agent_node(state, self.agents["analysis_agent"], "analysis_agent"))
        self.workflow.add_node("Visualization",
                               lambda state: agent_node(state, self.agents["visualization_agent"], "visualization_agent"))
        self.workflow.add_node("Report",
                               lambda state: agent_node(state, self.agents["report_agent"], "report_agent"))

        # Add edges
        self.workflow.add_edge(START, "Query")
        self.workflow.add_edge("Query", "Retrieval")
        self.workflow.add_edge("Retrieval", "API")
        self.workflow.add_edge("API", "Process")

        self.workflow.add_conditional_edges(
            "Process",
            process_router,
            {
                "Analysis": "Analysis",
                "Visualization": "Visualization",
                "Report": "Report",
                "Process": "Process",
                END: END
            }
        )

        for member in ["Analysis", "Visualization", 'Report']:
            self.workflow.add_edge(member, "Process")

        # Compile workflow
        self.memory = MemorySaver()
        self.graph = self.workflow.compile()

        display(Image(self.graph.get_graph().draw_mermaid_png()))

    def get_graph(self):
        """Return the compiled workflow graph"""
        return self.graph