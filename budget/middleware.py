from django.utils import timezone

class LogRequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Log request details
        print(f"[{timezone.now()}] {request.method} {request.path}")
        
        response = self.get_response(request)
        return response
