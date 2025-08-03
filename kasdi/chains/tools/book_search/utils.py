from typing import Dict, Any


def book_formatter(data: Dict[str, Any]) -> str:
    """
    Format a book document for output.
    """
    def remove_to_many_newlines(text: str) -> Any:
        if not isinstance(text, str):
            return text
        return "\n".join(line.strip() for line in text.splitlines() if line.strip())

    book_formated = ""

    for key, value in data.items():
        if value:
            book_formated += f"{key.capitalize().replace('_', ' ')}: {remove_to_many_newlines(value)}\n"

    return book_formated.strip()
