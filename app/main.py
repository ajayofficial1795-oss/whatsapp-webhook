import json

from fastapi import BackgroundTasks, FastAPI, Header, Request, Response
from fastapi.responses import JSONResponse, PlainTextResponse

from app.config import settings
from app.flow import handle_flow_data
from app.meta import extract_message, send_confirmation, send_payment_link, send_trek_flow, should_start_booking
from app.payments import parse_razorpay_webhook, verify_razorpay_signature
from app.storage import append_payment, find_booking, update_booking
from app.treks import active_treks

app = FastAPI(title="Direct Meta WhatsApp Trek Booking")


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.get("/webhook/whatsapp")
def verify_whatsapp_webhook(request: Request) -> Response:
    params = request.query_params
    if params.get("hub.mode") == "subscribe" and params.get("hub.verify_token") == settings.meta_verify_token:
        return PlainTextResponse(params.get("hub.challenge", ""))
    return JSONResponse({"ok": False, "error": "Invalid verify token"}, status_code=403)


@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks) -> dict:
    payload = await request.json()
    message = extract_message(payload)
    if should_start_booking(message):
        background_tasks.add_task(send_trek_flow, message["from"])
    return {"ok": True}


@app.get("/api/treks")
def treks() -> dict:
    return {"ok": True, "treks": active_treks()}


@app.post("/api/whatsapp-flow-data")
async def whatsapp_flow_data(request: Request) -> dict:
    return await handle_flow_data(await request.json())


@app.post("/api/send-trek-booking-flow")
async def send_trek_booking_flow(request: Request) -> dict:
    payload = await request.json()
    return {"ok": True, "result": await send_trek_flow(payload["to"])}


@app.post("/api/payment-webhook")
async def payment_webhook(request: Request, x_razorpay_signature: str | None = Header(default=None)) -> Response:
    raw_body = await request.body()

    if settings.payment_provider.lower() == "razorpay" and not verify_razorpay_signature(raw_body, x_razorpay_signature):
        return JSONResponse({"ok": False, "error": "Invalid Razorpay signature"}, status_code=400)

    payload = json.loads(raw_body.decode() or "{}")
    payment = parse_razorpay_webhook(payload)
    append_payment({**payment, "raw_webhook": payload})

    booking = find_booking(payment.get("booking_id")) if payment.get("booking_id") else None
    if booking and payment["paid"]:
        updated = update_booking(
            booking["booking_id"],
            {
                "booking_status": "confirmed",
                "payment_status": "paid",
                "transaction_id": payment.get("transaction_id"),
                "payment_method": payment.get("payment_method"),
                "paid_amount": payment.get("paid_amount"),
                "paid_at": payment.get("paid_at"),
            },
        )
        if updated and updated.get("customer_phone"):
            try:
                await send_confirmation(updated["customer_phone"], updated)
            except Exception as error:
                print(f"Failed to send Meta confirmation: {error}")

    return JSONResponse({"ok": True, **payment})


@app.post("/api/send-payment-link")
async def send_booking_payment_link(request: Request) -> dict:
    payload = await request.json()
    booking = find_booking(payload["booking_id"])
    if not booking:
        return {"ok": False, "error": "Booking not found"}
    return {"ok": True, "result": await send_payment_link(booking["customer_phone"], booking)}
