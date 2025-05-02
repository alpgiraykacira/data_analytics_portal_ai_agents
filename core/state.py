from langchain_core.messages import BaseMessage
from typing import Sequence, TypedDict


class State(TypedDict):
    """TypedDict for the entire state structure."""
    # The sequence of messages exchanged in the conversation
    messages: Sequence[BaseMessage]

    # The complete content of the research process
    process: str = ""

    # next process
    process_decision: str = ""

    # The current state of api calling
    api_state: str = ""

    # The current state of data visualization planning and execution
    visualization_state: str = ""

    # The content of the report sections being written
    report_section: str = ""

    # The identifier of the agent who sent the last message
    sender: str = ""