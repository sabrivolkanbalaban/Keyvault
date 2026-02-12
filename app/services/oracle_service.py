import re

import oracledb


class OracleService:
    def __init__(self, config):
        self.host = config["ORACLE_HOST"]
        self.port = config["ORACLE_PORT"]
        self.service = config["ORACLE_SERVICE"]
        self.user = config["ORACLE_USER"]
        self.password = config["ORACLE_PASSWORD"]
        self.dsn = f"{self.host}:{self.port}/{self.service}"

    def _get_connection(self):
        return oracledb.connect(
            user=self.user,
            password=self.password,
            dsn=self.dsn,
        )

    def test_connection(self) -> dict:
        """Test Oracle connection and return server info."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT banner FROM v$version WHERE ROWNUM = 1")
            row = cursor.fetchone()
            version = row[0] if row else "Unknown"
            cursor.close()
            conn.close()
            return {"success": True, "version": version}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_users(self) -> list:
        """Get all Oracle database users."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT username, 'OPEN' AS account_status, created "
            "FROM all_users "
            "ORDER BY username"
        )
        users = []
        for row in cursor:
            users.append({
                "username": row[0],
                "account_status": row[1],
                "created": row[2],
            })
        cursor.close()
        conn.close()
        return users

    def get_schemas(self) -> list:
        """Get distinct schema (owner) names that have tables or views."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT DISTINCT owner FROM all_tables "
            "UNION "
            "SELECT DISTINCT owner FROM all_views "
            "ORDER BY 1"
        )
        schemas = [row[0] for row in cursor]
        cursor.close()
        conn.close()
        return schemas

    def get_tables(self, schema: str) -> list:
        """Get tables for a given schema."""
        self._validate_identifier(schema)
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT table_name FROM all_tables "
            "WHERE owner = :owner ORDER BY table_name",
            {"owner": schema.upper()},
        )
        tables = [row[0] for row in cursor]
        cursor.close()
        conn.close()
        return tables

    def get_views(self, schema: str) -> list:
        """Get views for a given schema."""
        self._validate_identifier(schema)
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT view_name FROM all_views "
            "WHERE owner = :owner ORDER BY view_name",
            {"owner": schema.upper()},
        )
        views = [row[0] for row in cursor]
        cursor.close()
        conn.close()
        return views

    def get_objects(self, schema: str) -> list:
        """Get all tables and views for a given schema."""
        self._validate_identifier(schema)
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT table_name AS object_name, 'TABLE' AS object_type "
            "FROM all_tables WHERE owner = :owner "
            "UNION ALL "
            "SELECT view_name AS object_name, 'VIEW' AS object_type "
            "FROM all_views WHERE owner = :owner "
            "ORDER BY 2, 1",
            {"owner": schema.upper()},
        )
        objects = []
        for row in cursor:
            objects.append({
                "object_name": row[0],
                "object_type": row[1],
            })
        cursor.close()
        conn.close()
        return objects

    def get_user_privileges(self, username: str) -> list:
        """Get all table/view privileges for a given user."""
        self._validate_identifier(username)
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT grantee, table_schema, table_name, grantor, privilege, grantable, type "
            "FROM all_tab_privs "
            "WHERE grantee = :grantee "
            "ORDER BY table_schema, table_name, privilege",
            {"grantee": username.upper()},
        )
        privileges = []
        for row in cursor:
            privileges.append({
                "grantee": row[0],
                "owner": row[1],
                "table_name": row[2],
                "grantor": row[3],
                "privilege": row[4],
                "grantable": row[5],
                "type": row[6],
            })
        cursor.close()
        conn.close()
        return privileges

    def grant_privilege(
        self, grantee: str, privilege: str, schema: str, object_name: str
    ) -> dict:
        """Grant a privilege on a table/view to a user."""
        self._validate_identifier(grantee)
        self._validate_identifier(schema)
        self._validate_identifier(object_name)
        self._validate_privilege(privilege)

        sql = f'GRANT {privilege} ON "{schema}"."{object_name}" TO "{grantee}"'

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql)
            conn.commit()
            cursor.close()
            conn.close()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def revoke_privilege(
        self, grantee: str, privilege: str, schema: str, object_name: str
    ) -> dict:
        """Revoke a privilege on a table/view from a user."""
        self._validate_identifier(grantee)
        self._validate_identifier(schema)
        self._validate_identifier(object_name)
        self._validate_privilege(privilege)

        sql = f'REVOKE {privilege} ON "{schema}"."{object_name}" FROM "{grantee}"'

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql)
            conn.commit()
            cursor.close()
            conn.close()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def _validate_identifier(name: str):
        """Validate Oracle identifier to prevent SQL injection."""
        if not name or not re.match(r"^[A-Za-z_#$][A-Za-z0-9_#$]*$", name):
            raise ValueError(f"Invalid Oracle identifier: {name}")

    @staticmethod
    def _validate_privilege(privilege: str):
        """Validate privilege keyword."""
        allowed = {"SELECT", "INSERT", "UPDATE", "DELETE", "ALL PRIVILEGES"}
        if privilege.upper() not in allowed:
            raise ValueError(f"Invalid privilege: {privilege}")
