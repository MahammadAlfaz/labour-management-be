from decimal import Decimal

from app.modules.wall_calculations.calculations import (
    compute_layers,
    compute_total_cost,
    sum_area,
    sum_measurements,
)
from app.modules.wall_calculations.schemas import LayerInput, MeasurementLine


def _measurement(raw_text: str, length: str, quantity: int) -> MeasurementLine:
    return MeasurementLine(raw_text=raw_text, length=Decimal(length), quantity=quantity)


def test_worked_example_from_spec_matches_exactly():
    """Regression anchor: the exact numbers from .claude/costcalculation.md."""
    measurements = [
        _measurement("31 1/4 - 1 pc", "31.25", 1),
        _measurement("12 1/2 - 1 pc", "12.50", 1),
        _measurement("10 1/4 - 1 pc", "10.25", 1),
        _measurement("31 3/4 - 3 pcs", "31.75", 3),
        _measurement("26 3/4 - 1 pc", "26.75", 1),
        _measurement("4 1/2 - 1 pc", "4.50", 1),
        _measurement("10 1/4 - 1 pc", "10.25", 1),
    ]

    total_measurement = sum_measurements(measurements)
    assert total_measurement == Decimal("190.75")

    layers = compute_layers(
        [
            LayerInput(height=Decimal("2.25"), breadth=Decimal("2.50")),
            LayerInput(height=Decimal("1.50"), breadth=Decimal("2.00")),
            LayerInput(height=Decimal("2.25"), breadth=Decimal("1.50")),
        ],
        total_measurement,
    )
    assert layers[0].area == Decimal("1072.96875")
    assert layers[1].area == Decimal("572.25")
    assert layers[2].area == Decimal("643.78125")

    total_area = sum_area(layers)
    assert total_area == Decimal("2289.00")

    total_cost = compute_total_cost(total_area, Decimal("27"))
    assert total_cost == Decimal("61803.00")


def test_sum_measurements_ignores_excluded_rows():
    measurements = [
        _measurement("kept", "10", 2),
        MeasurementLine(raw_text="excluded", length=Decimal("100"), quantity=1, included=False),
    ]

    assert sum_measurements(measurements) == Decimal("20")


def test_layer_area_preserves_full_decimal_precision():
    layers = compute_layers(
        [LayerInput(height=Decimal("1.125"), breadth=Decimal("1.0"))], Decimal("1")
    )

    assert layers[0].area == Decimal("1.125")


def test_total_cost_rounds_only_at_the_currency_boundary():
    # total_area x rate lands on a fraction of a paisa; cost must round to 2dp.
    total_area = Decimal("10.0055")
    cost = compute_total_cost(total_area, Decimal("10"))

    assert cost == Decimal("100.06")
