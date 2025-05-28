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
) -> Annotated[Dict[str, object], "Execution result with stdout, stderr, and success flag"]:
    """
    Executes Python code in a REPL environment and returns structured results.

    Returns a dict with:
    - success: bool indicating if execution succeeded
    - stdout: standard output from the code
    - stderr: error message if an exception occurred
    """
    try:
        # Run the code and capture stdout
        stdout = repl.run(code)
        return {"success": True, "stdout": stdout, "stderr": ""}
    except Exception as e:
        # Log error and return structured error
        logger.error(f"Error in execute_python_code: {e}", exc_info=True)
        return {"success": False, "stdout": "", "stderr": str(e)}
