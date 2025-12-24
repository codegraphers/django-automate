from django.db import connection

from .registry import DataChatRegistry
from .sqlpolicy import SQLPolicy


class QueryExecutor:
    def __init__(self):
        pass

    def run_query(self, sql: str, policy: SQLPolicy):
        """
        Executes a query safely.
        """
        # 1. Validate Policy (Redundant safety check)
        final_sql = policy.validate_and_optimize(sql)

        # 2. Execute
        with connection.cursor() as cursor:
            # TODO: Set statement timeout in Postgres
            # cursor.execute("SET statement_timeout = 5000;")

            cursor.execute(final_sql)
            columns = [col[0] for col in cursor.description]
            results = cursor.fetchall()

            return [dict(zip(columns, row, strict=False)) for row in results]


class SchemaIntrospector:
    @staticmethod
    def get_llm_context():
        """
        Returns a DDL-like string describing exposed tables for the LLM.
        """
        tables = DataChatRegistry.get_exposed_tables()
        lines = []
        for table_name, config in tables.items():
            fields = ", ".join(config["fields"])
            lines.append(f"CREATE TABLE {table_name} ({fields});")

        return "\n".join(lines)
