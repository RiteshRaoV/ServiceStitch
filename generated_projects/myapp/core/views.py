from django.shortcuts import render

# Create your views here.

@csrf_exempt
def projects(request):
    """Auto-generated mock for path 'projects' supports: GET, POST, PUT"""
    m = request.method
    if m == "GET":
        return JsonResponse({'message': 'projects GET mock', 'data': []})
    if m == "POST":
        return JsonResponse({'message': 'projects POST mock'}, status=201)
    if m == "PUT":
        return JsonResponse({'message': 'projects PUT mock'})
    return JsonResponse({'error': 'Method not allowed'}, status=405)
