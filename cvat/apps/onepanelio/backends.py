from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

from cvat.apps.onepanelio.middleware import OnepanelCoreTokenAuthentication
from cvat.apps.onepanelio.models import MirrorOnepanelUser, OnepanelAuth

UserModel = get_user_model()

class OnepanelIORestBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        token_auth = OnepanelCoreTokenAuthentication()
        user_and_auth = token_auth.authenticate(request)
        if user_and_auth is None:
            return None
        return user_and_auth[0]

class OnepanelIOBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        # Ensure user exists in cvat
        MirrorOnepanelUser.create_user(request)
        try:
            # To allow auto-login for admin, check if the form is empty
            if username is None:
                username = "admin"
            user = UserModel._default_manager.get_by_natural_key(username)
            if password is None:
                password = OnepanelAuth.get_auth_token(request)
        except UserModel.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a nonexistent user (#20760).
            UserModel().set_password(password)
        else:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
