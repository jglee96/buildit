from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import AestheticInputValue, ProjectCreate, ProjectRead, RequirementValue
from app.services.orchestrator import create_project, get_user, upsert_aesthetic_inputs, upsert_requirements

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectRead)
def create_project_endpoint(payload: ProjectCreate, db: Session = Depends(get_db)) -> ProjectRead:
    user = get_user(db, payload.user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    row = create_project(db, payload)
    return ProjectRead.model_validate(row, from_attributes=True)


@router.post("/{project_id}/requirements", response_model=list[RequirementValue])
def upsert_requirements_endpoint(
    project_id: str,
    payload: list[RequirementValue],
    db: Session = Depends(get_db),
) -> list[RequirementValue]:
    try:
        rows = upsert_requirements(db, project_id=project_id, requirements=payload)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return [RequirementValue.model_validate(row, from_attributes=True) for row in rows]


@router.post("/{project_id}/aesthetic-inputs", response_model=list[AestheticInputValue])
def upsert_aesthetic_inputs_endpoint(
    project_id: str,
    payload: list[AestheticInputValue],
    db: Session = Depends(get_db),
) -> list[AestheticInputValue]:
    try:
        rows = upsert_aesthetic_inputs(db, project_id=project_id, inputs=payload)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return [AestheticInputValue.model_validate(row, from_attributes=True) for row in rows]
