import base64
from datetime import datetime


def mpesa_timestamp():
    return datetime.now().strftime("%Y%m%d%H%M%S")


def stk_password(shortcode, passkey, timestamp):
    data = f"{shortcode}{passkey}{timestamp}"
    return base64.b64encode(data.encode()).decode()
