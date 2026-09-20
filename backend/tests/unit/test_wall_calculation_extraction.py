from decimal import Decimal

import pytest

from app.core.gemini_client import GeminiError
from app.modules.wall_calculations.extraction import _parse_response
from app.modules.wall_calculations.schemas import MeasurementConfidence


def test_parses_clean_json_array():
    text = (
        '[{"raw_text": "31 1/4 - 1 pc", "length_decimal": 31.25, '
        '"quantity": 1, "confidence": "high"}]'
    )

    rows, warnings = _parse_response(text)

    assert warnings == []
    assert len(rows) == 1
    assert rows[0].length == Decimal("31.25")
    assert rows[0].quantity == 1
    assert rows[0].confidence == MeasurementConfidence.HIGH


def test_strips_markdown_code_fence():
    text = '```json\n[{"raw_text": "x", "length_decimal": 10, "quantity": 2}]\n```'

    rows, _warnings = _parse_response(text)

    assert len(rows) == 1
    assert rows[0].length == Decimal("10")


def test_defaults_missing_confidence_to_high():
    text = '[{"raw_text": "x", "length_decimal": 5, "quantity": 1}]'

    rows, _warnings = _parse_response(text)

    assert rows[0].confidence == MeasurementConfidence.HIGH


def test_marks_explicit_low_confidence():
    text = '[{"raw_text": "x", "length_decimal": 5, "quantity": 1, "confidence": "low"}]'

    rows, _warnings = _parse_response(text)

    assert rows[0].confidence == MeasurementConfidence.LOW


def test_skips_unreadable_rows_with_a_warning_instead_of_guessing():
    text = (
        '[{"raw_text": "good", "length_decimal": 5, "quantity": 1}, '
        '{"raw_text": "bad", "length_decimal": "not-a-number", "quantity": 1}]'
    )

    rows, warnings = _parse_response(text)

    assert len(rows) == 1
    assert rows[0].raw_text == "good"
    assert len(warnings) == 1
    assert "Line 2" in warnings[0]


def test_negative_or_zero_values_are_skipped_not_guessed():
    text = '[{"raw_text": "bad", "length_decimal": 0, "quantity": 1}]'

    rows, warnings = _parse_response(text)

    assert rows == []
    assert len(warnings) == 1


def test_empty_array_warns_that_nothing_was_detected():
    rows, warnings = _parse_response("[]")

    assert rows == []
    assert warnings == ["No measurements were detected in the image"]


def test_non_json_response_raises_gemini_error():
    with pytest.raises(GeminiError):
        _parse_response("Sorry, I can't help with that.")


def test_non_array_json_raises_gemini_error():
    with pytest.raises(GeminiError):
        _parse_response('{"raw_text": "x"}')
