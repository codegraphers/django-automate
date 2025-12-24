from django.db import connection


class DbCapabilities:
    """
    Detects features of the underlying database to enable optimizations.
    """

    @property
    def supports_skip_locked(self) -> bool:
        vendor = connection.vendor
        if vendor == "postgresql":
            return True  # Generally 9.5+
        if vendor == "mysql":
            # MySQL 8.0+ supports SKIP LOCKED
            return connection.mysql_version >= (8, 0, 1)
        return vendor == "oracle"

    @property
    def supports_gin_index(self) -> bool:
        return connection.vendor == "postgresql"
