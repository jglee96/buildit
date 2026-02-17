from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from sqlalchemy import JSON, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def id_str() -> str:
    return str(uuid4())


class RuleType(str, Enum):
    HARD = "hard"
    SOFT = "soft"


class RuleStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"


class RunStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=id_str)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    projects: Mapped[list["Project"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=id_str)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    country_code: Mapped[str] = mapped_column(String, nullable=False)
    jurisdiction_code: Mapped[str] = mapped_column(String, nullable=False)
    occupancy_type: Mapped[str] = mapped_column(String, nullable=False)
    site_geojson: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="projects")
    requirements: Mapped[list["ProjectRequirement"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    aesthetic_inputs: Mapped[list["ProjectAestheticInput"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    snapshots: Mapped[list["ProjectRuleSnapshot"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    runs: Mapped[list["DesignRun"]] = relationship(back_populates="project", cascade="all, delete-orphan")


class ProjectRequirement(Base):
    __tablename__ = "project_requirements"
    __table_args__ = (UniqueConstraint("project_id", "key", name="uq_project_requirement"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=id_str)
    project_id: Mapped[str] = mapped_column(String, ForeignKey("projects.id"), nullable=False)
    key: Mapped[str] = mapped_column(String, nullable=False)
    min_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    required_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    unit: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    project: Mapped["Project"] = relationship(back_populates="requirements")


class ProjectAestheticInput(Base):
    __tablename__ = "project_aesthetic_inputs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=id_str)
    project_id: Mapped[str] = mapped_column(String, ForeignKey("projects.id"), nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    reference_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    project: Mapped["Project"] = relationship(back_populates="aesthetic_inputs")


class RuleSet(Base):
    __tablename__ = "rule_sets"
    __table_args__ = (UniqueConstraint("country_code", "jurisdiction_code", "category", "version", name="uq_ruleset_version"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=id_str)
    country_code: Mapped[str] = mapped_column(String, nullable=False)
    jurisdiction_code: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    version: Mapped[str] = mapped_column(String, nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    source_hash: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String, default=RuleStatus.ACTIVE.value, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    definitions: Mapped[list["RuleDefinition"]] = relationship(back_populates="rule_set", cascade="all, delete-orphan")


class RuleDefinition(Base):
    __tablename__ = "rule_definitions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=id_str)
    rule_set_id: Mapped[str] = mapped_column(String, ForeignKey("rule_sets.id"), nullable=False)
    rule_key: Mapped[str] = mapped_column(String, nullable=False)
    rule_type: Mapped[str] = mapped_column(String, default=RuleType.HARD.value, nullable=False)
    expression: Mapped[dict] = mapped_column(JSON, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    rule_set: Mapped["RuleSet"] = relationship(back_populates="definitions")


class ProjectRuleSnapshot(Base):
    __tablename__ = "project_rule_snapshots"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=id_str)
    project_id: Mapped[str] = mapped_column(String, ForeignKey("projects.id"), nullable=False)
    evaluation_date: Mapped[date] = mapped_column(Date, nullable=False)
    frozen_rule_set_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    frozen_rule_definition_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    project: Mapped["Project"] = relationship(back_populates="snapshots")
    runs: Mapped[list["DesignRun"]] = relationship(back_populates="snapshot", cascade="all, delete-orphan")


class DesignRun(Base):
    __tablename__ = "design_runs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=id_str)
    project_id: Mapped[str] = mapped_column(String, ForeignKey("projects.id"), nullable=False)
    snapshot_id: Mapped[str] = mapped_column(String, ForeignKey("project_rule_snapshots.id"), nullable=False)
    objective: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default=RunStatus.QUEUED.value, nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="runs")
    snapshot: Mapped["ProjectRuleSnapshot"] = relationship(back_populates="runs")
    options: Mapped[list["DesignOption"]] = relationship(back_populates="run", cascade="all, delete-orphan")


class DesignOption(Base):
    __tablename__ = "design_options"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=id_str)
    run_id: Mapped[str] = mapped_column(String, ForeignKey("design_runs.id"), nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    option_type: Mapped[str] = mapped_column(String, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    parameters: Mapped[dict] = mapped_column(JSON, nullable=False)
    checks: Mapped[list] = mapped_column(JSON, nullable=False)
    mesh_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    run: Mapped["DesignRun"] = relationship(back_populates="options")
    solar_results: Mapped[list["SolarResult"]] = relationship(back_populates="option", cascade="all, delete-orphan")


class SolarResult(Base):
    __tablename__ = "solar_results"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=id_str)
    option_id: Mapped[str] = mapped_column(String, ForeignKey("design_options.id"), nullable=False)
    timestamp_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    sun_altitude: Mapped[float] = mapped_column(Float, nullable=False)
    sun_azimuth: Mapped[float] = mapped_column(Float, nullable=False)
    insolation_kwh_m2: Mapped[float] = mapped_column(Float, nullable=False)
    shadow_ratio: Mapped[float] = mapped_column(Float, nullable=False)

    option: Mapped["DesignOption"] = relationship(back_populates="solar_results")
