from langchain_core.messages import AIMessage
from core.state import State
from logger import setup_logger, log_performance
from langchain.agents import AgentExecutor
from typing import Dict, Any
import re
import json

logger = setup_logger("logs/node.log")

def clean_agent_string(s: str) -> str:
    # 1) Kod bloğu işaretlerini kaldırın (```), eğer varsa
    s = s.replace('```', '')
    # 2) Literal "\n" ve "\'" dizilerini silin
    s = s.replace(r'\n', '')
    s = s.replace(r"\'", "'")
    # 3) Geri kalan ters eğik çizgileri isteğe bağlı kaldırın
    s = s.replace('\\', '')
    # 4) Tüm normal boşluk karakterlerini kaldırın
    s = re.sub(r'\s+', '', s)
    return s

def manage_state_size(
    state: Dict[str, Any],
    max_messages: int = 10,
) -> Dict[str, Any]:
    """
    Manage the state size to prevent context length issues.
    - Keeps only the most recent `max_messages` in `state['messages']`.
    """
    if "messages" in state and len(state["messages"]) > max_messages:
        state["messages"] = state["messages"][-max_messages:]
        logger.info(f"State messages truncated to most recent {max_messages}")

    return state

@log_performance
def agent_node(state: State, agent: AgentExecutor, name: str) -> State:
    """
    Process an agent's action and update the state accordingly.
    """
    logger.info(f"Processing agent: {name}")

    # Manage state size before invoking the agent
    state = manage_state_size(state)

    try:
        result = agent.invoke(state)
        logger.debug(f"Agent {name} result: {result}")

        output = result["output"] if isinstance(result, dict) and "output" in result else str(result)

        ai_message = AIMessage(content=output, name=name)
        if "messages" not in state:
            state["messages"] = []
        state["messages"].append(ai_message)
        state["sender"] = name

        if name == "process_agent":
            state["process_state"] = ai_message
            state["process_decision"] = ai_message
            logger.info("Process decision and state updated")
        elif name == "query_agent":
            state["query_state"] = ai_message
            logger.info("Query state updated")
        elif name == "retrieval_agent":
            state["retrieval_state"] = ai_message
            logger.info("Retrieval state updated")
        elif name == "api_agent":
            ai_message.content = clean_agent_string(ai_message.content)
            state["api_state"] = ai_message
            logger.info("API state updated")
        elif name == "analysis_agent":
            state["analysis_state"] = ai_message
            logger.info("Analysis state updated")
        elif name == "visualization_agent":
            state["visualization_state"] = ai_message
            logger.info("Visualization state updated")
        elif name == "report_agent":
            state["report_state"] = ai_message
            logger.info("Report state updated")

        logger.info(f"Agent {name} processing completed")
        return state
    except Exception as e:
        logger.error(f"Error occurred while processing agent {name}: {str(e)}", exc_info=True)
        error_message = AIMessage(content=f"Error: {str(e)}", name=name)
        # Preserve existing state and add error message
        if "messages" not in state:
            state["messages"] = []
        state["messages"].append(error_message)
        return state  # Return the original state with error message added