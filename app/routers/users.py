from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import UserCreate, UserRead
from app.services.orchestrator import create_user

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserRead)
def create_user_endpoint(payload: UserCreate, db: Session = Depends(get_db)) -> UserRead:
    try:
        user = create_user(db, email=payload.email, name=payload.name)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return UserRead.model_validate(user, from_attributes=True)
