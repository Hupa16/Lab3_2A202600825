"""LLM provider factory shared by chatbot and agent runners."""
import os
from typing import Optional

from dotenv import load_dotenv

from src.core.gemini_provider import GeminiProvider
from src.core.llm_provider import LLMProvider
from src.core.local_provider import LocalProvider
from src.core.openai_provider import OpenAIProvider


def create_provider(env_path: Optional[str] = None) -> LLMProvider:
    load_dotenv(env_path)
    provider_name = os.getenv("DEFAULT_PROVIDER", "openai").lower()
    model = os.getenv("DEFAULT_MODEL", "gpt-4o")

    if provider_name in ("google", "gemini"):
        return GeminiProvider(model_name=model, api_key=os.getenv("GEMINI_API_KEY"))
    if provider_name == "local":
        path = os.getenv("LOCAL_MODEL_PATH", "./models/Phi-3-mini-4k-instruct-q4.gguf")
        return LocalProvider(model_path=path)
    return OpenAIProvider(model_name=model, api_key=os.getenv("OPENAI_API_KEY"))
