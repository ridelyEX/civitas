import re

from django.conf import settings
from django.urls import reverse
from django.contrib import messages
from django.shortcuts import redirect
from django.utils import timezone


class SessionExpiryMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.exempt_urls = [re.compile(url) for url in settings.EXEMPT_URLS]

    def __call__(self, request):
        path = request.path_info.lstrip('/')

        public_urls = [
            reverse('login'),
            '/static/',
            '/media/',
        ]

        if any(pattern.match(path) for pattern in self.exempt_urls):
            return self.get_response(request)

        if path.startswith('ageo/api_sol/'):
            return self.get_response(request)

        if any(request.path.startswith(url) for url in public_urls):
            return self.get_response(request)

        if request.user.is_authenticated and not request.path.startswith('/cmin/'):
            last_activity = request.session.get('last_activity')
            if last_activity:
                elapsed = timezone.now().timestamp() - last_activity
                if elapsed > settings.SESSION_COOKIE_AGE:
                    request.session.flush()
                    return redirect(reverse('cmin:inicio'))

            request.session['last_activity'] = timezone.now().timestamp()

        if not request.user.is_authenticated:
            messages.warning(request,
                             "La sesión ha expirado. Por favor, inicie sesión nuevamente.")
            return redirect(f"{reverse('login')}?next={request.path}")

        response = self.get_response(request)
        return response
