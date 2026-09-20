from decimal import ROUND_HALF_UP, Decimal

from bson.decimal128 import Decimal128

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


def to_decimal128(value: Decimal | float | int | str) -> Decimal128:
    """Convert to the BSON type Mongo actually stores.

    pymongo cannot encode a plain decimal.Decimal -- it raises InvalidDocument.
    Every money field must pass through this before an insert/update.
    """
    return Decimal128(to_money(value))


def from_decimal128(value: Decimal128 | None) -> Decimal | None:
    if value is None:
        return None
    return value.to_decimal()


def to_decimal128_exact(value: Decimal) -> Decimal128:
    """Convert to Decimal128 without quantizing to currency places.

    Use this for non-currency decimals (measurements, areas) where full
    precision must be preserved internally; use to_decimal128 for money.
    """
    return Decimal128(value)
