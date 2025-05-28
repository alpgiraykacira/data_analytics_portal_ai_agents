from core.state import State
from typing import Literal, Union, Dict
from langchain_core.messages import AIMessage
from langgraph.graph import END
from logger import setup_logger
import json
import ast

logger = setup_logger()

# Define types for node routing
NodeType = Literal['Process', 'Analysis', 'Visualization', 'Report', 'FINISH']


def process_router(state: State) -> NodeType:
    """
    Route based on the process decision in the state.

    Args:
        state (State): The current state of the system.

    Returns:
        NodeType: The next process node to route to based on the process decision.
    """
    logger.info("Entering process_router")
    process_decision = state.get("process_decision", "")

    decision_str: str = ""

    try:
        # Handle AIMessage content first
        if isinstance(process_decision, AIMessage):
            logger.debug("Process decision is an AIMessage")
            content = process_decision.content.strip()
            # Attempt JSON parsing
            try:
                decision_dict = json.loads(content.replace("'", '"'))
                decision_str = str(decision_dict.get('next', ''))
            except json.JSONDecodeError:
                # Attempt Python literal evaluation for dict-like strings
                try:
                    decision_dict = ast.literal_eval(content)
                    decision_str = str(decision_dict.get('next', ''))
                except Exception:
                    # Fallback to keyword detection
                    upper = content.upper()
                    if "NEXT: ANALYSIS" in upper:
                        decision_str = "Analysis"
                    elif "NEXT: VISUALIZATION" in upper:
                        decision_str = "Visualization"
                    elif "NEXT: REPORT" in upper:
                        decision_str = "Report"
                    elif "NEXT: FINISH" in upper or upper == "FINISH":
                        decision_str = "FINISH"
                    else:
                        decision_str = content
        # Handle plain dict
        elif isinstance(process_decision, dict):
            decision_str = str(process_decision.get('next', ''))
        else:
            decision_str = str(process_decision)
    except Exception as e:
        logger.error(f"Error processing decision: {e}")
        decision_str = ""

    valid_decisions = {"Analysis", "Visualization", "Report", "Process"}
    logger.info(f"Processed decision: {decision_str}")

    # Handle FINISH explicitly
    if decision_str.upper() == "FINISH":
        logger.info("Process decision is FINISH. Ending process.")
        return END

    if decision_str in valid_decisions:
        logger.info(f"Valid process decision: {decision_str}")
        return decision_str  # type: ignore

    # Default to "Process"
    logger.warning(f"Invalid or empty process decision: {decision_str}. Defaulting to 'Process'.")
    return "Process"  # type: ignore
