from pathlib import Path

def read_prompt(prompt_path: str) -> str:
    """
    Reads the prompt from a file.

    :param prompt_path: Path to the prompt file.
    :return: The content of the prompt file as a string.
    """
    prompt_path = Path(__file__).parent / "prompts" / prompt_path

    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

    with open(prompt_path, "r", encoding="utf-8") as file:
        return file.read()
