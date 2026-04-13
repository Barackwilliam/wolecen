from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import authenticate
from .models import User, Department


class LoginForm(forms.Form):
    """
    Custom login form using email + password.
    Does NOT extend AuthenticationForm — avoids username/email field conflict.
    Works with apps.accounts.backends.EmailBackend.
    """
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-input-auth',
            'placeholder': 'your.email@wolecen.com',
            'autofocus': True,
        }),
        label='Email Address',
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input-auth',
            'placeholder': '••••••••',
        }),
        label='Password',
    )

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self._user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        email = self.cleaned_data.get('email', '').strip()
        password = self.cleaned_data.get('password', '')

        if email and password:
            # EmailBackend receives email via 'username' kwarg
            self._user_cache = authenticate(
                self.request,
                username=email,
                password=password,
            )
            if self._user_cache is None:
                raise forms.ValidationError(
                    'Invalid email address or password. Please try again.'
                )
            if not self._user_cache.is_active:
                raise forms.ValidationError(
                    'This account has been deactivated. Contact your System Administrator.'
                )
        return self.cleaned_data

    def get_user(self):
        return self._user_cache


class UserCreateForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        min_length=8,
        required=False,
        help_text='Leave blank to auto-generate. User must change on first login.',
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'employee_id', 'role', 'department', 'phone', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if hasattr(field.widget, 'attrs') and 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'
        self.fields['role'].widget.attrs['class'] = 'form-select'
        self.fields['department'].widget.attrs['class'] = 'form-select'
        self.fields['department'].required = False

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)
        else:
            import secrets
            user.set_password(secrets.token_urlsafe(12))
        if not user.username:
            user.username = user.email
        if commit:
            user.save()
        return user


class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'avatar']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }


class ChangePasswordForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class UserAdminForm(forms.ModelForm):
    class Meta:
        model = User
        fields = '__all__'
        widgets = {
            'avatar': forms.TextInput(attrs={
                'role': 'uploadcare-uploader',
                'data-public-key': '431f160fc3fcf0ffb783',
                'data-images-only': 'true',
            })
        }

    class Media:
        css = {
            'all': ['https://ucarecdn.com/libs/widget/3.x/uploadcare.min.css']
        }
        js = [
            'https://ucarecdn.com/libs/widget/3.x/uploadcare.full.min.js',
        ]

