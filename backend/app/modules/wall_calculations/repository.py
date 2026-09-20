from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from bson import ObjectId

from app.core.money import from_decimal128, to_decimal128, to_decimal128_exact
from app.db import get_database
from app.modules.wall_calculations.schemas import (
    LayerOut,
    MeasurementLine,
    WallCalculationOut,
)


def _measurement_to_doc(measurement: MeasurementLine) -> dict:
    return {
        "raw_text": measurement.raw_text,
        "length": to_decimal128_exact(measurement.length),
        "quantity": measurement.quantity,
        "confidence": measurement.confidence.value,
        "included": measurement.included,
    }


def _measurement_from_doc(doc: dict) -> MeasurementLine:
    return MeasurementLine(
        raw_text=doc["raw_text"],
        length=from_decimal128(doc["length"]),
        quantity=doc["quantity"],
        confidence=doc["confidence"],
        included=doc["included"],
    )


def _layer_to_doc(layer: LayerOut) -> dict:
    return {
        "label": layer.label,
        "height": to_decimal128_exact(layer.height),
        "breadth": to_decimal128_exact(layer.breadth),
        "area": to_decimal128_exact(layer.area),
    }


def _layer_from_doc(doc: dict) -> LayerOut:
    return LayerOut(
        label=doc.get("label"),
        height=from_decimal128(doc["height"]),
        breadth=from_decimal128(doc["breadth"]),
        area=from_decimal128(doc["area"]),
    )


def _to_out(doc: dict) -> WallCalculationOut:
    return WallCalculationOut(
        id=str(doc["_id"]),
        site_id=doc.get("site_id"),
        title=doc.get("title"),
        source_image_path=doc.get("source_image_path"),
        measurements=[_measurement_from_doc(m) for m in doc.get("measurements", [])],
        total_measurement=from_decimal128(doc["total_measurement"]),
        layers=[_layer_from_doc(layer) for layer in doc["layers"]],
        total_area=from_decimal128(doc["total_area"]),
        rate_per_sqft=from_decimal128(doc["rate_per_sqft"]),
        total_cost=from_decimal128(doc["total_cost"]),
        created_by=doc["created_by"],
        updated_by=doc["updated_by"],
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )


class WallCalculationRepository:
    def __init__(self) -> None:
        self._collection = get_database().wall_calculations

    async def create(
        self,
        *,
        site_id: str | None,
        title: str | None,
        source_image_path: str | None,
        measurements: list[MeasurementLine],
        layers: list[LayerOut],
        total_measurement: Decimal,
        total_area: Decimal,
        rate_per_sqft: Decimal,
        total_cost: Decimal,
        admin_id: str,
    ) -> WallCalculationOut:
        now = datetime.now(timezone.utc)
        doc = {
            "site_id": site_id,
            "title": title,
            "source_image_path": source_image_path,
            "measurements": [_measurement_to_doc(m) for m in measurements],
            "layers": [_layer_to_doc(layer) for layer in layers],
            "total_measurement": to_decimal128_exact(total_measurement),
            "total_area": to_decimal128_exact(total_area),
            "rate_per_sqft": to_decimal128(rate_per_sqft),
            "total_cost": to_decimal128(total_cost),
            "created_by": admin_id,
            "updated_by": admin_id,
            "created_at": now,
            "updated_at": now,
        }
        result = await self._collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        return _to_out(doc)

    async def get_by_id(self, calc_id: str) -> WallCalculationOut | None:
        if not ObjectId.is_valid(calc_id):
            return None
        doc = await self._collection.find_one({"_id": ObjectId(calc_id)})
        return _to_out(doc) if doc else None

    async def list(self, *, site_id: str | None = None, limit: int = 100) -> list[WallCalculationOut]:
        query: dict = {}
        if site_id:
            query["site_id"] = site_id
        cursor = self._collection.find(query).sort("created_at", -1).limit(limit)
        return [_to_out(doc) async for doc in cursor]

    async def replace_calculation(
        self,
        calc_id: str,
        *,
        site_id: str | None,
        title: str | None,
        measurements: list[MeasurementLine],
        layers: list[LayerOut],
        total_measurement: Decimal,
        total_area: Decimal,
        rate_per_sqft: Decimal,
        total_cost: Decimal,
        admin_id: str,
    ) -> WallCalculationOut | None:
        updates = {
            "site_id": site_id,
            "title": title,
            "measurements": [_measurement_to_doc(m) for m in measurements],
            "layers": [_layer_to_doc(layer) for layer in layers],
            "total_measurement": to_decimal128_exact(total_measurement),
            "total_area": to_decimal128_exact(total_area),
            "rate_per_sqft": to_decimal128(rate_per_sqft),
            "total_cost": to_decimal128(total_cost),
            "updated_by": admin_id,
            "updated_at": datetime.now(timezone.utc),
        }
        await self._collection.update_one({"_id": ObjectId(calc_id)}, {"$set": updates})
        return await self.get_by_id(calc_id)

    async def delete(self, calc_id: str) -> None:
        await self._collection.delete_one({"_id": ObjectId(calc_id)})
