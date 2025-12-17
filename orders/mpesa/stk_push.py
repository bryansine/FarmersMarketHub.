import requests
from django.conf import settings
from .auth import get_access_token
from .utils import mpesa_timestamp, stk_password


def stk_push(amount, phone, account_reference, callback_url):
    access_token = get_access_token()
    timestamp = mpesa_timestamp()

    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE,
        "Password": stk_password(
            settings.MPESA_SHORTCODE,
            settings.MPESA_PASSKEY,
            timestamp
        ),
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(amount),
        "PartyA": phone,
        "PartyB": settings.MPESA_SHORTCODE,
        "PhoneNumber": phone,
        "CallBackURL": callback_url,
        "AccountReference": account_reference,
        "TransactionDesc": "FarmersHub Order Payment"
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    if settings.MPESA_ENV == "sandbox":
        url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    else:
        url = "https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest"

    response = requests.post(url, json=payload, headers=headers, timeout=15)
    return response.json()
