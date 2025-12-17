import base64
from datetime import datetime
from django.conf import settings


def mpesa_timestamp():
    return datetime.now().strftime("%Y%m%d%H%M%S")


def stk_password():
    data = f"{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{mpesa_timestamp()}"
    encoded = base64.b64encode(data.encode())
    return encoded.decode("utf-8")


def normalize_phone(phone: str) -> str:
    """
    Accepts:
    - 0712345678
    - 712345678
    - 254712345678

    Returns:
    - 254712345678
    """
    phone = phone.strip().replace(" ", "")

    if phone.startswith("+"):
        phone = phone[1:]

    if phone.startswith("0"):
        return "254" + phone[1:]

    if phone.startswith("7") and len(phone) == 9:
        return "254" + phone

    if phone.startswith("254"):
        return phone

    raise ValueError("Invalid phone number format")
