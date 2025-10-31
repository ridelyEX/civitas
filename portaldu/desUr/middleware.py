from django.urls import reverse
from django.contrib import messages
from django.shortcuts import redirect

class SessionExpiryMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        public_urls = [
            reverse('login'),
            '/satic/',
            '/media/',
        ]

        if any(request.path.startswith(url) for url in public_urls):
            return self.get_response(request)

        if not request.user.is_authenticated:
            messages.warning(request,
                             "la sesión ha expirado. Por favor, inicie sesión nuevamente.")
            return redirect(f"{reverse('login')}?next={request.path}")

        response = self.get_response(request)
        return response


