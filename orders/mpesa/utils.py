import base64
from datetime import datetime
from django.conf import settings


def mpesa_timestamp():
    return datetime.now().strftime("%Y%m%d%H%M%S")


def stk_password():
    data = (
        f"{settings.MPESA_SHORTCODE}"
        f"{settings.MPESA_PASSKEY}"
        f"{mpesa_timestamp()}"
    )
    return base64.b64encode(data.encode()).decode()


def normalize_phone(phone):
    phone = phone.strip()

    if phone.startswith("0"):
        phone = "254" + phone[1:]

    if phone.startswith("+"):
        phone = phone[1:]

    if not phone.startswith("254"):
        raise ValueError("Invalid Safaricom phone number")

    return phone
