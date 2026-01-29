from django.shortcuts import render

# Create your views here.
# import json
# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt
# from orders.models import Order # We import the Order model to update it

# @csrf_exempt
# def mpesa_callback(request):
#     """
#     This view receives the JSON response from Safaricom
#     """
#     if request.method != "POST":
#         return JsonResponse({"error": "Method not allowed"}, status=405)

#     try:
#         # 1. Parse the incoming JSON
#         data = json.loads(request.body)
#         stk_callback = data.get('Body', {}).get('stkCallback', {})
        
#         # 2. Extract key information
#         merchant_request_id = stk_callback.get('MerchantRequestID')
#         checkout_request_id = stk_callback.get('CheckoutRequestID')
#         result_code = stk_callback.get('ResultCode')
#         result_desc = stk_callback.get('ResultDesc')

#         # 3. Find the matching Order
#         # We search by the CheckoutRequestID we saved during the initial push
#         try:
#             order = Order.objects.get(mpesa_checkout_request_id=checkout_request_id)
#         except Order.DoesNotExist:
#             print(f"Order not found for CheckoutID: {checkout_request_id}")
#             # Even if order is not found, return success to Safaricom so they stop retrying
#             return JsonResponse({"ResultCode": 0, "ResultDesc": "Accepted"})

#         # 4. Update the order based on the result
#         order.mpesa_response = json.dumps(data) # Save the full log just in case
        
#         if result_code == 0:
#             order.status = 'paid'
#             print(f"Order {order.id} marked as PAID.")
#         else:
#             order.status = 'failed'
#             print(f"Order {order.id} payment FAILED: {result_desc}")
            
#         order.save()

#     except Exception as e:
#         print(f"Error processing callback: {str(e)}")
        
#     # Always return a success response to Safaricom
#     return JsonResponse({"ResultCode": 0, "ResultDesc": "Accepted"})


from .utils import MpesaClient
from django.http import JsonResponse

def mpesa_token_view(request):
    client = MpesaClient()
    token = client.get_access_token()
    return JsonResponse({"access_token": token})