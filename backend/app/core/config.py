"""
Application configuration, loaded from environment variables / .env file.
"""
from functools import lru_cache
from typing import List, Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Database ---
    DATABASE_URL: str = "postgresql+psycopg2://portfolio:changeme@localhost:5433/portfolio_builder_db"

    # --- Auth / JWT ---
    JWT_SECRET_KEY: str = "insecure-dev-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # --- Mobile number lookup hashing (HMAC-SHA256 keyed hash, see
    # app/core/security.py::hmac_lookup_hash) ---
    MOBILE_LOOKUP_KEY: str = "insecure-dev-lookup-key-change-me"

    # --- OTP ---
    # "dev_fixed": every OTP request/verify uses FIXED_DEV_OTP and is
    # printed to the console via DevConsoleOTPProvider — no real SMS/
    # WhatsApp provider is wired up yet. Switch to "provider" once one is
    # integrated (see app/providers/sms_provider.py); no other code needs
    # to change.
    OTP_MODE: Literal["dev_fixed", "provider"] = "dev_fixed"
    FIXED_DEV_OTP: str = "123456"
    OTP_EXPIRE_MINUTES: int = 10
    OTP_MAX_ATTEMPTS: int = 5
    OTP_RESEND_COOLDOWN_SECONDS: int = 30

    # --- WhatsApp Business API (Meta Graph API) — used when OTP_MODE == "provider" ---
    WHATSAPP_ACCESS_TOKEN: str = ""
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_API_VERSION: str = "v25.0"
    WHATSAPP_TEMPLATE_NAME: str = "otp_verification"
    WHATSAPP_TEMPLATE_LANG: str = "en"

    # --- Seed / bootstrap ---
    DEFAULT_ADMIN_MOBILE: str = "+910000000000"
    DEFAULT_ADMIN_PASSWORD: str = "changeme123"

    # --- CORS ---
    ALLOWED_ORIGINS: str = "http://localhost:5174,http://localhost:3000"

    # --- Publishing ---
    PUBLISHED_SITES_DIR: str = "/app/published_sites"
    BASE_DOMAIN: str = "mepage.in"
    PUBLIC_SCHEME: str = "https"
    PUBLIC_PORT: str = ""

    # --- Resume upload + LLM pre-fill ---
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_BASE_URL: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-5"
    RESUME_UPLOAD_DIR: str = "/app/uploads/resumes"

    # --- Media (profile/project image) upload, served statically at /uploads ---
    UPLOADS_DIR: str = "/app/uploads"

    # --- AI Resume Builder: rendered PDF export audit copies ---
    RESUME_EXPORT_DIR: str = "/app/uploads/resume_exports"

    # --- AI Assistant chat widget ---
    AI_ASSISTANT_MAX_QA_PAIRS: int = 20
    AI_ASSISTANT_QUESTION_MAX_LENGTH: int = 150
    AI_ASSISTANT_ANSWER_MAX_LENGTH: int = 500
    AI_ASSISTANT_DAILY_MESSAGE_LIMIT: int = 200
    AI_ASSISTANT_ADD_ON_PRICE_RUPEES: int = 499

    # --- MePage website assistant (public bot on mepage.in) ---
    MEPAGE_ASSISTANT_ENABLED: bool = True
    # Browser origins allowed to call the public chat endpoint.
    MEPAGE_ASSISTANT_ALLOWED_ORIGINS: str = "https://mepage.in,https://www.mepage.in"
    MEPAGE_ASSISTANT_MAX_MESSAGE_CHARS: int = 500
    MEPAGE_ASSISTANT_MAX_HISTORY_TURNS: int = 6      # past user+assistant turns sent to the model
    MEPAGE_ASSISTANT_MAX_OUTPUT_TOKENS: int = 400
    MEPAGE_ASSISTANT_IP_LIMIT: int = 15              # messages per IP per window
    MEPAGE_ASSISTANT_IP_WINDOW_SECONDS: int = 600
    MEPAGE_ASSISTANT_DAILY_LIMIT: int = 2000         # all visitors combined, per UTC day
    # Set true only when this API sits behind your own reverse proxy (nginx).
    # Then the client IP is read from X-Forwarded-For. Leave false otherwise,
    # because the header can be forged by anyone who reaches the API directly.
    MEPAGE_ASSISTANT_TRUST_PROXY: bool = False

    # Exactly one LLM provider must be enabled (validated at startup, see
    # app/core/llm_config_check.py). "anthropic" reuses ANTHROPIC_API_KEY /
    # ANTHROPIC_BASE_URL / ANTHROPIC_MODEL above.
    LLM_PROVIDER: Literal["anthropic", "azure_openai"] = "anthropic"
    AZURE_OPENAI_API_KEY: str = ""
    AZURE_OPENAI_ENDPOINT: str = ""
    AZURE_OPENAI_DEPLOYMENT: str = ""
    AZURE_OPENAI_API_VERSION: str = "2024-10-21"

    # --- Razorpay (payment gateway) ---
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = ""

    # --- Billing ---
    UPGRADE_PRICE_RUPEES: int = 999
    # QR Store Builder Pro plan price (product "qr_store_pro"). 0 = not sold.
    QR_STORE_PRO_PRICE_RUPEES: int = 0
    # QR Store "Split Bill" plan (product "qr_split_bill") and the "Pro + Split Bill"
    # bundle (product "qr_pro_split"). 0 = not sold.
    QR_SPLIT_BILL_PRICE_RUPEES: int = 0
    QR_PRO_SPLIT_PRICE_RUPEES: int = 0

    @property
    def mepage_assistant_origins(self) -> List[str]:
        return [o.strip() for o in self.MEPAGE_ASSISTANT_ALLOWED_ORIGINS.split(",") if o.strip()]

    @property
    def cors_origins(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    def build_public_url(self, host: str) -> str:
        port_suffix = f":{self.PUBLIC_PORT}" if self.PUBLIC_PORT else ""
        return f"{self.PUBLIC_SCHEME}://{host}{port_suffix}"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
