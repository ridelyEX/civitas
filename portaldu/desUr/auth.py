from charset_normalizer.md import is_accentuated
from django.contrib.auth.backends import BaseBackend
from django.shortcuts import redirect
from django.utils import timezone
from django_user_agents.templatetags.user_agents import is_pc

from .models import DesUrUsers
from functools import wraps
from django.shortcuts import redirect

class DesUrAuthBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return redirect('desur_login')
        try:
            user = DesUrUsers.objects.get(username=username)
            if user.is_active and user.check_password(password):
                user.last_login = timezone.now()
                user.save(update_fields=['last_login'])
                return user
        except DesUrUsers.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return DesUrUsers.objects.get(pk=user_id)
        except DesUrUsers.DoesNotExist:
            return None

class DesUrUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/desur/'):
            desur_user_id = request.session.get('desur_user_id')
            if desur_user_id:
                try:
                    request.user = DesUrUsers.objects.get(id=desur_user_id)
                except DesUrUsers.DoesNotExist:
                    request.user = None
            else:
                request.user = None
        return self.get_response(request)


def desur_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        desur_user_id = request.session.get('desur_user_id')
        if not desur_user_id:
            return redirect('desur_login')

        try:
            request.user = DesUrUsers.objects.get(id=desur_user_id, is_active=True)
        except DesUrUsers.DoesNotExist:
            request.session.pop('desur_user_id', None)
            return redirect('desur_login')
        return view_func(request, *args, **kwargs)
    return wrapper