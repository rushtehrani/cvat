from allauth.account.views import login
from django.contrib import auth
from django.contrib.auth.middleware import MiddlewareMixin
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import redirect
from django.contrib.auth import get_user_model

from cvat.apps.onepanelio.models import AuthToken

UserModel = get_user_model()


class AutomaticUserLoginMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        if not AutomaticUserLoginMiddleware._is_user_authenticated(request):
            user = auth.authenticate(request)
            if user is None:
                # Load admin user, check if current cookie value matches
                # admin in the database
                username = "admin"
                user = UserModel._default_manager.get_by_natural_key(username)
                if user is None:
                    return HttpResponseForbidden()
                current_cookie_token = AuthToken.get_auth_token(request)
                if not user.check_password(current_cookie_token):
                    return HttpResponseForbidden()
            if user is None:
                return HttpResponseForbidden()

            request.user = user
            auth.login(request, user)

    @staticmethod
    def _is_user_authenticated(request):
        user = request.user
        return user and user.is_authenticated
