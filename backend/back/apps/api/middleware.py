from django.conf import settings
from django.http import JsonResponse


class UploadSizeLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        max_body_size = getattr(settings, 'MAX_PRINT_UPLOAD_BODY_SIZE', None)
        if max_body_size and self._is_print_upload(request):
            content_length = request.META.get('CONTENT_LENGTH')
            if content_length:
                try:
                    content_length = int(content_length)
                except ValueError:
                    return JsonResponse({'detail': 'Invalid Content-Length.'}, status=400)
                if content_length > max_body_size:
                    return JsonResponse({'detail': 'Upload request too large.'}, status=413)
        return self.get_response(request)

    def _is_print_upload(self, request):
        return (
            request.method in {'POST', 'PUT', 'PATCH'}
            and request.path.startswith('/api/v1/requests')
        )
