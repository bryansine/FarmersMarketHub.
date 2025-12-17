import requests
from base64 import b64encode
from django.conf import settings


def get_access_token():
    if settings.MPESA_ENV == "sandbox":
        url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    else:
        url = "https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"

    credentials = f"{settings.MPESA_CONSUMER_KEY}:{settings.MPESA_CONSUMER_SECRET}"
    encoded_credentials = b64encode(credentials.encode()).decode()

    headers = {
        "Authorization": f"Basic {encoded_credentials}"
    }

    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()

    return response.json()["access_token"]
