"""
Thin wrapper around the Razorpay SDK. Key Secret and Webhook Secret are
read only from server-side env vars (app.core.config.settings) — never
stored in the DB, never sent to the frontend. Only the public Key ID is
exposed to the browser (required by Razorpay's Checkout.js).
"""
from functools import lru_cache

import razorpay
from razorpay.errors import SignatureVerificationError

from app.core.config import settings


def razorpay_configured() -> bool:
    return bool(settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET)


@lru_cache
def get_razorpay_client() -> razorpay.Client:
    return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


def verify_payment_signature(order_id: str, payment_id: str, signature: str) -> bool:
    """Verifies the signature Razorpay Checkout.js returns to the browser
    after a successful payment. Raises SignatureVerificationError (via the
    SDK) if invalid."""
    client = get_razorpay_client()
    try:
        return client.utility.verify_payment_signature({
            "razorpay_order_id": order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": signature,
        })
    except SignatureVerificationError:
        return False


def verify_webhook_signature(body: bytes, signature: str) -> bool:
    """Verifies the X-Razorpay-Signature header on an incoming webhook
    request against RAZORPAY_WEBHOOK_SECRET."""
    if not settings.RAZORPAY_WEBHOOK_SECRET:
        return False
    client = get_razorpay_client()
    try:
        return client.utility.verify_webhook_signature(
            body.decode("utf-8"), signature, settings.RAZORPAY_WEBHOOK_SECRET
        )
    except SignatureVerificationError:
        return False
