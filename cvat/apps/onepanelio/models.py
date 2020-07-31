# Copyright (C) 2020 Onepanel Inc.
#
# SPDX-License-Identifier: MIT

from django.contrib.auth.models import User


class AuthToken:
    @staticmethod
    def get_auth_token(request):
        return request.COOKIES['auth-token']


class AdminUser:
    @staticmethod
    def create_admin_user(request):
        auth_token = AuthToken.get_auth_token(request)
        username = "admin"
        if not User.objects.filter(username=username).exists():
            u = User(username=username)
            u.set_password(auth_token)
            u.is_superuser = True
            u.is_staff = True
            u.save()
