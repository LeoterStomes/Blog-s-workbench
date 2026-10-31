from __future__ import annotations

import json
from typing import Any

from database import SessionLocal
from models import ConsultationTaskEvent


def append_task_event(
    session_id: int,
    event_type: str,
    payload: dict[str, Any],
    *,
    status: str | None = None,
    call_id: str | None = None,
) -> int | None:
    db = SessionLocal()
    try:
        event = ConsultationTaskEvent(
            session_id=session_id,
            event_type=event_type,
            status=status,
            call_id=call_id,
            payload=json.dumps(payload, ensure_ascii=False),
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return int(event.id)
    except Exception:
        db.rollback()
        return None
    finally:
        db.close()


def serialize_task_event(event: ConsultationTaskEvent) -> dict[str, Any]:
    try:
        payload = json.loads(event.payload or "{}")
    except (json.JSONDecodeError, TypeError):
        payload = {"text": event.payload or ""}
    return {
        "id": str(event.id),
        "type": event.event_type,
        "status": event.status or "",
        "callId": event.call_id or "",
        "payload": payload,
        "createdAt": event.created_at.isoformat() if event.created_at else "",
    }
