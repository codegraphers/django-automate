from __future__ import annotations
from typing import Any, Dict, List
import logging

from ..types import ChatRequest, ChatResponse, CostEstimate, Usage
from ..errors import LLMError, LLMErrorCode
from ..pricing import ModelPricing
from .base import ProviderAdapter

logger = logging.getLogger(__name__)

class GeminiAdapter(ProviderAdapter):
    code = "google" # or gemini

    @property
    def capabilities(self) -> Dict[str, bool]:
        return {
            "supports_streaming": False,
            "supports_tools": False, # Simple impl for now
            "supports_vision": True
        }

    def chat(self, req: ChatRequest, *, api_key: str) -> ChatResponse:
        try:
            import google.generativeai as genai
        except ImportError:
            raise LLMError(LLMErrorCode.INTERNAL_ERROR, "google-generativeai package not installed")

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(req.model)
        
        # Convert messages
        # Gemini expects history list + last message
        # Simplified: Just grab last user message
        
        last_msg = req.messages[-1].content
        
        try:
            # Generate
            # Note: generation_config could handle temp/max_tokens
            generation_config = genai.types.GenerationConfig(
                temperature=req.temperature,
                max_output_tokens=req.max_tokens
            )
            
            resp = model.generate_content(last_msg, generation_config=generation_config)
            
            return ChatResponse(
                content=resp.text,
                role="model",
                usage=Usage(input_tokens=0, output_tokens=0), # Usage not trivial in simple response
            )

        except Exception as e:
            raise self.normalize_error(e)

    def estimate_cost(self, req: ChatRequest) -> CostEstimate:
        return CostEstimate(total_cost_usd=0.0, currency="USD", details={})

    def normalize_error(self, exc: Exception) -> LLMError:
        return LLMError(LLMErrorCode.PROVIDER_ERROR, f"Gemini Error: {exc}", retryable=False)
