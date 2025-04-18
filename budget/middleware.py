from django.utils.timezone import now

class LogRequestMiddleware:
    """
    Middleware to log the details of each request.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Code to execute for each request before the view is called
        print(f"[{now()}] {request.method} request to {request.path}")

        response = self.get_response(request)

        # Code to execute for each response after the view is called
        return response