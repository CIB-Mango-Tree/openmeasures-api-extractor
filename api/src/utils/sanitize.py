from html import unescape
from typing import Union


def clean_text(text: Union[str, None]) -> Union[str, None]:
    if text is None:
        return text

    try:
        text = unescape(text).encode("latin1").decode("utf-8")

    except (UnicodeDecodeError, UnicodeEncodeError):
        text = text.replace("\u2019", "’")

    return text
