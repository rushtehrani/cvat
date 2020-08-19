# Copyright (C) 2020 Onepanel Inc.
#
# SPDX-License-Identifier: MIT
from pprint import pprint

from django.contrib.auth.models import User
import onepanel.core.api
from onepanel.core.api.rest import ApiException

class AuthToken:
    @staticmethod
    def get_auth_token(request):
        return request.COOKIES['auth-token']

    @staticmethod
    def validate_token(token: str, username: str, onepanel_api_url: str) -> bool:
        if username != 'admin':
            return False
        # Defining the host is optional and defaults to http://localhost:8888
        # See configuration.py for a list of all supported configuration parameters.
        configuration = onepanel.core.api.Configuration(
            host=onepanel_api_url
        )

        # Enter a context with an instance of the API client
        with onepanel.core.api.ApiClient(configuration) as api_client:
            # Create an instance of the API class
            api_instance = onepanel.core.api.AuthServiceApi(api_client)
            body = onepanel.core.api.TokenWrapper()  # TokenWrapper |
            body.token = "Bearer " + token
            try:
                api_response = api_instance.is_valid_token(body)
                return True
            except ApiException as e:
                print("Exception when calling AuthServiceApi->is_valid_token: %s\n" % e)
                return False

class AdminUser:
    @staticmethod
    def create_admin_user(request, username="admin", auth_token=None):
        if auth_token is None:
            auth_token = AuthToken.get_auth_token(request)
        if not User.objects.filter(username=username).exists():
            u = User(username=username)
            u.set_password(auth_token)
            u.is_superuser = True
            u.is_staff = True
            u.save()
