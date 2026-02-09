import ldap3
from ldap3 import ALL, NTLM, SUBTREE, Connection, Server
from ldap3.core.exceptions import LDAPBindError, LDAPSocketOpenError
from ldap3.utils.conv import escape_filter_chars


class LDAPService:
    def __init__(self, config):
        self.server_url = config["LDAP_SERVER"]
        self.base_dn = config["LDAP_BASE_DN"]
        self.bind_user = config["LDAP_BIND_USER"]
        self.bind_password = config["LDAP_BIND_PASSWORD"]
        self.domain = config["LDAP_DOMAIN"]
        self.user_search_base = config.get(
            "LDAP_USER_SEARCH_BASE", self.base_dn
        )
        self.group_search_base = config.get(
            "LDAP_GROUP_SEARCH_BASE", self.base_dn
        )

    def authenticate(self, username: str, password: str) -> dict | None:
        """
        Authenticate user against Active Directory using NTLM bind.
        Returns user attributes dict on success, None on failure.
        """
        server = Server(
            self.server_url,
            get_info=ALL,
            use_ssl=self.server_url.startswith("ldaps"),
        )
        user_dn = f"{self.domain}\\{username}"

        try:
            conn = Connection(
                server,
                user=user_dn,
                password=password,
                authentication=NTLM,
                auto_bind=True,
            )
        except (LDAPBindError, LDAPSocketOpenError):
            return None

        search_filter = f"(sAMAccountName={escape_filter_chars(username)})"
        conn.search(
            search_base=self.user_search_base,
            search_filter=search_filter,
            search_scope=SUBTREE,
            attributes=[
                "cn",
                "mail",
                "displayName",
                "department",
                "title",
                "distinguishedName",
                "memberOf",
                "sAMAccountName",
            ],
        )

        if not conn.entries:
            conn.unbind()
            return None

        entry = conn.entries[0]
        user_data = {
            "username": str(entry.sAMAccountName),
            "email": str(entry.mail) if entry.mail else None,
            "full_name": str(entry.cn),
            "display_name": (
                str(entry.displayName) if entry.displayName else str(entry.cn)
            ),
            "department": str(entry.department) if entry.department else None,
            "title": str(entry.title) if entry.title else None,
            "dn": str(entry.distinguishedName),
            "groups": (
                [str(g) for g in entry.memberOf] if entry.memberOf else []
            ),
        }

        conn.unbind()
        return user_data

    def search_users(self, query: str, limit: int = 20) -> list:
        """Search AD for users matching query (admin use)."""
        server = Server(self.server_url, get_info=ALL)
        conn = Connection(
            server,
            user=self.bind_user,
            password=self.bind_password,
            authentication=NTLM,
            auto_bind=True,
        )

        safe_query = escape_filter_chars(query)
        search_filter = (
            f"(&(objectClass=user)(objectCategory=person)"
            f"(|(cn=*{safe_query}*)(sAMAccountName=*{safe_query}*)(mail=*{safe_query}*)))"
        )
        conn.search(
            search_base=self.user_search_base,
            search_filter=search_filter,
            search_scope=SUBTREE,
            attributes=["cn", "mail", "sAMAccountName", "department"],
            size_limit=limit,
        )

        results = []
        for entry in conn.entries:
            results.append(
                {
                    "username": str(entry.sAMAccountName),
                    "full_name": str(entry.cn),
                    "email": str(entry.mail) if entry.mail else None,
                    "department": (
                        str(entry.department) if entry.department else None
                    ),
                }
            )

        conn.unbind()
        return results

    def get_groups(self, limit: int = 100) -> list:
        """Get AD groups for sync."""
        server = Server(self.server_url, get_info=ALL)
        conn = Connection(
            server,
            user=self.bind_user,
            password=self.bind_password,
            authentication=NTLM,
            auto_bind=True,
        )

        search_filter = "(objectClass=group)"
        conn.search(
            search_base=self.group_search_base,
            search_filter=search_filter,
            search_scope=SUBTREE,
            attributes=["cn", "distinguishedName", "description", "member"],
            size_limit=limit,
        )

        results = []
        for entry in conn.entries:
            results.append(
                {
                    "name": str(entry.cn),
                    "dn": str(entry.distinguishedName),
                    "description": (
                        str(entry.description) if entry.description else None
                    ),
                    "members": (
                        [str(m) for m in entry.member] if entry.member else []
                    ),
                }
            )

        conn.unbind()
        return results
