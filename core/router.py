from core.state import State
from typing import Literal, Union, Dict, List, Optional
from langchain_core.messages import AIMessage
from langgraph.graph import END
import logging
import json

logger = logging.getLogger(__name__)

# Define types for node routing
NodeType = Literal['APICalling', 'Process', 'Visualization', 'Report']


def process_router(state: State) -> NodeType:
    """
    Route based on the process decision in the state.

    Args:
        state (State): The current state of the system.

    Returns:
        NodeType: The next process node to route to based on the process decision.
    """
    logger.info("Entering process_router")
    process_decision: Union[AIMessage, Dict, str, None] = state.get("process_decision", "")

    decision_str: str = ""

    try:
        if isinstance(process_decision, AIMessage):
            logger.debug("Process decision is an AIMessage")
            try:
                # First try to parse as JSON
                decision_dict = json.loads(process_decision.content.replace("'", '"'))
                decision_str = str(decision_dict.get('next', ''))
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract decision from text
                content = process_decision.content.upper()
                if "NEXT: REPORT" in content:
                    decision_str = "Report"
                elif "NEXT: API" in content:
                    decision_str = "API"
                elif "NEXT: VISUALIZATION" in content:
                    decision_str = "Visualization"
                else:
                    decision_str = process_decision.content
        elif isinstance(process_decision, dict):
            decision_str = str(process_decision.get('next', ''))
        else:
            decision_str = str(process_decision)
    except Exception as e:
        logger.error(f"Error processing decision: {e}")
        decision_str = ""

    # Define valid decisions
    valid_decisions = {"API", "Visualization", "Report", "Process"}

    logger.info(f"Processed decision: {decision_str}")

    if decision_str.upper() == "FINISH":
        logger.info("Process decision is FINISH. Ending process.")
        return END

    if decision_str in valid_decisions:
        logger.info(f"Valid process decision: {decision_str}")
        return decision_str

    # Default to "Process" if decision is invalid or empty
    logger.warning(f"Invalid or empty process decision: {decision_str}. Defaulting to 'Process'.")
    return "Process"