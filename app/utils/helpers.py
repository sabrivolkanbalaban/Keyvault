from datetime import datetime, timezone


def time_ago(dt):
    """Return a human-readable relative time string."""
    if not dt:
        return "Never"

    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    diff = now - dt
    seconds = diff.total_seconds()

    if seconds < 60:
        return "Just now"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes}m ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours}h ago"
    elif seconds < 2592000:
        days = int(seconds / 86400)
        return f"{days}d ago"
    else:
        return dt.strftime("%Y-%m-%d")


CATEGORY_ICONS = {
    "credential": "bi-key",
    "url": "bi-link-45deg",
    "api_key": "bi-braces",
    "certificate": "bi-shield-lock",
    "note": "bi-journal-text",
    "database": "bi-database",
    "ssh_key": "bi-terminal",
    "other": "bi-file-earmark-lock",
}

CATEGORY_COLORS = {
    "credential": "primary",
    "url": "info",
    "api_key": "warning",
    "certificate": "success",
    "note": "secondary",
    "database": "danger",
    "ssh_key": "dark",
    "other": "light",
}


def get_category_icon(category):
    return CATEGORY_ICONS.get(category, "bi-file-earmark-lock")


def get_category_color(category):
    return CATEGORY_COLORS.get(category, "secondary")
