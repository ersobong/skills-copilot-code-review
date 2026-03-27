"""Announcements endpoints for the High School Management System API."""

from datetime import date
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from pymongo import ReturnDocument

from ..database import announcements_collection, teachers_collection

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"]
)


class AnnouncementPayload(BaseModel):
    """Announcement payload used for create and update operations."""

    message: str = Field(min_length=1, max_length=400)
    expiration_date: str
    start_date: Optional[str] = None


def _validate_iso_date(date_value: str, field_name: str) -> date:
    try:
        return date.fromisoformat(date_value)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} must be in YYYY-MM-DD format"
        ) from exc


def _validate_dates(payload: AnnouncementPayload) -> Dict[str, Optional[str]]:
    trimmed_message = payload.message.strip()
    if not trimmed_message:
        raise HTTPException(status_code=400, detail="Message is required")

    expiration = _validate_iso_date(payload.expiration_date, "expiration_date")

    normalized_start_date: Optional[str] = None
    if payload.start_date:
        start = _validate_iso_date(payload.start_date, "start_date")
        if start > expiration:
            raise HTTPException(
                status_code=400,
                detail="start_date must be on or before expiration_date"
            )
        normalized_start_date = start.isoformat()

    return {
        "message": trimmed_message,
        "start_date": normalized_start_date,
        "expiration_date": expiration.isoformat()
    }


def _assert_authenticated_user(username: str) -> None:
    teacher = teachers_collection.find_one({"_id": username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Invalid teacher credentials")


def _serialize_announcement(document: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": str(document.get("_id")),
        "message": document.get("message", ""),
        "start_date": document.get("start_date"),
        "expiration_date": document.get("expiration_date")
    }


@router.get("", response_model=List[Dict[str, Any]])
@router.get("/", response_model=List[Dict[str, Any]])
def get_active_announcements() -> List[Dict[str, Any]]:
    """Get all active announcements for public display."""
    today = date.today().isoformat()
    query = {
        "expiration_date": {"$gte": today},
        "$or": [
            {"start_date": None},
            {"start_date": {"$exists": False}},
            {"start_date": ""},
            {"start_date": {"$lte": today}}
        ]
    }

    results = announcements_collection.find(query).sort("expiration_date", 1)
    return [_serialize_announcement(document) for document in results]


@router.get("/manage", response_model=List[Dict[str, Any]])
def get_all_announcements(username: str = Query(...)) -> List[Dict[str, Any]]:
    """Get all announcements for management (requires authenticated user)."""
    _assert_authenticated_user(username)
    results = announcements_collection.find({}).sort("expiration_date", 1)
    return [_serialize_announcement(document) for document in results]


@router.post("", response_model=Dict[str, Any])
@router.post("/", response_model=Dict[str, Any])
def create_announcement(
    payload: AnnouncementPayload,
    username: str = Query(...)
) -> Dict[str, Any]:
    """Create an announcement (requires authenticated user)."""
    _assert_authenticated_user(username)
    announcement = _validate_dates(payload)

    result = announcements_collection.insert_one(announcement)
    created = announcements_collection.find_one({"_id": result.inserted_id})

    if not created:
        raise HTTPException(status_code=500, detail="Failed to create announcement")

    return _serialize_announcement(created)


@router.put("/{announcement_id}", response_model=Dict[str, Any])
def update_announcement(
    announcement_id: str,
    payload: AnnouncementPayload,
    username: str = Query(...)
) -> Dict[str, Any]:
    """Update an announcement (requires authenticated user)."""
    _assert_authenticated_user(username)
    announcement = _validate_dates(payload)

    target = announcements_collection.find_one({"_id": announcement_id})
    if target:
        announcements_collection.update_one({"_id": announcement_id}, {"$set": announcement})
        updated = announcements_collection.find_one({"_id": announcement_id})
        if not updated:
            raise HTTPException(status_code=500, detail="Failed to update announcement")
        return _serialize_announcement(updated)

    # Fallback for ObjectId-based records created before this change.
    from bson import ObjectId  # Local import to avoid unnecessary dependency during module import.

    try:
        object_id = ObjectId(announcement_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail="Announcement not found") from exc

    result = announcements_collection.find_one_and_update(
        {"_id": object_id},
        {"$set": announcement},
        return_document=ReturnDocument.AFTER
    )

    if not result:
        raise HTTPException(status_code=404, detail="Announcement not found")

    return _serialize_announcement(result)


@router.delete("/{announcement_id}")
def delete_announcement(
    announcement_id: str,
    username: str = Query(...)
) -> Dict[str, str]:
    """Delete an announcement (requires authenticated user)."""
    _assert_authenticated_user(username)

    result = announcements_collection.delete_one({"_id": announcement_id})
    if result.deleted_count == 1:
        return {"message": "Announcement deleted"}

    from bson import ObjectId  # Local import to avoid unnecessary dependency during module import.

    try:
        object_id = ObjectId(announcement_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail="Announcement not found") from exc

    legacy_result = announcements_collection.delete_one({"_id": object_id})
    if legacy_result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")

    return {"message": "Announcement deleted"}
