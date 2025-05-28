from typing import Annotated
from langchain.tools import tool
from PIL import Image
from logger import setup_logger

logger = setup_logger()

@tool
def read_file(file_path: Annotated[str, "./ by default"]) -> str:
    """
    Reads content from an existing file.

    Args:
        file_path (str): Path to the file to be read.

    Returns:
        str: Contents of the file.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return content
    except FileNotFoundError:
        return f"Error: File {file_path} not found."
    except Exception as e:
        return f"Error reading file: {str(e)}"

@tool
def write_file(file_path: Annotated[str, "./ by default"], content: Annotated[str, "Formatted report content"]) -> str:
    """
    Writes content to an existing file (overwrites).

    Args:
        file_path (str): Path to the file to write.
        content (str): Content to write to the file.

    Returns:
        str: Success message or error message.
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        return f"Content successfully written to {file_path}."
    except FileNotFoundError:
        return f"Error: File {file_path} not found."
    except Exception as e:
        return f"Error writing file: {str(e)}"

@tool
def save_image(
    image: Annotated[Image.Image, "PIL Image object"],
    file_path: Annotated[str, "Local file path"]
) -> str:
    """
    Saves a PIL Image to the specified local path and returns the path.
    """
    try:
        image.save(file_path)
        return f"Image saved to {file_path}"
    except Exception as e:
        return f"Error saving image: {e}"
