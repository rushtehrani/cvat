# Copyright (C) 2020 Onepanel Inc.
#
# SPDX-License-Identifier: MIT


class AuthToken:
    @staticmethod
    def get_auth_token(request):
        return request.COOKIES['auth-token']
