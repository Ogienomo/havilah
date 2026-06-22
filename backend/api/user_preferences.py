"""
Havilah OS — User Preferences API

GET  /api/user/preferences       → fetch current user's preferences
PUT  /api/user/preferences       → update current user's preferences
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.models.user_preferences import UserPreferences
from backend.repositories.base import get_session

logger = logging.getLogger("havilah.api.user_preferences")

router = APIRouter(prefix="/api/user", tags=["user-preferences"])


class UserPreferencesResponse(BaseModel):
    user_id: UUID
    auto_approve: bool
    preferences: dict


class UserPreferencesUpdate(BaseModel):
    auto_approve: Optional[bool] = None
    preferences: Optional[dict] = None


def _get_or_create_prefs(db, user_id: str) -> UserPreferences:
    prefs = db.query(UserPreferences).filter(UserPreferences.user_id == user_id).first()
    if prefs is None:
        prefs = UserPreferences(user_id=user_id, auto_approve=False, preferences={})
        db.add(prefs)
        db.flush()
    return prefs


@router.get("/preferences", response_model=UserPreferencesResponse)
def get_preferences(user_id: str):
    """Fetch preferences for the given user_id."""
    try:
        with get_session() as db:
            prefs = _get_or_create_prefs(db, user_id)
            return UserPreferencesResponse(
                user_id=prefs.user_id,
                auto_approve=prefs.auto_approve,
                preferences=prefs.preferences or {},
            )
    except Exception as e:
        logger.error(f"Failed to fetch preferences for {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch preferences")


@router.put("/preferences", response_model=UserPreferencesResponse)
def update_preferences(user_id: str, body: UserPreferencesUpdate):
    """Update preferences for the given user_id."""
    try:
        with get_session() as db:
            prefs = _get_or_create_prefs(db, user_id)
            if body.auto_approve is not None:
                prefs.auto_approve = body.auto_approve
            if body.preferences is not None:
                prefs.preferences = {**(prefs.preferences or {}), **body.preferences}
            prefs.updated_at = datetime.now(timezone.utc)
            db.flush()
            return UserPreferencesResponse(
                user_id=prefs.user_id,
                auto_approve=prefs.auto_approve,
                preferences=prefs.preferences or {},
            )
    except Exception as e:
        logger.error(f"Failed to update preferences for {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update preferences")
