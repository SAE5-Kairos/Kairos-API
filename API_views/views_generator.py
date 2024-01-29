import json
from django.shortcuts import render
from django.http import JsonResponse
from Kairos_API.database import Database
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def generate_edt(request):
    if request.method == "POST":
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        
        return JsonResponse(body, safe=False)
    else: return JsonResponse({"error": "Request POST awaited"})