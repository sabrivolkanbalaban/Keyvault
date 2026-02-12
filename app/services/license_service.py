from datetime import datetime, timedelta, timezone

from sqlalchemy import or_

from app import db
from app.models.license import License, LicenseAssignment
from app.services.audit_service import AuditService

LICENSE_TYPES = [
    ("perpetual", "Perpetual"),
    ("subscription", "Subscription"),
    ("trial", "Trial"),
    ("oem", "OEM"),
    ("volume", "Volume"),
    ("site", "Site License"),
    ("named_user", "Named User"),
    ("concurrent", "Concurrent"),
    ("freeware", "Freeware"),
    ("open_source", "Open Source"),
    ("enterprise", "Enterprise"),
    ("other", "Other"),
]


class LicenseService:
    @staticmethod
    def get_licenses(q=None, license_type=None, status=None, page=1, per_page=25):
        query = License.query

        if q:
            search = f"%{q}%"
            query = query.filter(
                or_(
                    License.name.ilike(search),
                    License.vendor.ilike(search),
                    License.description.ilike(search),
                    License.department.ilike(search),
                )
            )

        if license_type:
            query = query.filter(License.license_type == license_type)

        now = datetime.now(timezone.utc)
        if status == "active":
            query = query.filter(
                License.is_active == True,
                or_(
                    License.expiration_date.is_(None),
                    License.expiration_date > now,
                ),
            )
        elif status == "expired":
            query = query.filter(
                License.expiration_date.isnot(None),
                License.expiration_date <= now,
            )
        elif status == "expiring_soon":
            cutoff = now + timedelta(days=30)
            query = query.filter(
                License.expiration_date.isnot(None),
                License.expiration_date > now,
                License.expiration_date <= cutoff,
            )
        elif status == "inactive":
            query = query.filter(License.is_active == False)

        return query.order_by(License.name).paginate(
            page=page, per_page=per_page, error_out=False
        )

    @staticmethod
    def get_user_licenses(username, full_name=None):
        """Find assignments matching user's username or full name."""
        filters = [LicenseAssignment.is_active == True]
        name_conditions = [LicenseAssignment.assigned_to.ilike(f"%{username}%")]
        if full_name:
            name_conditions.append(
                LicenseAssignment.assigned_to.ilike(f"%{full_name}%")
            )
        filters.append(or_(*name_conditions))
        return (
            LicenseAssignment.query.filter(*filters)
            .join(License)
            .order_by(License.name)
            .all()
        )

    @staticmethod
    def create_license(user, **kwargs):
        license_key_value = kwargs.pop("license_key", None)

        lic = License(
            name=kwargs["name"],
            vendor=kwargs.get("vendor"),
            version=kwargs.get("version"),
            description=kwargs.get("description"),
            license_type=kwargs.get("license_type", "perpetual"),
            cost=kwargs.get("cost"),
            currency=kwargs.get("currency", "USD"),
            purchase_order=kwargs.get("purchase_order"),
            purchase_date=kwargs.get("purchase_date"),
            expiration_date=kwargs.get("expiration_date"),
            support_expiration_date=kwargs.get("support_expiration_date"),
            seat_count=kwargs.get("seat_count"),
            vendor_contact=kwargs.get("vendor_contact"),
            support_plan=kwargs.get("support_plan"),
            department=kwargs.get("department"),
            notes=kwargs.get("notes"),
            created_by_id=user.id,
        )
        if license_key_value:
            lic.license_key = license_key_value

        db.session.add(lic)
        db.session.commit()

        AuditService.log(
            action="license_created",
            user_id=user.id,
            username=user.username,
            resource_type="license",
            resource_id=lic.id,
            resource_name=lic.name,
        )
        return lic

    @staticmethod
    def update_license(lic, user, **kwargs):
        plain_fields = (
            "name",
            "vendor",
            "version",
            "description",
            "license_type",
            "cost",
            "currency",
            "purchase_order",
            "purchase_date",
            "expiration_date",
            "support_expiration_date",
            "seat_count",
            "vendor_contact",
            "support_plan",
            "department",
            "notes",
            "is_active",
        )
        for field in plain_fields:
            if field in kwargs:
                setattr(lic, field, kwargs[field])

        if "license_key" in kwargs and kwargs["license_key"]:
            lic.license_key = kwargs["license_key"]

        db.session.commit()

        AuditService.log(
            action="license_updated",
            user_id=user.id,
            username=user.username,
            resource_type="license",
            resource_id=lic.id,
            resource_name=lic.name,
        )
        return lic

    @staticmethod
    def delete_license(lic, user):
        AuditService.log(
            action="license_deleted",
            user_id=user.id,
            username=user.username,
            resource_type="license",
            resource_id=lic.id,
            resource_name=lic.name,
        )
        db.session.delete(lic)
        db.session.commit()

    @staticmethod
    def assign_user(lic, assigned_to, assigned_by, notes=None, machine_name=None):
        existing = LicenseAssignment.query.filter_by(
            license_id=lic.id, assigned_to=assigned_to, is_active=True
        ).first()
        if existing:
            return None, "This person is already assigned to this license."

        if lic.seat_count is not None and lic.used_seats >= lic.seat_count:
            return None, "No available seats for this license."

        assignment = LicenseAssignment(
            license_id=lic.id,
            assigned_to=assigned_to,
            assigned_by_id=assigned_by.id,
            notes=notes,
            machine_name=machine_name,
        )
        db.session.add(assignment)
        db.session.commit()

        AuditService.log(
            action="license_assigned",
            user_id=assigned_by.id,
            username=assigned_by.username,
            resource_type="license",
            resource_id=lic.id,
            resource_name=lic.name,
            details=f"Assigned to {assigned_to}",
        )
        return assignment, None

    @staticmethod
    def unassign_user(assignment, user):
        assignment.is_active = False
        assignment.unassigned_date = datetime.now(timezone.utc)
        db.session.commit()

        AuditService.log(
            action="license_unassigned",
            user_id=user.id,
            username=user.username,
            resource_type="license",
            resource_id=assignment.license_id,
            resource_name=assignment.license.name,
            details=f"Unassigned {assignment.assigned_to}",
        )

    @staticmethod
    def get_dashboard_stats():
        now = datetime.now(timezone.utc)
        cutoff_30 = now + timedelta(days=30)

        total = License.query.filter_by(is_active=True).count()
        expired = License.query.filter(
            License.is_active == True,
            License.expiration_date.isnot(None),
            License.expiration_date <= now,
        ).count()
        expiring_soon = License.query.filter(
            License.is_active == True,
            License.expiration_date.isnot(None),
            License.expiration_date > now,
            License.expiration_date <= cutoff_30,
        ).count()
        total_assignments = LicenseAssignment.query.filter_by(
            is_active=True
        ).count()

        return {
            "total": total,
            "expired": expired,
            "expiring_soon": expiring_soon,
            "total_assignments": total_assignments,
        }
