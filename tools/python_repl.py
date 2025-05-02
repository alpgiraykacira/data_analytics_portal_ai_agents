from typing import Annotated
from langchain_core.tools import tool
from logger import setup_logger
from langchain_experimental.utilities import PythonREPL

logger = setup_logger()

repl = PythonREPL()

@tool
def execute_python_code(code: Annotated[str, "Python code to execute"]):
    """
    Executes Python code passed as a string and prints its output.

    The function takes a string containing Python code and attempts to execute
    it using a REPL (Read-Eval-Print Loop) interface. It logs the process,
    including the input code, the result of execution, or any errors that occur.

    Args:
        code (str): Python code to execute.
    """
    try:
        logger.info(f"Executing Python code: {code}")
        result = repl.run(code)
    except Exception as e:
        logger.error(f"Error executing Python code: {str(e)}")
        return {"error": str(e)}
    result_str = f"Successfully executed Python code.\nStdout:\n{result}"
    return result_str