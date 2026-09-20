from decimal import Decimal

from app.core.money import to_money
from app.modules.wall_calculations.schemas import LayerInput, LayerOut, MeasurementLine


def sum_measurements(measurements: list[MeasurementLine]) -> Decimal:
    """Total Measurement = SUM(Length x Quantity) over included rows."""
    total = Decimal("0")
    for measurement in measurements:
        if not measurement.included:
            continue
        total += measurement.length * measurement.quantity
    return total


def compute_layers(layers: list[LayerInput], total_measurement: Decimal) -> list[LayerOut]:
    """Layer Area = Total Measurement x Height x Breadth, at full precision."""
    return [
        LayerOut(
            label=layer.label,
            height=layer.height,
            breadth=layer.breadth,
            area=total_measurement * layer.height * layer.breadth,
        )
        for layer in layers
    ]


def sum_area(layers: list[LayerOut]) -> Decimal:
    """Total Area = sum of all layer areas, at full precision."""
    total = Decimal("0")
    for layer in layers:
        total += layer.area
    return total


def compute_total_cost(total_area: Decimal, rate_per_sqft: Decimal) -> Decimal:
    """Total Cost = Total Area x Rate, rounded once at the currency boundary."""
    return to_money(total_area * rate_per_sqft)
