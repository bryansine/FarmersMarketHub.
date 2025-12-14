import base64, requests, datetime
from django.conf import settings


def get_oauth_token():
    url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
    resp = requests.get(url, auth=(settings.MPESA_CONSUMER_KEY, settings.MPESA_CONSUMER_SECRET), verify=True)
    resp.raise_for_status()
    return resp.json()['access_token']

def stk_push(amount, phone, account_reference, callback_url, description="Payment"):
    """
    Initiate STK push. Returns parsed JSON or error dict.
    Requires these settings in settings.py:
    MPESA_CONSUMER_KEY, MPESA_CONSUMER_SECRET, MPESA_SHORTCODE (BusinessShortCode),
    MPESA_PASSKEY, MPESA_ENVIRONMENT ('sandbox' or 'production')
    """
    token = get_oauth_token()
    endpoint = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'

    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    password_str = f"{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}"
    password = base64.b64encode(password_str.encode()).decode()

    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": str(amount),
        "PartyA": phone,
        "PartyB": settings.MPESA_SHORTCODE,
        "PhoneNumber": phone,
        "CallBackURL": callback_url,
        "AccountReference": account_reference,
        "TransactionDesc": description
    }

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    resp = requests.post(endpoint, json=payload, headers=headers)
    resp.raise_for_status()
    return resp.json()
