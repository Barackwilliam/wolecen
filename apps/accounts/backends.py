from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()


class EmailBackend(ModelBackend):
    """
    Authenticate using email address instead of username.
    Replaces Django's default ModelBackend for the custom login form.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        # 'username' here receives the email value from the login form
        email = username or kwargs.get('email')
        if not email or not password:
            return None

        try:
            user = User.objects.get(email__iexact=email.strip())
        except User.DoesNotExist:
            # Run the default password hasher to prevent timing attacks
            User().set_password(password)
            return None
        except User.MultipleObjectsReturned:
            # Shouldn't happen since email is unique, but handle gracefully
            user = User.objects.filter(email__iexact=email.strip()).order_by('id').first()

        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
