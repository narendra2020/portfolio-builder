"""
Fails fast at startup if the configured LLM_PROVIDER is missing its
required credentials, instead of surfacing a confusing error on the
first chat request.
"""
from app.core.config import settings


def check_llm_config() -> None:
    if settings.LLM_PROVIDER == "anthropic":
        if not settings.ANTHROPIC_API_KEY:
            raise RuntimeError(
                "LLM_PROVIDER=anthropic requires ANTHROPIC_API_KEY to be set."
            )
    elif settings.LLM_PROVIDER == "azure_openai":
        missing = [
            name
            for name, value in (
                ("AZURE_OPENAI_API_KEY", settings.AZURE_OPENAI_API_KEY),
                ("AZURE_OPENAI_ENDPOINT", settings.AZURE_OPENAI_ENDPOINT),
                ("AZURE_OPENAI_DEPLOYMENT", settings.AZURE_OPENAI_DEPLOYMENT),
            )
            if not value
        ]
        if missing:
            raise RuntimeError(
                f"LLM_PROVIDER=azure_openai requires {', '.join(missing)} to be set."
            )
