from langchain_core.messages import AIMessage
from core.state import State
import logging
from langchain.agents import AgentExecutor

logger = logging.getLogger(__name__)

def agent_node(state: State, agent: AgentExecutor, name: str) -> State:
    """
    Process an agent's action and update the state accordingly.
    """
    logger.info(f"Processing agent: {name}")
    try:
        # Initialize states if they don't exist
        if "process_state" not in state:
            state["process_state"] = None
        if "report_state" not in state:
            state["report_state"] = None

        result = agent.invoke(state)
        logger.debug(f"Agent {name} result: {result}")

        output = result["output"] if isinstance(result, dict) and "output" in result else str(result)

        ai_message = AIMessage(content=output, name=name)
        if "messages" not in state:
            state["messages"] = []
        state["messages"].append(ai_message)
        state["sender"] = name

        if name == "process_agent":
            state["process_decision"] = ai_message
            state["process_state"] = ai_message  # Add process state update
            logger.info("Process decision and state updated")
        elif name == "api_agent" and not state.get("api_state"):
            state["api_state"] = ai_message
            logger.info("API state updated")
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