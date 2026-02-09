import csv
import json
from datetime import datetime, timezone
from io import StringIO

from app.models.secret import Secret


class ExportService:
    @staticmethod
    def export_json(secrets: list, include_passwords: bool = True) -> str:
        data = {
            "version": "1.0",
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "count": len(secrets),
            "items": [],
        }
        for s in secrets:
            item = {
                "name": s.name,
                "category": s.category,
                "description": s.description,
                "username": s.username if include_passwords else "***",
                "password": s.password if include_passwords else "***",
                "url": s.url,
                "notes": s.notes if include_passwords else "***",
                "api_key": s.api_key if include_passwords else "***",
                "tags": [t.name for t in s.tags],
                "folder": s.folder.name if s.folder else None,
                "created_at": (
                    s.created_at.isoformat() if s.created_at else None
                ),
                "expires_at": (
                    s.expires_at.isoformat() if s.expires_at else None
                ),
            }
            data["items"].append(item)
        return json.dumps(data, indent=2, ensure_ascii=False)

    @staticmethod
    def export_csv(secrets: list) -> str:
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(
            ["Name", "Category", "Username", "URL", "Tags", "Created At"]
        )
        for s in secrets:
            writer.writerow(
                [
                    s.name,
                    s.category,
                    s.username or "",
                    s.url or "",
                    ", ".join(t.name for t in s.tags),
                    s.created_at.isoformat() if s.created_at else "",
                ]
            )
        return output.getvalue()

    @staticmethod
    def import_json(json_data: str, owner_id: int) -> list:
        data = json.loads(json_data)
        created = []
        for item in data.get("items", []):
            secret = Secret(
                name=item["name"],
                category=item.get("category", "credential"),
                owner_id=owner_id,
            )
            secret.username = item.get("username")
            secret.password = item.get("password")
            secret.url = item.get("url")
            secret.notes = item.get("notes")
            secret.api_key = item.get("api_key")
            if item.get("description"):
                secret.description = item["description"]
            created.append(secret)
        return created

    @staticmethod
    def import_keepass_csv(csv_data: str, owner_id: int) -> list:
        reader = csv.DictReader(StringIO(csv_data))
        created = []
        for row in reader:
            secret = Secret(
                name=row.get("Title", row.get("Group", "Imported")),
                category="credential",
                owner_id=owner_id,
            )
            secret.username = row.get("Username")
            secret.password = row.get("Password")
            secret.url = row.get("URL")
            secret.notes = row.get("Notes")
            created.append(secret)
        return created
