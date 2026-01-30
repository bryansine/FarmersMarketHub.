from .utils import MpesaClient
from django.shortcuts import render
from django.http import JsonResponse

def mpesa_token_view(request):
    client = MpesaClient()
    token = client.get_access_token()
    return JsonResponse({"access_token": token})