from datetime import datetime, timezone
from typing import Any

from app.db import get_database


async def record_audit_log(
    *,
    entity_type: str,
    entity_id: str,
    action: str,
    admin_id: str,
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
) -> None:
    await get_database().audit_logs.insert_one(
        {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "action": action,
            "admin_id": admin_id,
            "before": before,
            "after": after,
            "at": datetime.now(timezone.utc),
        }
    )
