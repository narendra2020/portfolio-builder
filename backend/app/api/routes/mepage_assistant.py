"""
Public website assistant endpoints (no login): POST /api/public/mepage-assistant/chat.

Cost-control and abuse-control layers, in order:
  1. Feature flag and Origin allow-list (browser traffic from mepage.in only)
  2. Request size limits (Pydantic) and a body cap
  3. Per-IP and global daily rate limits (services/mepage_assistant.py)
  4. Short LLM timeout, capped output tokens, capped history
Nginx adds limit_req in front of this (see the deploy notes).

Message text is never written to the database or the logs.
"""
import logging

from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services import mepage_assistant as svc

logger = logging.getLogger("mepage_assistant")

router = APIRouter(prefix="/api/public/mepage-assistant", tags=["mepage-assistant-public"])


class HistoryTurn(BaseModel):
    role: str = Field(..., max_length=12)
    content: str = Field(..., max_length=2000)


class AssistantChatIn(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    history: list[HistoryTurn] = Field(default_factory=list, max_length=40)


class AssistantChatOut(BaseModel):
    answer: str
    fallback: bool = False


class AssistantInfoOut(BaseModel):
    name: str = "MePage Guide"
    max_message_chars: int
    suggestions: list[str]


SUGGESTIONS = [
    "What products does MePage offer?",
    "How does the QR Code Store Builder work?",
    "How do I create a portfolio website?",
    "Is there a free trial?",
]


def _client_ip(request: Request) -> str:
    if settings.MEPAGE_ASSISTANT_TRUST_PROXY:
        forwarded = request.headers.get("x-forwarded-for", "")
        if forwarded:
            return forwarded.split(",")[-1].strip() or "unknown"   # last hop = the one our proxy appended
        real = request.headers.get("x-real-ip")
        if real:
            return real.strip()
    return request.client.host if request.client else "unknown"


def _check_enabled_and_origin(request: Request) -> None:
    if not settings.MEPAGE_ASSISTANT_ENABLED:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
    origin = request.headers.get("origin")
    # Browsers always send Origin on cross-origin POSTs. A request with no
    # Origin comes from a non-browser client; allow it (the rate limits still
    # apply) but a present-and-wrong Origin is rejected.
    if origin and origin not in settings.mepage_assistant_origins:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Origin not allowed")


def _cors(response: Response, request: Request) -> None:
    origin = request.headers.get("origin")
    if origin and origin in settings.mepage_assistant_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Vary"] = "Origin"


@router.options("/chat", include_in_schema=False)
@router.options("/info", include_in_schema=False)
def preflight(request: Request, response: Response):
    origin = request.headers.get("origin")
    if not origin or origin not in settings.mepage_assistant_origins:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Origin not allowed")
    response.headers["Access-Control-Allow-Origin"] = origin
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Max-Age"] = "600"
    response.headers["Vary"] = "Origin"
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/info", response_model=AssistantInfoOut)
def info(request: Request, response: Response):
    _check_enabled_and_origin(request)
    _cors(response, request)
    return AssistantInfoOut(max_message_chars=settings.MEPAGE_ASSISTANT_MAX_MESSAGE_CHARS, suggestions=SUGGESTIONS)


@router.post("/chat", response_model=AssistantChatOut)
def chat(payload: AssistantChatIn, request: Request, response: Response):
    _check_enabled_and_origin(request)
    _cors(response, request)

    message = svc.clean_text(payload.message, 100_000)
    if not message:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Message cannot be empty.")
    if len(message) > settings.MEPAGE_ASSISTANT_MAX_MESSAGE_CHARS:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"Please keep your message under {settings.MEPAGE_ASSISTANT_MAX_MESSAGE_CHARS} characters.",
        )

    try:
        svc.check_and_count(_client_ip(request))
    except svc.RateLimited as exc:
        response.headers["Retry-After"] = str(exc.retry_after)
        detail = ("You're sending messages quickly. Please wait a little and try again."
                  if exc.scope == "ip" else
                  "The assistant is very busy today. Please try again later or email care@mepage.in.")
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, detail, headers={"Retry-After": str(exc.retry_after)})

    try:
        answer = svc.ask([t.model_dump() for t in payload.history], message)
        return AssistantChatOut(answer=answer)
    except svc.MepageAssistantError as exc:
        logger.warning("mepage assistant LLM failure: %s", type(exc).__name__)   # no message text, no secrets
        return AssistantChatOut(answer=svc.fallback_answer(message), fallback=True)
    except Exception:
        logger.exception("mepage assistant unexpected failure")
        return AssistantChatOut(answer=svc.fallback_answer(message), fallback=True)
