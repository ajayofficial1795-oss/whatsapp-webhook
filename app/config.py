import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_base_url: str = os.getenv("APP_BASE_URL", "http://localhost:8000")
    data_dir: str = os.getenv("DATA_DIR", "data")

    meta_api_version: str = os.getenv("META_API_VERSION", "v20.0")
    meta_access_token: str = os.getenv("META_ACCESS_TOKEN", "")
    meta_phone_number_id: str = os.getenv("META_PHONE_NUMBER_ID", "")
    meta_waba_id: str = os.getenv("META_WABA_ID", "")
    meta_verify_token: str = os.getenv("META_VERIFY_TOKEN", "change-me")
    meta_trek_flow_id: str = os.getenv("META_TREK_FLOW_ID", "")
    meta_confirmation_template: str = os.getenv("META_CONFIRMATION_TEMPLATE", "trek_booking_confirmed")
    meta_template_language: str = os.getenv("META_TEMPLATE_LANGUAGE", "en")

    payment_provider: str = os.getenv("PAYMENT_PROVIDER", "manual")
    manual_payment_url: str = os.getenv("MANUAL_PAYMENT_URL", "https://example.com/pay")
    razorpay_key_id: str = os.getenv("RAZORPAY_KEY_ID", "")
    razorpay_key_secret: str = os.getenv("RAZORPAY_KEY_SECRET", "")
    razorpay_webhook_secret: str = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")


settings = Settings()
