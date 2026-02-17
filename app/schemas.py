from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    email: str
    name: Optional[str] = None


class UserRead(UserCreate):
    id: str
    created_at: datetime


class AestheticInputValue(BaseModel):
    category: str
    content: str
    reference_url: Optional[str] = None
    weight: float = 1.0


class ProjectCreate(BaseModel):
    user_id: str
    name: str
    country_code: str
    jurisdiction_code: str
    occupancy_type: str
    site_geojson: dict[str, Any]
    aesthetic_inputs: list[AestheticInputValue] = Field(default_factory=list)


class ProjectRead(ProjectCreate):
    id: str
    created_at: datetime


class RequirementValue(BaseModel):
    key: str
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    required_value: Optional[float] = None
    unit: Optional[str] = None


class RuleSetCreate(BaseModel):
    country_code: str = Field(..., examples=["KR"])
    jurisdiction_code: str = Field(..., examples=["KR-11-SEOUL-JONGNO"])
    category: str = Field(..., examples=["zoning"])
    version: str = Field(..., examples=["2026.02.01"])
    effective_from: date
    effective_to: Optional[date] = None
    source_url: str
    source_hash: Optional[str] = None
    published_at: datetime
    status: str = "active"


class RuleSetRead(RuleSetCreate):
    id: str
    created_at: datetime


class RuleDefinitionCreate(BaseModel):
    rule_set_id: str
    rule_key: str
    rule_type: str = "hard"
    expression: dict[str, Any]
    priority: int = 100


class RuleDefinitionRead(RuleDefinitionCreate):
    id: str
    created_at: datetime


class SnapshotCreateRequest(BaseModel):
    evaluation_date: date
    category: str = "zoning"


class SnapshotRead(BaseModel):
    id: str
    project_id: str
    evaluation_date: date
    frozen_rule_set_ids: list[str]
    frozen_rule_definition_ids: list[str]
    created_at: datetime


class EvaluateRequest(BaseModel):
    evaluation_date: date
    category: str = "zoning"
    objective: str = "maximize_far"
    hours: list[int] = Field(default_factory=lambda: [9, 12, 15])


class ConstraintCheck(BaseModel):
    rule_key: str
    rule_type: str
    passed: bool
    detail: str


class DesignOptionRead(BaseModel):
    id: str
    rank: int
    option_type: str
    score: float
    parameters: dict[str, Any]
    checks: list[ConstraintCheck]
    mesh_payload: dict[str, Any]


class SolarPoint(BaseModel):
    timestamp_utc: datetime
    sun_altitude: float
    sun_azimuth: float
    insolation_kwh_m2: float
    shadow_ratio: float


class RunRead(BaseModel):
    id: str
    project_id: str
    snapshot_id: str
    objective: str
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    options: list[DesignOptionRead] = Field(default_factory=list)
    solar: dict[str, list[SolarPoint]] = Field(default_factory=dict)
