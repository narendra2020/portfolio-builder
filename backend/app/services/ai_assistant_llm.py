"""
Answers a visitor's question about a portfolio owner, using whichever
LLM provider is configured (settings.LLM_PROVIDER). Mirrors the
structure of resume_llm.py: a settings-driven client built per call, a
single custom exception, provider SDK errors translated rather than
leaked.
"""
import openai

from app.core.config import settings
from app.services.claude_client import ClaudeCallError, call_for_text

_SYSTEM_PROMPT_TEMPLATE = (
    "You are the AI Assistant on {owner_name}'s portfolio website, answering "
    "questions from visitors (e.g. hiring managers) about {owner_name}. Answer "
    "ONLY using the knowledge provided below — never invent facts, employers, "
    "dates, or skills that aren't present. Speak about {owner_name} in the "
    "third person. If the knowledge provided doesn't answer the question, say "
    "so politely and suggest the visitor contact {owner_name} directly. Keep "
    "answers concise (a few sentences).\n\n"
    "Knowledge:\n{knowledge_context}"
)


class AiAssistantLLMError(Exception):
    """Raised when the configured LLM provider call fails or returns no usable answer."""


def answer_question(knowledge_context: str, question: str, owner_name: str) -> str:
    system_prompt = _SYSTEM_PROMPT_TEMPLATE.format(
        owner_name=owner_name, knowledge_context=knowledge_context or "(no information provided)"
    )
    if settings.LLM_PROVIDER == "azure_openai":
        return _answer_with_azure_openai(system_prompt, question)
    return _answer_with_anthropic(system_prompt, question)


def _answer_with_anthropic(system_prompt: str, question: str) -> str:
    try:
        return call_for_text(system_prompt, question, max_tokens=512)
    except ClaudeCallError as exc:
        raise AiAssistantLLMError(str(exc)) from exc


def _answer_with_azure_openai(system_prompt: str, question: str) -> str:
    client = openai.AzureOpenAI(
        api_key=settings.AZURE_OPENAI_API_KEY,
        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        api_version=settings.AZURE_OPENAI_API_VERSION,
    )
    try:
        response = client.chat.completions.create(
            model=settings.AZURE_OPENAI_DEPLOYMENT,
            max_tokens=512,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question},
            ],
        )
    except openai.OpenAIError as exc:
        raise AiAssistantLLMError(f"Azure OpenAI API call failed: {exc}") from exc

    choice = response.choices[0] if response.choices else None
    if not choice or not choice.message or not choice.message.content:
        raise AiAssistantLLMError("Azure OpenAI response did not include an answer.")
    return choice.message.content
