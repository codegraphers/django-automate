"""
PGVector Store Adapter
Using pgvector python client or raw SQL
"""

import logging
from typing import Any

from django.db import connection

from .base import SearchResult, VectorStore

logger = logging.getLogger(__name__)

try:
    import pgvector
except ImportError:
    pgvector = None


class PGVectorStore(VectorStore):
    """PGVector using raw SQL for flexibility."""

    def __init__(self, table_name: str, connection_name: str = "default"):
        self.table_name = table_name
        self.connection_name = connection_name

    def search(self, embedding: list[float], top_k: int, filters: dict[str, Any] | None = None) -> list[SearchResult]:
        # Naive SQL construction - vulnerable to injection if table_name not safe
        # In prod, restrict table_name or use models
        sql = f"""
            SELECT id, content, metadata, 1 - (embedding <=> %s::vector) as similarity
            FROM {self.table_name}
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """

        # Handle filters - complex logic needed here
        # For now, skip filters for MVP

        with connection.cursor() as cursor:
            # Need to format embedding as string for older pgvector or pass list depending on driver
            # pyscopg3 handles list native with %s::vector

            # Note: This implies the table has 'content', 'metadata', 'embedding' columns
            cursor.execute(sql, [embedding, embedding, top_k])
            rows = cursor.fetchall()

        results = []
        for row in rows:
            results.append(SearchResult(source_id=str(row[0]), text=row[1], metadata=row[2] or {}, score=row[3]))

        return results

    def health(self) -> dict[str, Any]:
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return {"healthy": True, "message": "Connected to Postgres"}
        except Exception as e:
            return {"healthy": False, "message": str(e)}
