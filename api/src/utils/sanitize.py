from html import unescape


def clean_text(text: str | None) -> str | None:
    """Unescapes HTML entities and repairs mojibake (UTF-8 bytes previously read as latin-1).

    The unescape and the mojibake repair are separate steps on purpose. Previously both happened
    in one expression inside a try, so any text containing a non-ASCII character raised on the
    latin-1 round trip and the except branch returned the *original* string -- discarding the
    unescape too. Entities like &amp; survived into exports on every non-ASCII post.
    """
    if text is None:
        return None

    text = unescape(text)

    try:
        return text.encode("latin1").decode("utf-8")

    # Not mojibake, just ordinary text that latin-1 cannot represent (or is not valid UTF-8
    # once re-encoded). The unescaped text is already correct.
    except (UnicodeDecodeError, UnicodeEncodeError):
        return text
