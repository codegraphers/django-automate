"""
RAG URL Configuration

Routes:
- /api/rag/{slug}/query - POST - Execute retrieval query
- /api/rag/{slug}/health - GET - Check endpoint health
"""
from django.urls import path
from .api import query

app_name = 'rag'

urlpatterns = [
    path('<slug:slug>/query', query.query_endpoint, name='query'),
    path('<slug:slug>/health', query.health_endpoint, name='health'),
]
