import json
from pathlib import Path

from app.config import settings


def _data_path() -> Path:
    return Path(settings.data_dir) / "treks.json"


def format_inr(amount: int) -> str:
    return "Rs. {:,}".format(amount)


def load_treks() -> list[dict]:
    return json.loads(_data_path().read_text()).get("treks", [])


def active_treks() -> list[dict]:
    return [trek for trek in load_treks() if trek.get("active", True)]


def find_trek(trek_id: str | None) -> dict | None:
    if not trek_id:
        return None

    normalized = str(trek_id).strip().lower()
    for trek in active_treks():
        if trek["id"].lower() == normalized or trek["name"].lower() == normalized:
            return trek
    return None


def find_date(trek: dict, date_id: str | None) -> dict | None:
    if not date_id:
        return None

    normalized = str(date_id).strip().lower()
    for trek_date in trek.get("dates", []):
        if not trek_date.get("active", True):
            continue
        if trek_date["id"].lower() == normalized or trek_date["date"].lower() == normalized:
            return trek_date
    return None


def trek_options() -> list[dict]:
    return [
        {
            "id": trek["id"],
            "title": trek["name"],
            "description": format_inr(trek["price_per_person"]),
        }
        for trek in active_treks()
    ]


def date_options(trek_id: str | None) -> list[dict]:
    trek = find_trek(trek_id)
    if not trek:
        return []

    return [
        {
            "id": trek_date["id"],
            "title": trek_date.get("label", trek_date["date"]),
            "description": f"{trek_date['available_seats']} seats available",
        }
        for trek_date in trek.get("dates", [])
        if trek_date.get("active", True)
    ]