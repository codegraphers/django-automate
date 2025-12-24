"""
OpenAI Embeddings Implementation
"""
import logging
from typing import List

from .base import Embeddings
# Should wrap the openai client gracefully if not installed
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

logger = logging.getLogger(__name__)

class OpenAIEmbeddings(Embeddings):
    """OpenAI embeddings wrapper."""
    
    def __init__(self, api_key: str, model: str = "text-embedding-ada-002", api_base: str = None):
        if not OpenAI:
            raise ImportError("openai package is not installed")
        
        self.client = OpenAI(api_key=api_key, base_url=api_base)
        self.model = model
        self._dimension = None
    
    def embed_query(self, text: str) -> List[float]:
        # Helper to remove newlines which can affect performance
        text = text.replace("\n", " ")
        response = self.client.embeddings.create(input=[text], model=self.model)
        return response.data[0].embedding
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        # TODO: Handle batching if texts > 2048
        texts = [t.replace("\n", " ") for t in texts]
        response = self.client.embeddings.create(input=texts, model=self.model)
        return [data.embedding for data in response.data]
    
    @property
    def dimension(self) -> int:
        if self._dimension is None:
            # Lazy load dimension by embedding a dummy token
            # Or use known dimensions for standard models
            if self.model == "text-embedding-ada-002":
                self._dimension = 1536
            elif self.model == "text-embedding-3-small":
                self._dimension = 1536
            elif self.model == "text-embedding-3-large":
                self._dimension = 3072
            else:
                self._dimension = len(self.embed_query("test"))
        return self._dimension
