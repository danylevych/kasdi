
def make_telegram_safe_message(text: str) -> str:
    return text.replace("**", "*")
