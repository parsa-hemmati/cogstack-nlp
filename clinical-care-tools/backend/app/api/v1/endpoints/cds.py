"""Clinical Decision Support API (Sprint 6)"""

from fastapi import APIRouter, Depends
from typing import Annotated

from app.schemas.clinical_decision_support import CDSRequest, CDSResponse, CDSRecommendation
from app.core.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/cds", tags=["Clinical Decision Support"])


@router.post("/hooks/{hook_id}", response_model=CDSResponse)
async def cds_hook(
    hook_id: str,
    request: CDSRequest,
    current_user: Annotated[User, Depends(get_current_user)]
) -> CDSResponse:
    """CDS Hooks endpoint

    Implements CDS Hooks specification for EHR integration.
    """
    # TODO: Implement CDS logic
    return CDSResponse(cards=[])
