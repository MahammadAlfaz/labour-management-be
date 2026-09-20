from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field


class MeasurementConfidence(str, Enum):
    HIGH = "high"
    LOW = "low"


class MeasurementLine(BaseModel):
    raw_text: str = Field(max_length=200)
    length: Decimal = Field(gt=0)
    quantity: int = Field(ge=1)
    confidence: MeasurementConfidence = MeasurementConfidence.HIGH
    included: bool = True


class ExtractedMeasurement(BaseModel):
    raw_text: str
    length: Decimal
    quantity: int
    confidence: MeasurementConfidence


class ExtractionResult(BaseModel):
    source_image_path: str
    measurements: list[ExtractedMeasurement]
    warnings: list[str] = Field(default_factory=list)


class LayerInput(BaseModel):
    label: str | None = Field(default=None, max_length=100)
    height: Decimal = Field(gt=0)
    breadth: Decimal = Field(gt=0)


class LayerOut(BaseModel):
    label: str | None
    height: Decimal
    breadth: Decimal
    area: Decimal


class WallCalculationCreate(BaseModel):
    site_id: str | None = None
    title: str | None = Field(default=None, max_length=200)
    source_image_path: str | None = None
    measurements: list[MeasurementLine] = Field(default_factory=list)
    total_measurement: Decimal = Field(gt=0)
    layers: list[LayerInput] = Field(min_length=1)
    rate_per_sqft: Decimal = Field(gt=0)


class WallCalculationUpdate(BaseModel):
    site_id: str | None = None
    title: str | None = Field(default=None, max_length=200)
    measurements: list[MeasurementLine] | None = None
    total_measurement: Decimal | None = Field(default=None, gt=0)
    layers: list[LayerInput] | None = Field(default=None, min_length=1)
    rate_per_sqft: Decimal | None = Field(default=None, gt=0)


class WallCalculationOut(BaseModel):
    id: str
    site_id: str | None
    title: str | None
    source_image_path: str | None
    measurements: list[MeasurementLine]
    total_measurement: Decimal
    layers: list[LayerOut]
    total_area: Decimal
    rate_per_sqft: Decimal
    total_cost: Decimal
    created_by: str
    updated_by: str
    created_at: datetime
    updated_at: datetime
