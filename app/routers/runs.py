from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import EvaluateRequest, RunRead
from app.services.orchestrator import get_project, get_run_response, run_evaluation

router = APIRouter(prefix="/runs", tags=["runs"])


@router.post("/projects/{project_id}/evaluate", response_model=RunRead)
def evaluate_project_endpoint(project_id: str, payload: EvaluateRequest, db: Session = Depends(get_db)) -> RunRead:
    project = get_project(db, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    try:
        run = run_evaluation(db, project=project, payload=payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    response = get_run_response(db, run.id)
    if response is None:
        raise HTTPException(status_code=500, detail="Run created but not found")
    return response


@router.get("/{run_id}", response_model=RunRead)
def get_run_endpoint(run_id: str, db: Session = Depends(get_db)) -> RunRead:
    response = get_run_response(db, run_id)
    if response is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return response
