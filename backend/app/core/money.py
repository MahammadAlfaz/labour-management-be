from decimal import ROUND_HALF_UP, Decimal

TWO_PLACES = Decimal("0.01")


def to_money(value: Decimal | float | int | str) -> Decimal:
    """Convert a raw value into a Decimal rounded to 2 places (currency-safe).

    Float input is accepted only for convenience at API boundaries where a
    client sends a JSON number; it is immediately quantized so no float
    imprecision propagates into stored or calculated amounts.
    """
    return Decimal(str(value)).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def zero() -> Decimal:
    return Decimal("0.00")
