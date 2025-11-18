"""Session schemas for API.

Pydantic models for session management operations.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class SessionInfo(BaseModel):
    """Session information."""

    session_id: str
    user_id: str
    created_at: datetime
    expires_at: datetime
    ip_address: Optional[str]
    user_agent: Optional[str]
    is_current: bool  # Whether this is the current session


class SessionListResponse(BaseModel):
    """List of active sessions."""

    sessions: List[SessionInfo]
    total: int
