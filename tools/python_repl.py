from logger import setup_logger
from typing import Annotated, Dict
from langchain.tools import tool
from langchain_experimental.utilities import PythonREPL

# Set up a logger
logger = setup_logger()
# Initialize REPL with pre-imported libraries
repl = PythonREPL()
# Seed common libraries into the REPL namespace
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
repl.globals.update({
    "pd": pd,
    "np": np,
    "plt": plt
})

@tool
def execute_python_code(
    code: Annotated[str, "Python code to execute in REPL"]
) -> Annotated[str, "Execution result or error message"]:
    """
    Executes Python code in a REPL environment and returns structured results.

    Returns result string:
        result: str
    """
    result = repl.run(code)
    return result
