from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain_openai import ChatOpenAI
from typing import List
from langchain.tools import tool
import os
from logger import setup_logger

logger = setup_logger("logs/agent.log")

def create_agent(
        llm: ChatOpenAI,
        tools: list[tool],
        system_message: str,
        members: list[str],
) -> AgentExecutor:
    """
    Create an agent with the given language model, tools, system message, and team members.

    Parameters:
        llm (ChatOpenAI): The language model to use for the agent.
        tools (list[tool]): A list of tools the agent can use.
        system_message (str): A message defining the agent's role and tasks.
        members (list[str]): A list of team member roles for collaboration.

    Returns:
        AgentExecutor: An executor that manages the agent's task execution.
    """

    logger.info("Creating agent")

    # Prepare the tools names and team members for the system prompt
    tool_names = ", ".join([tool.name for tool in tools])
    team_members_str = ", ".join(members)

    # Create the system prompt for the agent
    system_prompt = (
        "You are a specialized AI assistant in a data analysis team. "
        "Your role is to complete specific tasks in the analysis of EPİAŞ electricity data. "
        "Use the provided tools to make progress on your task. "
        "If you can't fully complete a task, explain what you've done and what's needed next. "
        "Always aim for accurate and clear outputs. "
        f"You have access to the following tools: {tool_names}. "
        f"Your specific role: {system_message}\n"
        "Work autonomously according to your specialty, using the tools available to you. "
        "Do not ask for clarification. "
        "Your other team members (and other teams) will collaborate with you based on their specialties. "
        f"You are chosen for a reason! You are one of the following team members: {team_members_str}.\n"
    )

    # Define the prompt structure with placeholders for dynamic content
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="messages"),
        ("ai", "process_state: {process_state}"),
        ("ai", "process_decision: {process_decision}"),
        ("ai", "query_state: {query_state}"),
        ("ai", "retrieval_state: {retrieval_state}"),
        ("ai", "api_state: {api_state}"),
        ("ai", "analysis_state: {analysis_state}"),
        ("ai", "visualization_state: {visualization_state}"),
        ("ai", "report_state: {report_state}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    # Create the agent using the defined prompt and tools
    agent = create_openai_functions_agent(llm=llm, tools=tools, prompt=prompt)

    logger.info("Agent created successfully")

    # Return an executor to manage the agent's task execution
    return AgentExecutor.from_agent_and_tools(agent=agent, tools=tools, verbose=False, handle_parsing_errors=True)


def create_supervisor(llm: ChatOpenAI, system_prompt: str, members: list[str]) -> AgentExecutor:
    # Log the start of supervisor creation
    logger.info("Creating supervisor")

    # Define options for routing, including FINISH and team members
    options = ["FINISH"] + members

    # Define the function for routing and task assignment
    function_def = {
        "name": "route",
        "description": "Select the next role and assign a task.",
        "parameters": {
            "title": "routeSchema",
            "type": "object",
            "properties": {
                "next": {
                    "title": "Next",
                    "anyOf": [
                        {"enum": options},
                    ],
                },
                "task": {
                    "title": "Task",
                    "type": "string",
                    "description": "The task to be performed by the selected agent"
                }
            },
            "required": ["next", "task"],
        },
    }

    # Create the prompt template
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
            (
                "system",
                "Given the conversation above, who should act next? "
                "Or should we FINISH? Select one of: {options}. "
                "Additionally, specify the task that the selected role should perform."
            ),
        ]
    ).partial(options=str(options), team_members=", ".join(members))

    # Log successful creation of supervisor
    logger.info("Supervisor created successfully")

    # Return the chained operations
    return (
            prompt
            | llm.bind_functions(functions=[function_def], function_call="route")
            | JsonOutputFunctionsParser()
    )

logger.info("Agent creation module initialized")