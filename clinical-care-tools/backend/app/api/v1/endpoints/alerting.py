"""Alerting API (Sprint 7)"""

from fastapi import APIRouter, Depends
from typing import Annotated
from app.schemas.alerting import Alert
from app.core.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/alerts", tags=["Automated Alerting"])


@router.get("/", response_model=list[Alert])
async def get_alerts(
    current_user: Annotated[User, Depends(get_current_user)]
) -> list[Alert]:
    """Get active alerts"""
    # TODO: Implement alert retrieval
    return []
