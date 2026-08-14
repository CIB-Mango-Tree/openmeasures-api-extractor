QUOTE = '"'


def quote_term(value: str) -> str:
    """Wraps a multi-word term in quotes so the API matches it as a phrase.

    The query is sent with querytype=boolean_content, which treats a bare `data center` as two
    separate tokens -- so a search for that phrase returned every post containing just "data".
    Users had to add quotes themselves to get a phrase match.

    Single words are returned untouched, and a term the user already quoted is left as-is rather
    than being double-quoted. Users who do want the words matched separately can add a second
    search field, which is what the modifiers are for.
    """
    stripped = value.strip()

    if not stripped:
        return stripped

    if (
        len(stripped) > 1
        and stripped.startswith(QUOTE)
        and stripped.endswith(QUOTE)
    ):
        return stripped

    if not any(character.isspace() for character in stripped):
        return stripped

    escaped = stripped.replace(QUOTE, f"\\{QUOTE}")

    return f"{QUOTE}{escaped}{QUOTE}"
