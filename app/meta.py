import httpx

from app.config import settings


def normalize_phone(phone: str) -> str:
    return "".join(ch for ch in str(phone or "") if ch.isdigit())


def build_trek_flow_message(to: str) -> dict:
    return {
        "messaging_product": "whatsapp",
        "to": normalize_phone(to),
        "type": "interactive",
        "interactive": {
            "type": "flow",
            "header": {"type": "text", "text": "Book Your Trek"},
            "body": {"text": "Choose trek, date, and people count."},
            "footer": {"text": "Secure payment after selection"},
            "action": {
                "name": "flow",
                "parameters": {
                    "flow_message_version": "3",
                    "mode": "draft",
                    "flow_id": settings.meta_trek_flow_id,
                    "flow_cta": "Book Trek",
                    "flow_action": "navigate",
                    "flow_action_payload": {"screen": "TREK_SELECTION", "data": {}},
                },
            },
        },
    }


def build_text_message(to: str, text: str) -> dict:
    return {
        "messaging_product": "whatsapp",
        "to": normalize_phone(to),
        "type": "text",
        "text": {"body": text},
    }


def build_confirmation_template(to: str, booking: dict) -> dict:
    return {
        "messaging_product": "whatsapp",
        "to": normalize_phone(to),
        "type": "template",
        "template": {
            "name": settings.meta_confirmation_template,
            "language": {"code": settings.meta_template_language},
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": booking.get("booking_id", "")},
                        {"type": "text", "text": booking.get("trek_name", "")},
                        {"type": "text", "text": booking.get("trek_date", "")},
                        {"type": "text", "text": str(booking.get("trek_people", ""))},
                        {"type": "text", "text": booking.get("total_price_display", "")},
                        {"type": "text", "text": booking.get("transaction_id", "")},
                    ],
                }
            ],
        },
    }


async def send_meta_message(message: dict) -> dict:
    if not settings.meta_access_token or not settings.meta_phone_number_id:
        raise ValueError("Missing Meta access token or phone number id")

    url = f"https://graph.facebook.com/{settings.meta_api_version}/{settings.meta_phone_number_id}/messages"
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            url,
            headers={"Authorization": f"Bearer {settings.meta_access_token}", "Content-Type": "application/json"},
            json=message,
        )

    body = response.json()
    if response.status_code >= 400:
        raise ValueError(body.get("error", {}).get("message", "Meta WhatsApp message failed"))
    return body


async def send_trek_flow(to: str) -> dict:
    return await send_meta_message(build_trek_flow_message(to))


async def send_payment_link(to: str, booking: dict) -> dict:
    text = (
        f"Your trek booking payment link is ready.\n\n"
        f"Booking ID: {booking['booking_id']}\n"
        f"Trek: {booking['trek_name']}\n"
        f"Date: {booking['trek_date']}\n"
        f"People: {booking['trek_people']}\n"
        f"Amount: {booking['total_price_display']}\n\n"
        f"Pay here: {booking['payment_link']}"
    )
    return await send_meta_message(build_text_message(to, text))


async def send_confirmation(to: str, booking: dict) -> dict:
    return await send_meta_message(build_confirmation_template(to, booking))


def extract_message(payload: dict) -> dict | None:
    value = payload.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {})
    messages = value.get("messages", [])
    if not messages:
        return None
    message = messages[0]
    return {
        "from": message.get("from"),
        "type": message.get("type"),
        "text": message.get("text", {}).get("body", ""),
        "raw": message,
    }


def should_start_booking(message: dict | None) -> bool:
    text = str((message or {}).get("text", "")).strip().lower()
    return text in {"trek", "book trek", "trek booking"} or "book trek" in text
