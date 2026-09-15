import json
import time
from pathlib import Path
from uuid import uuid4

from app.config import settings


def _path(name: str) -> Path:
    path = Path(settings.data_dir) / name
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("[]")
    return path


def _read(name: str) -> list[dict]:
    return json.loads(_path(name).read_text())


def _write(name: str, rows: list[dict]) -> None:
    _path(name).write_text(json.dumps(rows, indent=2))


def create_booking(booking: dict) -> dict:
    rows = _read("bookings.json")
    booking = {
        "booking_id": booking.get("booking_id") or f"BK-{int(time.time())}-{uuid4().hex[:6]}",
        "booking_status": "payment_pending",
        "payment_status": "pending",
        "created_at": int(time.time()),
        **booking,
    }
    rows.append(booking)
    _write("bookings.json", rows)
    return booking


def find_booking(booking_id: str) -> dict | None:
    for booking in _read("bookings.json"):
        if booking.get("booking_id") == booking_id:
            return booking
    return None


def update_booking(booking_id: str, updates: dict) -> dict | None:
    rows = _read("bookings.json")
    updated = None
    for index, booking in enumerate(rows):
        if booking.get("booking_id") == booking_id:
            rows[index] = {**booking, **updates, "updated_at": int(time.time())}
            updated = rows[index]
            break
    _write("bookings.json", rows)
    return updated


def append_payment(payment: dict) -> dict:
    rows = _read("payments.json")
    payment = {"created_at": int(time.time()), **payment}
    rows.append(payment)
    _write("payments.json", rows)
    return payment