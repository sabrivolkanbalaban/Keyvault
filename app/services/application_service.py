from sqlalchemy import or_

from app import db
from app.models.application import Application
from app.services.audit_service import AuditService

PLATFORM_CHOICES = [
    ("java", "Java"),
    ("dotnet", ".NET"),
    ("python", "Python"),
    ("nodejs", "Node.js"),
    ("php", "PHP"),
    ("other", "Other"),
]

DEPLOYMENT_CHOICES = [
    ("iis", "IIS"),
    ("docker", "Docker"),
    ("linux_service", "Linux Service"),
    ("kubernetes", "Kubernetes"),
    ("other", "Other"),
]

SLA_CHOICES = [
    ("Critical", "Critical"),
    ("High", "High"),
    ("Medium", "Medium"),
    ("Low", "Low"),
]

CRITICALITY_CHOICES = [
    ("Mission Critical", "Mission Critical"),
    ("Business Critical", "Business Critical"),
    ("Business Operational", "Business Operational"),
    ("Administrative", "Administrative"),
]

STATUS_CHOICES = [
    ("active", "Active"),
    ("inactive", "Inactive"),
]


class ApplicationService:

    @staticmethod
    def get_applications(q=None, status=None, platform=None, page=1, per_page=25):
        query = Application.query

        if q:
            search = f"%{q}%"
            query = query.filter(
                or_(
                    Application.name.ilike(search),
                    Application.server_name.ilike(search),
                    Application.ip_address.ilike(search),
                    Application.description.ilike(search),
                    Application.responsible_person.ilike(search),
                    Application.department.ilike(search),
                )
            )

        if status:
            query = query.filter(Application.status == status)

        if platform:
            query = query.filter(Application.platform == platform)

        return query.order_by(Application.name).paginate(
            page=page, per_page=per_page, error_out=False
        )

    @staticmethod
    def create_application(user, **kwargs):
        app_record = Application(created_by_id=user.id)
        for key, value in kwargs.items():
            if hasattr(app_record, key):
                setattr(app_record, key, value)
        db.session.add(app_record)
        db.session.commit()

        AuditService.log(
            action="application_created",
            user_id=user.id,
            username=user.username,
            resource_type="application",
            resource_id=app_record.id,
            resource_name=app_record.name,
        )
        return app_record

    @staticmethod
    def update_application(app_record, user, **kwargs):
        for key, value in kwargs.items():
            if hasattr(app_record, key):
                setattr(app_record, key, value)
        db.session.commit()

        AuditService.log(
            action="application_updated",
            user_id=user.id,
            username=user.username,
            resource_type="application",
            resource_id=app_record.id,
            resource_name=app_record.name,
        )
        return app_record

    @staticmethod
    def delete_application(app_record, user):
        AuditService.log(
            action="application_deleted",
            user_id=user.id,
            username=user.username,
            resource_type="application",
            resource_id=app_record.id,
            resource_name=app_record.name,
        )
        db.session.delete(app_record)
        db.session.commit()

    @staticmethod
    def get_dashboard_stats():
        total = Application.query.count()
        active = Application.query.filter_by(status="active").count()
        inactive = Application.query.filter_by(status="inactive").count()
        mission_critical = Application.query.filter_by(
            criticality="Mission Critical", status="active"
        ).count()
        return {
            "total": total,
            "active": active,
            "inactive": inactive,
            "mission_critical": mission_critical,
        }
