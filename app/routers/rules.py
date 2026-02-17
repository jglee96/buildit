from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import RuleDefinitionCreate, RuleDefinitionRead, RuleSetCreate, RuleSetRead
from app.services.orchestrator import create_rule_definition, create_ruleset

router = APIRouter(prefix="/rules", tags=["rules"])


@router.post("/sets", response_model=RuleSetRead)
def create_rule_set_endpoint(payload: RuleSetCreate, db: Session = Depends(get_db)) -> RuleSetRead:
    try:
        row = create_ruleset(db, payload)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return RuleSetRead.model_validate(row, from_attributes=True)


@router.post("/definitions", response_model=RuleDefinitionRead)
def create_rule_definition_endpoint(payload: RuleDefinitionCreate, db: Session = Depends(get_db)) -> RuleDefinitionRead:
    try:
        row = create_rule_definition(db, payload)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return RuleDefinitionRead.model_validate(row, from_attributes=True)
