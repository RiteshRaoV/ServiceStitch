from django.shortcuts import render

# Create your views here.

@csrf_exempt
def login(request):
    """Auto-generated mock for path 'login' supports: POST"""
    m = request.method
    if m == "POST":
        return JsonResponse({'message': 'login POST mock'}, status=201)
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def signup(request):
    """Auto-generated mock for path 'signup' supports: POST"""
    m = request.method
    if m == "POST":
        return JsonResponse({'message': 'signup POST mock'}, status=201)
    return JsonResponse({'error': 'Method not allowed'}, status=405)
