"""
Shared Anthropic Claude client used by every Claude-backed feature in this
app (resume upload pre-fill, AI Assistant chat widget, Resume Builder).
One place for client construction, forced-tool-use JSON calls, and
plain-text calls, so error handling / retries / auth / config stay
consistent across callers.
"""
import anthropic

from app.core.config import settings


class ClaudeCallError(Exception):
    """Raised when the Anthropic API call fails or returns no usable content."""


def _client() -> anthropic.Anthropic:
    return anthropic.Anthropic(
        api_key=settings.ANTHROPIC_API_KEY,
        base_url=settings.ANTHROPIC_BASE_URL or None,
    )


def call_with_tool(system: str, user_content: str, tool: dict, max_tokens: int = 4096) -> dict:
    """Forced tool-use call — guarantees a structured JSON response."""
    try:
        response = _client().messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=max_tokens,
            system=system,
            tools=[tool],
            tool_choice={"type": "tool", "name": tool["name"]},
            messages=[{"role": "user", "content": user_content}],
        )
    except anthropic.APIError as exc:
        raise ClaudeCallError(f"Anthropic API call failed: {exc}") from exc

    for block in response.content:
        if block.type == "tool_use" and block.name == tool["name"]:
            return block.input

    raise ClaudeCallError("Anthropic response did not include the expected tool call.")


def call_for_text(system: str, user_content: str, max_tokens: int = 512) -> str:
    """Plain free-text call."""
    try:
        response = _client().messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user_content}],
        )
    except anthropic.APIError as exc:
        raise ClaudeCallError(f"Anthropic API call failed: {exc}") from exc

    for block in response.content:
        if block.type == "text":
            return block.text

    raise ClaudeCallError("Anthropic response did not include a text block.")
