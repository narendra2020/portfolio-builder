"""
Replaceable SMS/WhatsApp OTP delivery provider interface.

DevConsoleOTPProvider logs the OTP to the console instead of sending it,
and is used while settings.OTP_MODE == "dev_fixed". WhatsAppBusinessProvider
(app/providers/whatsapp_provider.py) sends it via the Meta Graph API and is
used when settings.OTP_MODE == "provider" — see
app/services/otp_service.py's get_sms_provider().
"""
from typing import Protocol

from pydantic import BaseModel


class SMSDeliveryResult(BaseModel):
    success: bool
    provider_reference: str | None = None


class SMSProvider(Protocol):
    async def send_otp(self, phone_number: str, otp: str, transaction_id: str) -> SMSDeliveryResult:
        ...


class DevConsoleOTPProvider:
    """Development-only provider: prints the OTP instead of sending it."""

    async def send_otp(self, phone_number: str, otp: str, transaction_id: str) -> SMSDeliveryResult:
        print(f"[DevConsoleOTPProvider] OTP for {phone_number} (txn {transaction_id}): {otp}")
        return SMSDeliveryResult(success=True, provider_reference=f"dev-console-{transaction_id}")
