from app.payments import create_payment_link
from app.storage import create_booking, update_booking
from app.treks import date_options, find_date, find_trek, format_inr, trek_options


def people_options(limit: int = 10) -> list[dict]:
    return [
        {"id": str(count), "title": str(count), "description": "1 person" if count == 1 else f"{count} people"}
        for count in range(1, limit + 1)
    ]


def selected_id(value):
    if isinstance(value, dict):
        return value.get("id") or value.get("title")
    return value


async def handle_flow_data(payload: dict) -> dict:
    action = payload.get("action", "init")
    normalized_action = action.lower()
    version = payload.get("version", "3.0")
    screen = payload.get("screen", "TREK_SELECTION")
    data = payload.get("data") or payload

    if normalized_action == "ping":
        return {"data": {"status": "active"}}

    if normalized_action == "init":
        return {"version": version, "screen": "TREK_SELECTION", "data": {"treks": trek_options()}}

    if screen == "TREK_SELECTION":
        trek_id = selected_id(data.get("trek_id"))
        trek = find_trek(trek_id)
        return {
            "version": version,
            "screen": "DATE_SELECTION",
            "data": {
                "trek_id": trek_id,
                "trek_name": trek.get("name") if trek else "",
                "dates": date_options(trek_id),
                "people_options": people_options(),
            },
        }

    if screen == "DATE_SELECTION":
        trek_id = selected_id(data.get("trek_id"))
        trek_date_id = selected_id(data.get("trek_date_id"))
        trek_people = selected_id(data.get("trek_people"))
        trek = find_trek(trek_id)
        if not trek:
            return {"version": version, "screen": "BOOKING_SUMMARY", "data": {"ok": False, "error": "Unknown trek"}}

        trek_date = find_date(trek, trek_date_id)
        if not trek_date:
            return {"version": version, "screen": "BOOKING_SUMMARY", "data": {"ok": False, "error": "Unknown trek date"}}

        trek_people = int(trek_people or 1)
        price = int(trek_date.get("price_per_person") or trek["price_per_person"])
        total = price * trek_people
        booking = create_booking(
            {
                "customer_phone": data.get("customer_phone"),
                "customer_name": data.get("customer_name"),
                "trek_id": trek["id"],
                "trek_name": trek["name"],
                "trek_date_id": trek_date["id"],
                "trek_date": trek_date.get("label", trek_date["date"]),
                "trek_people": trek_people,
                "price_per_person": price,
                "total_price": total,
                "total_price_display": format_inr(total),
            }
        )
        payment = await create_payment_link(booking)
        booking.update(payment)
        update_booking(booking["booking_id"], payment)

        return {
            "version": version,
            "screen": "BOOKING_SUMMARY",
            "data": {
                "ok": True,
                "error": "",
                "booking_id": booking["booking_id"],
                "trek_name": booking["trek_name"],
                "trek_date": booking["trek_date"],
                "trek_people": str(booking["trek_people"]),
                "total_price_display": booking["total_price_display"],
                "payment_link": booking["payment_link"],
                "payment_status": booking["payment_status"],
            },
        }

    return {"version": version, "screen": "TREK_SELECTION", "data": {"treks": trek_options()}}
