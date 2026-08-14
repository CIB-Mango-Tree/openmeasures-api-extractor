"""Validation of the create-query payload.

The regression these guard: when end_date failed its own validator it was absent from
info.data, and validate_start_date subscripted it directly. The KeyError escaped as a 500, so
the user got no message at all -- the endpoint only catches ValidationError.
"""

from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError

from src.validator import CreateQueryValidator

# Both dates must be at least six months old, so "valid" is well before that.
OLD = datetime.now() - timedelta(days=400)
RECENT = datetime.now() - timedelta(days=5)


def _payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "platform": "truth_social",
        "terms": [{"term": "mango", "modifier": "EQUAL"}],
        "timezone": "UTC",
        "end_date": OLD.isoformat(),
        "start_date": (OLD - timedelta(days=1)).isoformat(),
    }
    payload.update(overrides)

    return payload


def test_accepts_a_valid_payload() -> None:
    assert CreateQueryValidator.model_validate(_payload()) is not None


def test_recent_end_date_reports_validation_errors_not_a_crash() -> None:
    """This raised KeyError('end_date') before, which surfaced as a 500."""
    with pytest.raises(ValidationError) as caught:
        CreateQueryValidator.model_validate(
            _payload(end_date=RECENT.isoformat(), start_date=RECENT.isoformat())
        )

    fields = {error["loc"][0] for error in caught.value.errors()}

    assert "end_date" in fields


def test_recent_end_date_with_an_old_start_date_still_validates_cleanly() -> None:
    with pytest.raises(ValidationError) as caught:
        CreateQueryValidator.model_validate(_payload(end_date=RECENT.isoformat()))

    messages = [error["msg"] for error in caught.value.errors()]

    assert any("end date" in message for message in messages)


@pytest.mark.parametrize(
    "end_date,expected_type",
    [
        (None, "datetime_type"),
        ("not-a-date", "datetime_from_date_parsing"),
        ("", "datetime_from_date_parsing"),
    ],
)
def test_unusable_end_date_still_reports_an_end_date_error(
    end_date: object, expected_type: str
) -> None:
    """Skipping the cross-field comparison must not swallow end_date's own error."""
    with pytest.raises(ValidationError) as caught:
        CreateQueryValidator.model_validate(_payload(end_date=end_date))

    errors = {(error["loc"][0], error["type"]) for error in caught.value.errors()}

    assert ("end_date", expected_type) in errors


def test_omitted_end_date_is_reported_as_missing() -> None:
    payload = _payload()

    del payload["end_date"]

    with pytest.raises(ValidationError) as caught:
        CreateQueryValidator.model_validate(payload)

    assert ("end_date", "missing") in {
        (error["loc"][0], error["type"]) for error in caught.value.errors()
    }


def test_start_date_after_end_date_is_rejected() -> None:
    with pytest.raises(ValidationError) as caught:
        CreateQueryValidator.model_validate(
            _payload(start_date=(OLD + timedelta(days=1)).isoformat())
        )

    messages = [error["msg"] for error in caught.value.errors()]

    assert any("greater than the end date" in message for message in messages)


def test_invalid_timezone_is_rejected() -> None:
    with pytest.raises(ValidationError):
        CreateQueryValidator.model_validate(_payload(timezone="Not/AZone"))
