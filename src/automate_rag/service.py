
from .models import Chunk, Document, DocumentStatus
from .stores.base import VectorStore, VectorUpsert


class IngestionService:
    def __init__(self, vector_store: VectorStore):
        self.store = vector_store

    def ingest_document(self, doc: Document):
        """
        Orchestrates the ingestion lifecycle for a single document.
        In a real system, these would be separate async steps.
        """
        try:
            # 1. Parse
            text = self._parse(doc)
            doc.status = DocumentStatus.PARSED
            doc.save()

            # 2. Chunk
            chunks = self._chunk(doc, text)
            doc.status = DocumentStatus.CHUNKED
            doc.save()

            # 3. Embed & Index
            self._embed_and_index(doc, chunks)
            doc.status = DocumentStatus.INDEXED
            doc.save()

        except Exception as e:
            doc.status = DocumentStatus.FAILED
            doc.save()
            raise e

    def _parse(self, doc: Document) -> str:
        # Resolve artifact or fetch URL
        # Mock implementation
        return "This is the content of the document."

    def _chunk(self, doc: Document, text: str) -> list[Chunk]:
        # Naive splitting
        parts = text.split(". ")
        chunks = []
        for i, part in enumerate(parts):
            chunk = Chunk.objects.create(
                tenant_id=doc.tenant_id,
                corpus=doc.corpus,
                document=doc,
                chunk_index=i,
                text_preview=part[:50],
                token_count=len(part.split())
            )
            chunks.append(chunk)
        return chunks

    def _embed_and_index(self, doc: Document, chunks: list[Chunk]):
        # Mock embedding
        upserts = []
        for chunk in chunks:
            # Fake vector
            vec = [0.1] * 1536
            upserts.append(VectorUpsert(
                id=str(chunk.id),
                vector=vec,
                metadata={
                    "document_id": str(doc.id),
                    "corpus_id": str(doc.corpus.id),
                    "text": chunk.text_preview
                }
            ))

        self.store.upsert(
            tenant_id=doc.tenant_id,
            corpus_id=str(doc.corpus.id),
            vectors=upserts
        )
