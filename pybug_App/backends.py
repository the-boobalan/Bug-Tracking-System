from .models import RegisterModel


class RegisterModelBackend:
    """Authenticate the project's existing account model through Django auth."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None

        user = RegisterModel.objects.filter(username=username).first()
        if user and user.check_password(password):
            return user
        return None

    def get_user(self, user_id):
        return RegisterModel.objects.filter(id=user_id).first()
