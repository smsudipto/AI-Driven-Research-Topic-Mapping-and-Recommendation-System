from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend


class EmailOrUsernameModelBackend(BaseBackend):
    """Authenticate an account by either its username or email address."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or password is None:
            return None

        user_model = get_user_model()
        try:
            user = user_model.objects.get(username=username)
        except user_model.DoesNotExist:
            try:
                user = user_model.objects.get(email=username)
            except user_model.DoesNotExist:
                return None

        if user.check_password(password) and self._is_active(user):
            return user
        return None

    def get_user(self, user_id):
        user_model = get_user_model()
        try:
            user = user_model.objects.get(pk=user_id)
        except user_model.DoesNotExist:
            return None
        return user if self._is_active(user) else None

    @staticmethod
    def _is_active(user):
        return getattr(user, 'is_active', True)
