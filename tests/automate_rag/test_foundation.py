import uuid

import pytest

from automate_rag.models import Corpus, Document, KnowledgeSource, SourceType
from automate_rag.stores.base import IndexSpec, VectorUpsert
from automate_rag.stores.memory import MemoryVectorStore


@pytest.fixture
def store():
    return MemoryVectorStore()

def test_memory_store_basics(store):
    tenant = "t1"
    corpus_id = "c1"

    # 1. Ensure Index
    store.ensure_index(tenant_id=tenant, corpus_id=corpus_id, spec=IndexSpec())

    # 2. Upsert
    v1 = VectorUpsert(id="1", vector=[1.0, 0.0], metadata={"text": "hello"})
    v2 = VectorUpsert(id="2", vector=[0.0, 1.0], metadata={"text": "world"})
    store.upsert(tenant_id=tenant, corpus_id=corpus_id, vectors=[v1, v2])

    # 3. Query
    # Exact match v1
    hits = store.query(tenant_id=tenant, corpus_id=corpus_id, vector=[1.0, 0.0], top_k=2)
    assert len(hits) == 2
    assert hits[0].id == "1"
    assert hits[0].score > 0.99

    # Orthogonal
    hits_ortho = store.query(tenant_id=tenant, corpus_id=corpus_id, vector=[0.0, 1.0], top_k=1)
    assert hits_ortho[0].id == "2"

    # Filters
    hits_filtered = store.query(
        tenant_id=tenant,
        corpus_id=corpus_id,
        vector=[1.0, 0.0],
        top_k=2,
        filters={"text": "world"}
    )
    assert len(hits_filtered) == 1
    assert hits_filtered[0].id == "2"

    # 4. Delete
    store.delete_by_document(tenant_id=tenant, corpus_id=corpus_id, document_id="doc1") # No metadata set yet

    v3 = VectorUpsert(id="3", vector=[0.5, 0.5], metadata={"document_id": "doc_x"})
    store.upsert(tenant_id=tenant, corpus_id=corpus_id, vectors=[v3])
    store.delete_by_document(tenant_id=tenant, corpus_id=corpus_id, document_id="doc_x")

    hits_del = store.query(tenant_id=tenant, corpus_id=corpus_id, vector=[0.5, 0.5], top_k=10)
    # 1 and 2 still exist, 3 gone
    assert len(hits_del) == 2

@pytest.mark.django_db
def test_rag_models_lifecycle():
    c = Corpus.objects.create(tenant_id="t1", name="Test Corpus")
    s = KnowledgeSource.objects.create(
        tenant_id="t1", corpus=c, type=SourceType.LOCAL_UPLOAD, name="Uploads"
    )
    d = Document.objects.create(
        tenant_id="t1", corpus=c, source=s, external_ref="file.txt"
    )

    assert d.status == "new"
    assert c.documents.count() == 1

@pytest.mark.django_db
def test_ingestion_service(store):
    from automate_rag.service import IngestionService

    c = Corpus.objects.create(tenant_id="t1", name="Ingest Corpus")
    d = Document.objects.create(tenant_id="t1", corpus=c, external_ref="test.txt")

    svc = IngestionService(vector_store=store)
    svc.ingest_document(d)

    d.refresh_from_db()
    assert d.status == "indexed"
    assert d.chunks.count() > 0

    # Verify store has vectors
    hits = store.query(tenant_id="t1", corpus_id=str(c.id), vector=[0.1]*1536, top_k=1)
    assert len(hits) == 1

