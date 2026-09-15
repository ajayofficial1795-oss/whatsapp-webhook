import base64
import hashlib
import hmac
import time

import httpx

from app.config import settings


def verify_razorpay_signature(raw_body: bytes, signature: str | None) -> bool:
    if not settings.razorpay_webhook_secret or not signature:
        return False

    expected = hmac.new(
        settings.razorpay_webhook_secret.encode(),
        raw_body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


async def create_payment_link(booking: dict) -> dict:
    if settings.payment_provider.lower() != "razorpay":
        return {
            "payment_provider": "manual",
            "payment_link": settings.manual_payment_url,
            "payment_reference": booking["booking_id"],
            "payment_status": "pending_manual_payment",
        }

    if not settings.razorpay_key_id or not settings.razorpay_key_secret:
        raise ValueError("Missing Razorpay credentials")

    auth = base64.b64encode(f"{settings.razorpay_key_id}:{settings.razorpay_key_secret}".encode()).decode()
    body = {
        "amount": int(booking["total_price"]) * 100,
        "currency": "INR",
        "accept_partial": False,
        "reference_id": booking["booking_id"],
        "description": f"{booking['trek_name']} booking for {booking['trek_people']} people on {booking['trek_date']}",
        "customer": {
            "name": booking.get("customer_name"),
            "contact": booking.get("customer_phone"),
            "email": booking.get("customer_email"),
        },
        "notify": {
            "sms": bool(booking.get("customer_phone")),
            "email": bool(booking.get("customer_email")),
        },
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            "https://api.razorpay.com/v1/payment_links",
            headers={"Authorization": f"Basic {auth}", "Content-Type": "application/json"},
            json=body,
        )

    response_body = response.json()
    if response.status_code >= 400:
        raise ValueError(response_body.get("error", {}).get("description", "Razorpay payment link creation failed"))

    return {
        "payment_provider": "razorpay",
        "payment_link": response_body["short_url"],
        "payment_reference": response_body["id"],
        "payment_status": response_body.get("status", "created"),
    }


def parse_razorpay_webhook(payload: dict) -> dict:
    payment = payload.get("payload", {}).get("payment", {}).get("entity", {})
    payment_link = payload.get("payload", {}).get("payment_link", {}).get("entity", {})
    booking_id = payment_link.get("reference_id") or payload.get("booking_id")

    return {
        "booking_id": booking_id,
        "payment_provider": "razorpay",
        "payment_reference": payment_link.get("id"),
        "payment_status": payment_link.get("status") or payment.get("status"),
        "transaction_id": payment.get("id"),
        "payment_method": payment.get("method"),
        "paid_amount": int(payment.get("amount") or 0) // 100,
        "paid_at": int(time.time()),
        "paid": payment_link.get("status") == "paid" or payment.get("status") == "captured",
    }