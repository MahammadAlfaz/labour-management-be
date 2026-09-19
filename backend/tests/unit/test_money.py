from decimal import Decimal

from app.core.money import to_money, zero


def test_to_money_rounds_to_two_places():
    assert to_money("750") == Decimal("750.00")
    assert to_money("750.005") == Decimal("750.01")


def test_to_money_accepts_decimal():
    assert to_money(Decimal("199.999")) == Decimal("200.00")


def test_zero_is_two_place_decimal():
    assert zero() == Decimal("0.00")
