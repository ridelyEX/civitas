from django.utils.cache import get_conditional_response


class ServiceWorkerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.path.endswith('sw.js') or request.path.endswith('service-worker.js'):
            response['Content-Type'] = 'application/javascript'
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Service-Worker-Allowed'] = '/'
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
            response['Access-Control-Allow-Headers'] = 'Content-Type'

            # Headers para manifest.json
        if request.path.endswith('manifest.json'):
            response['Content-Type'] = 'application/manifest+json'
            response['Access-Control-Allow-Origin'] = '*'

            # Headers generales para PWA
        if request.path.startswith('/ageo/'):
            response['Cache-Control'] = 'no-cache'
            response['Access-Control-Allow-Origin'] = '*'

        return response

