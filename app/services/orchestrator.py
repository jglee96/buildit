from __future__ import annotations

from datetime import datetime
from time import perf_counter
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    DesignOption,
    DesignRun,
    Project,
    ProjectAestheticInput,
    ProjectRequirement,
    ProjectRuleSnapshot,
    RuleDefinition,
    RuleSet,
    RunStatus,
    SolarResult,
    User,
)
from app.schemas import AestheticInputValue, EvaluateRequest, ProjectCreate, RequirementValue, RunRead
from app.services.optimizer import compute_solar_profile, optimize_options


def create_user(db: Session, *, email: str, name: Optional[str]) -> User:
    existing = db.scalar(select(User).where(User.email == email))
    if existing is not None:
        if name and existing.name != name:
            existing.name = name
            db.commit()
            db.refresh(existing)
        return existing
    user = User(email=email, name=name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_project(db: Session, payload: ProjectCreate) -> Project:
    data = payload.model_dump()
    aesthetic_inputs = data.pop("aesthetic_inputs", [])
    project = Project(**data)
    db.add(project)
    db.flush()
    for aesthetic_input in aesthetic_inputs:
        db.add(ProjectAestheticInput(project_id=project.id, **aesthetic_input))
    db.commit()
    db.refresh(project)
    return project


def upsert_requirements(db: Session, *, project_id: str, requirements: list[RequirementValue]) -> list[ProjectRequirement]:
    existing = db.scalars(select(ProjectRequirement).where(ProjectRequirement.project_id == project_id)).all()
    existing_by_key = {item.key: item for item in existing}
    for req in requirements:
        row = existing_by_key.get(req.key)
        if row is None:
            row = ProjectRequirement(project_id=project_id, key=req.key)
            db.add(row)
        row.min_value = req.min_value
        row.max_value = req.max_value
        row.required_value = req.required_value
        row.unit = req.unit
    db.commit()
    return db.scalars(select(ProjectRequirement).where(ProjectRequirement.project_id == project_id)).all()


def upsert_aesthetic_inputs(db: Session, *, project_id: str, inputs: list[AestheticInputValue]) -> list[ProjectAestheticInput]:
    existing = db.scalars(select(ProjectAestheticInput).where(ProjectAestheticInput.project_id == project_id)).all()
    for row in existing:
        db.delete(row)
    db.flush()
    for aesthetic_input in inputs:
        db.add(ProjectAestheticInput(project_id=project_id, **aesthetic_input.model_dump()))
    db.commit()
    return db.scalars(select(ProjectAestheticInput).where(ProjectAestheticInput.project_id == project_id)).all()


def create_ruleset(db: Session, payload) -> RuleSet:
    row = RuleSet(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def create_rule_definition(db: Session, payload) -> RuleDefinition:
    row = RuleDefinition(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def resolve_active_rules(db: Session, *, project: Project, evaluation_date, category: str) -> tuple[list[RuleSet], list[RuleDefinition]]:
    stmt = (
        select(RuleSet)
        .where(RuleSet.country_code == project.country_code)
        .where(RuleSet.jurisdiction_code == project.jurisdiction_code)
        .where(RuleSet.category == category)
        .where(RuleSet.status == "active")
        .where(RuleSet.effective_from <= evaluation_date)
        .where((RuleSet.effective_to.is_(None)) | (RuleSet.effective_to >= evaluation_date))
        .order_by(RuleSet.effective_from.desc())
    )
    rule_sets = db.scalars(stmt).all()
    if not rule_sets:
        return [], []
    rule_set_ids = [item.id for item in rule_sets]
    definitions = db.scalars(select(RuleDefinition).where(RuleDefinition.rule_set_id.in_(rule_set_ids)).order_by(RuleDefinition.priority.asc())).all()
    return rule_sets, definitions


def create_snapshot(db: Session, *, project_id: str, evaluation_date, rule_sets: list[RuleSet], definitions: list[RuleDefinition]) -> ProjectRuleSnapshot:
    snapshot = ProjectRuleSnapshot(
        project_id=project_id,
        evaluation_date=evaluation_date,
        frozen_rule_set_ids=[row.id for row in rule_sets],
        frozen_rule_definition_ids=[row.id for row in definitions],
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot


def run_evaluation(db: Session, *, project: Project, payload: EvaluateRequest) -> DesignRun:
    t_eval_start = perf_counter()
    stage_ms: dict[str, float] = {}

    t_stage = perf_counter()
    rule_sets, definitions = resolve_active_rules(
        db,
        project=project,
        evaluation_date=payload.evaluation_date,
        category=payload.category,
    )
    stage_ms["resolve_rules"] = round((perf_counter() - t_stage) * 1000.0, 3)
    if not rule_sets:
        raise ValueError("No active rule set matched project + date")

    t_stage = perf_counter()
    snapshot = create_snapshot(db, project_id=project.id, evaluation_date=payload.evaluation_date, rule_sets=rule_sets, definitions=definitions)
    stage_ms["create_snapshot"] = round((perf_counter() - t_stage) * 1000.0, 3)

    run = DesignRun(
        project_id=project.id,
        snapshot_id=snapshot.id,
        objective=payload.objective,
        status=RunStatus.RUNNING.value,
        started_at=datetime.utcnow(),
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    t_stage = perf_counter()
    requirements = db.scalars(select(ProjectRequirement).where(ProjectRequirement.project_id == project.id)).all()
    aesthetic_inputs = db.scalars(select(ProjectAestheticInput).where(ProjectAestheticInput.project_id == project.id)).all()
    options, optimizer_profile = optimize_options(
        rule_definitions=definitions,
        requirements=requirements,
        objective=payload.objective,
        site_geojson=project.site_geojson,
        country_code=project.country_code,
        occupancy_type=project.occupancy_type,
        aesthetic_inputs=aesthetic_inputs,
    )
    stage_ms["optimize_options"] = round((perf_counter() - t_stage) * 1000.0, 3)

    t_stage = perf_counter()
    lat, lng = project_lat_lng(project.site_geojson)
    solar_profile = compute_solar_profile(lat, lng, payload.evaluation_date, payload.hours)
    stage_ms["compute_solar_profile"] = round((perf_counter() - t_stage) * 1000.0, 3)

    t_stage = perf_counter()
    for rank, option in enumerate(options, start=1):
        option_parameters = dict(option["parameters"])
        option_parameters["runtime_profile"] = {
            "pipeline_ms": stage_ms,
            "optimizer_ms": optimizer_profile,
        }
        option_row = DesignOption(
            run_id=run.id,
            rank=rank,
            option_type=option["option_type"],
            score=option["score"],
            parameters=option_parameters,
            checks=option["checks"],
            mesh_payload=option["mesh_payload"],
        )
        db.add(option_row)
        db.flush()
        for solar in solar_profile:
            db.add(
                SolarResult(
                    option_id=option_row.id,
                    timestamp_utc=solar["timestamp_utc"],
                    sun_altitude=solar["sun_altitude"],
                    sun_azimuth=solar["sun_azimuth"],
                    insolation_kwh_m2=solar["insolation_kwh_m2"],
                    shadow_ratio=solar["shadow_ratio"],
                )
            )
    stage_ms["persist_options_and_solar"] = round((perf_counter() - t_stage) * 1000.0, 3)
    stage_ms["total"] = round((perf_counter() - t_eval_start) * 1000.0, 3)

    run.status = RunStatus.COMPLETED.value
    run.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(run)
    return run


def get_run_response(db: Session, run_id: str) -> Optional[RunRead]:
    run = db.get(DesignRun, run_id)
    if run is None:
        return None
    options = db.scalars(select(DesignOption).where(DesignOption.run_id == run_id).order_by(DesignOption.rank.asc())).all()
    solar_map: dict[str, list] = {}
    for option in options:
        records = db.scalars(select(SolarResult).where(SolarResult.option_id == option.id).order_by(SolarResult.timestamp_utc.asc())).all()
        solar_map[option.id] = records
    return RunRead(
        id=run.id,
        project_id=run.project_id,
        snapshot_id=run.snapshot_id,
        objective=run.objective,
        status=run.status,
        started_at=run.started_at,
        completed_at=run.completed_at,
        error_message=run.error_message,
        options=[
            {
                "id": option.id,
                "rank": option.rank,
                "option_type": option.option_type,
                "score": option.score,
                "parameters": option.parameters,
                "checks": option.checks,
                "mesh_payload": option.mesh_payload,
            }
            for option in options
        ],
        solar={
            option_id: [
                {
                    "timestamp_utc": row.timestamp_utc,
                    "sun_altitude": row.sun_altitude,
                    "sun_azimuth": row.sun_azimuth,
                    "insolation_kwh_m2": row.insolation_kwh_m2,
                    "shadow_ratio": row.shadow_ratio,
                }
                for row in rows
            ]
            for option_id, rows in solar_map.items()
        },
    )


def project_lat_lng(site_geojson: dict) -> tuple[float, float]:
    coordinates = site_geojson.get("coordinates", [])
    if not coordinates or not coordinates[0]:
        return 37.5665, 126.9780
    ring = coordinates[0]
    lng_values = [pt[0] for pt in ring]
    lat_values = [pt[1] for pt in ring]
    return sum(lat_values) / len(lat_values), sum(lng_values) / len(lng_values)


def get_project(db: Session, project_id: str) -> Optional[Project]:
    return db.get(Project, project_id)


def get_user(db: Session, user_id: str) -> Optional[User]:
    return db.get(User, user_id)
