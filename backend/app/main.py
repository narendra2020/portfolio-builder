"""
FastAPI application entry point.

Run locally with:
    uvicorn app.main:app --reload --port 8000
"""
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import (
    admin_billing,
    admin_questionnaire,
    admin_taxonomy,
    admin_templates,
    admin_users,
    ai_assistant,
    auth,
    billing,
    layout,
    media,
    mepage_assistant,
    number_verification,
    profile,
    publish,
    questionnaire,
    resume,
    resumes,
    taxonomy,
    templates,
)
from app.core.config import settings
from app.core.llm_config_check import check_llm_config

check_llm_config()

BACKEND_DIR = Path(__file__).resolve().parent.parent
AI_ASSISTANT_WIDGET_JS = BACKEND_DIR / "app" / "static" / "ai_assistant_widget.js"
TEMPLATE_ASSETS_DIR = BACKEND_DIR / "app" / "templates" / "assets"

app = FastAPI(
    title="Portfolio Builder API",
    description="Mobile-OTP-authenticated portfolio website builder: auth, RBAC, "
                "taxonomy, profile onboarding, the dynamic questionnaire engine, "
                "the template registry, the drag-and-drop layout editor, and "
                "static publishing.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(number_verification.router)
app.include_router(taxonomy.router)
app.include_router(admin_taxonomy.router)
app.include_router(profile.router)
app.include_router(resume.router)
app.include_router(resumes.router)
app.include_router(media.router)
app.include_router(questionnaire.router)
app.include_router(admin_questionnaire.router)
app.include_router(templates.router)
app.include_router(admin_templates.router)
app.include_router(admin_users.router)
app.include_router(layout.router)
app.include_router(publish.router)
app.include_router(billing.router)
app.include_router(admin_billing.router)
app.include_router(ai_assistant.router)
app.include_router(ai_assistant.public_router)
app.include_router(mepage_assistant.router)

os.makedirs(settings.UPLOADS_DIR, exist_ok=True)
# Mounted under /api so it flows through the same reverse-proxy path
# (Vite dev proxy / frontend nginx) as every other backend route.
app.mount("/api/uploads", StaticFiles(directory=settings.UPLOADS_DIR), name="uploads")
# Build-time template assets (thumbnails, default art) — distinct from
# UPLOADS_DIR, which holds user-uploaded content.
app.mount("/api/template-assets", StaticFiles(directory=TEMPLATE_ASSETS_DIR), name="template-assets")


@app.get("/api/health", tags=["health"])
def health_check():
    return {"status": "ok", "service": "portfolio-builder-api"}


@app.get("/api/ai-assistant-widget.js", include_in_schema=False)
def ai_assistant_widget_js():
    return FileResponse(AI_ASSISTANT_WIDGET_JS, media_type="application/javascript")
