from html import unescape


def clean_text(text: str | None) -> str | None:
    if text is None:
        return text

    try:
        text = unescape(text).encode("latin1").decode("utf-8")

    except (UnicodeDecodeError, UnicodeEncodeError):
        text = text.replace("\u2019", "’")

    return text
