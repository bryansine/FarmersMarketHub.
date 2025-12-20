import json
import requests
from django.conf import settings
from .auth import get_mpesa_access_token
from .utils import mpesa_timestamp, stk_password, normalize_phone


def stk_push(amount, phone, account_reference, callback_url):
    access_token = get_mpesa_access_token()
    phone = normalize_phone(phone)

    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE,
        "Password": stk_password(),
        "Timestamp": mpesa_timestamp(),
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(amount),
        "PartyA": phone,
        "PartyB": settings.MPESA_SHORTCODE,
        "PhoneNumber": phone,
        "CallBackURL": callback_url,
        "AccountReference": account_reference,
        "TransactionDesc": f"Order {account_reference}",
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    url = (
        "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
        if settings.MPESA_ENV == "sandbox"
        else "https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    )

    response = requests.post(
        url,
        headers=headers,
        data=json.dumps(payload),
        timeout=30
    )

    return response.json()
