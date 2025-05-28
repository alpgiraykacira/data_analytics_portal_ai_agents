from langchain_core.messages import AIMessage
from core.state import State
from logger import setup_logger
from langchain.agents import AgentExecutor
from typing import Dict, Any

logger = setup_logger()

def truncate_content(content: str, max_length: int = 10000) -> str:
    """Truncate content to a maximum length."""
    if len(content) > max_length:
        return content[:max_length] + "... [content truncated]"
    return content

def manage_state_size(
    state: Dict[str, Any],
    max_messages: int = 10,
    max_text_length: int = 20000
) -> Dict[str, Any]:
    """
    Manage the state size to prevent context length issues.
    - Keeps only the most recent `max_messages` in `state['messages']`.
    - Truncates any other string fields longer than `max_text_length`.
    """
    # 1) Truncate chat history
    if "messages" in state and len(state["messages"]) > max_messages:
        state["messages"] = state["messages"][-max_messages:]
        logger.info(f"State messages truncated to most recent {max_messages}")

    # 2) Truncate long text fields
    for key, val in state.items():
        if key != "messages" and isinstance(val, str) and len(val) > max_text_length:
            state[key] = truncate_content(val, max_text_length)
            logger.info(f"State field '{key}' truncated to {max_text_length} chars")

    return state


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