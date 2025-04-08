import time
import logging
from django.core.cache import cache
from django.conf import settings
import json
from django.utils import timezone

logger = logging.getLogger(__name__)

class LogRequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Start timer
        start_time = time.time()

        # Process request
        response = self.get_response(request)

        # Calculate request duration
        duration = time.time() - start_time

        # Log request details
        logger.info(
            f"Request: {request.method} {request.path} "
            f"Status: {response.status_code} "
            f"Duration: {duration:.2f}s "
            f"User: {request.user}"
        )

        # Track API usage in Redis
        if request.path.startswith('/api/'):
            self._track_api_usage(request)

        return response

    def _track_api_usage(self, request):
        """Track API usage in Redis for rate limiting and analytics"""
        if request.user.is_authenticated:
            key = f"api_usage:{request.user.id}"
            cache.incr(key)
            cache.expire(key, 86400)  # Expire after 24 hours

class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Start time of request
        start_time = timezone.now()

        # Process request
        response = self.get_response(request)

        # Calculate request duration
        duration = timezone.now() - start_time

        # Get request data
        request_data = {
            'method': request.method,
            'path': request.path,
            'status_code': response.status_code,
            'duration': f"{duration.total_seconds():.2f}s",
            'user': str(request.user),
            'ip': self.get_client_ip(request),
        }

        # Log the request
        logger.info(
            f"Request: {json.dumps(request_data)}"
        )

        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
