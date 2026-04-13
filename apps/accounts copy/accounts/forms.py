from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth import authenticate
from .models import User, Department


class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-input-auth',
            'placeholder': 'your.email@wolecen.com',
            'autofocus': True,
        }),
        label='Email Address',
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-input-auth', 'placeholder': '••••••••'}),
        label='Password',
    )

    def clean(self):
        email = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        if email and password:
            self.user_cache = authenticate(self.request, username=email, password=password)
            if self.user_cache is None:
                raise forms.ValidationError('Invalid email or password.')
            if not self.user_cache.is_active:
                raise forms.ValidationError('This account has been deactivated. Contact your administrator.')
        return self.cleaned_data


class UserCreateForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        min_length=8,
        required=False,
        help_text='Leave blank to auto-generate. User will be required to change on first login.',
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'employee_id', 'role', 'department', 'phone', 'is_active']
        widgets = {f: forms.TextInput(attrs={'class': 'form-control'}) if isinstance(User._meta.get_field(f), forms.CharField.__class__) else forms.Select(attrs={'class': 'form-select'}) for f in ['role', 'department']}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if hasattr(field.widget, 'attrs'):
                if not field.widget.attrs.get('class'):
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
