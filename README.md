# Direct Meta WhatsApp Trek Booking

Python FastAPI backend for a direct Meta WhatsApp Cloud API booking flow without WATI.

## Flow

```text
Customer sends "book trek"
  -> Meta calls POST /webhook/whatsapp
  -> API sends Meta interactive WhatsApp Flow message
  -> WhatsApp Flow calls POST /api/whatsapp-flow-data
  -> API creates booking + payment link
  -> Razorpay calls POST /api/payment-webhook
  -> API stores transaction and sends confirmation template
```

## Run Locally

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

## Docker

```sh
docker build -t whatsapp-trek-booking:local .
docker run --rm -p 8000:8000 --env-file .env whatsapp-trek-booking:local
```

## User Experience Preview

Open `preview.html` in a browser to see the customer-side WhatsApp journey before Meta credentials are configured.

It simulates:

```text
book trek keyword
WhatsApp Flow invite button
trek/date/people selection
payment link message
payment confirmation message
```

## Meta Webhook

Configure callback URL:

```text
https://<your-domain>/webhook/whatsapp
```

Verify token must match:

```text
META_VERIFY_TOKEN
```

Subscribe to WhatsApp message events.

## Send Flow Manually

```sh
curl -X POST http://localhost:8000/api/send-trek-booking-flow \
  -H 'Content-Type: application/json' \
  -d '{"to":"918884945557"}'
```

Requires:

```text
META_ACCESS_TOKEN
META_PHONE_NUMBER_ID
META_TREK_FLOW_ID
```

## WhatsApp Flow Data Endpoint

Set the Flow data exchange endpoint to:

```text
https://<your-domain>/api/whatsapp-flow-data
```

Use the existing Flow JSON from the earlier project or recreate the same screens:

```text
TREK_SELECTION -> DATE_SELECTION -> BOOKING_SUMMARY
```

## Razorpay

Set:

```text
PAYMENT_PROVIDER=razorpay
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=
RAZORPAY_WEBHOOK_SECRET=
```

In Razorpay Dashboard, add webhook:

```text
https://<your-domain>/api/payment-webhook
```

Recommended events:

```text
payment_link.paid
payment.captured
payment.failed
```

The webhook verifies `X-Razorpay-Signature` before updating local JSON storage.