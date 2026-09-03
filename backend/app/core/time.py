from datetime import datetime, timezone

def utcnow() -> datetime:
    """UTC timestamp stored as naive UTC for broad SQLite/PostgreSQL compatibility."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
