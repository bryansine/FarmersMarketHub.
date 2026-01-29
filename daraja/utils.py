import requests
import json
import base64
from datetime import datetime
from django.conf import settings

def format_phone_number(phone):
    """
    Ensure phone number is in format 2547XXXXXXXX
    """
    if phone.startswith("+"):
        phone = phone[1:]
    if phone.startswith("0"):
        phone = "254" + phone[1:]
    return phone

class MpesaClient:
    def __init__(self):
        self.consumer_key = settings.MPESA_CONSUMER_KEY
        self.consumer_secret = settings.MPESA_CONSUMER_SECRET
        self.api_url = "https://sandbox.safaricom.co.ke" if settings.MPESA_ENV == 'sandbox' else "https://api.safaricom.co.ke"
       

    def get_access_token(self):
        url = f"{self.api_url}/oauth/v1/generate?grant_type=client_credentials"
        auth = base64.b64encode(f"{self.consumer_key}:{self.consumer_secret}".encode()).decode()
        headers = {"Authorization": f"Basic {auth}"}
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()['access_token']
        except Exception as e:
            print(f"Error generating token: {str(e)}")
            return None

    def stk_push(self, phone_number, amount, account_reference, callback_url):
        token = self.get_access_token()
        if not token:
            return {"error": "Could not generate access token"}

        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        passkey = settings.MPESA_PASSKEY
        shortcode = settings.MPESA_SHORTCODE
        
        # Generate password
        password_str = f"{shortcode}{passkey}{timestamp}"
        password = base64.b64encode(password_str.encode()).decode()

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        payload = {
            "BusinessShortCode": shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(amount), # M-Pesa only accepts integers
            "PartyA": format_phone_number(phone_number),
            "PartyB": shortcode,
            "PhoneNumber": format_phone_number(phone_number),
            "CallBackURL": callback_url,
            "AccountReference": account_reference,
            "TransactionDesc": f"Payment for {account_reference}"
        }

        url = f"{self.api_url}/mpesa/stkpush/v1/processrequest"
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            return response.json()
        except Exception as e:
            return {"error": str(e)}