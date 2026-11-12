"""
WhatsApp Business API (Meta Graph API) OTP delivery provider. Sends the
"otp_verification" template message with the OTP in both the body and
the copy-code button, per Meta's recommended OTP template layout. Used
when settings.OTP_MODE == "provider" (see app/services/otp_service.py's
get_sms_provider()).
"""
import httpx

from app.core.config import settings
from app.providers.sms_provider import SMSDeliveryResult


class WhatsAppBusinessProvider:
    async def send_otp(self, phone_number: str, otp: str, transaction_id: str) -> SMSDeliveryResult:
        to = phone_number.lstrip("+")
        url = (
            f"https://graph.facebook.com/{settings.WHATSAPP_API_VERSION}/"
            f"{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
        )
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": settings.WHATSAPP_TEMPLATE_NAME,
                "language": {"code": settings.WHATSAPP_TEMPLATE_LANG},
                "components": [
                    {"type": "body", "parameters": [{"type": "text", "text": otp}]},
                    {
                        "type": "button",
                        "sub_type": "url",
                        "index": "0",
                        "parameters": [{"type": "text", "text": otp}],
                    },
                ],
            },
        }
        headers = {
            "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload, headers=headers)
        except httpx.HTTPError:
            return SMSDeliveryResult(success=False, provider_reference=None)

        if response.status_code >= 400:
            return SMSDeliveryResult(success=False, provider_reference=None)

        message_id = None
        try:
            message_id = response.json()["messages"][0]["id"]
        except (KeyError, IndexError, ValueError):
            pass
        return SMSDeliveryResult(success=True, provider_reference=message_id)
