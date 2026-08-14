"""Phrase handling for search terms.

Reported as: a search for `data center` only returned posts containing "data", and users had to
add quotes themselves. querytype=boolean_content treats a bare multi-word value as separate
tokens, so multi-word terms are quoted for them.
"""

import pytest

from src.utils.search import quote_term


@pytest.mark.parametrize(
    "value,expected",
    [
        ("data center", '"data center"'),
        ("  data center  ", '"data center"'),
        ("election integrity report", '"election integrity report"'),
        # Single words must be untouched, or every existing query changes meaning.
        ("mango", "mango"),
        ("", ""),
        ("   ", ""),
        # Already quoted by the user: quoting again would search for a literal quote character.
        ('"data center"', '"data center"'),
        # Inner quotes are escaped rather than terminating the phrase early.
        ('say "hi" now', '"say \\"hi\\" now"'),
    ],
)
def test_quote_term(value: str, expected: str) -> None:
    assert quote_term(value) == expected


def test_query_term_property_quotes_each_term_independently() -> None:
    from src.db.models import Query, QueryTerm

    query = Query()
    query.terms = [
        QueryTerm(term="data center", modifier="EQUAL", position=1),
        QueryTerm(term="mango", modifier="AND", position=2),
        QueryTerm(term="supply chain", modifier="OR", position=3),
    ]

    # Modifiers stay outside the quotes so they are still read as boolean operators.
    assert query.term == '"data center" AND mango OR "supply chain"'
