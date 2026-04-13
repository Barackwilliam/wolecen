from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.core.paginator import Paginator

from .models import User, Department
from .forms import LoginForm, UserCreateForm, UserEditForm, ChangePasswordForm
from apps.audit.models import AuditLog


def get_client_ip(request):
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()

            # Login the user
            login(request, user)

            # Update last_login_ip only — do NOT include last_login in update_fields
            # (Django updates last_login automatically via signal)
            try:
                User.objects.filter(pk=user.pk).update(
                    last_login_ip=get_client_ip(request)
                )
            except Exception:
                pass  # Non-critical, don't break login

            # Audit log — wrapped so it never breaks login flow
            try:
                AuditLog.log(
                    user=user,
                    event_type=AuditLog.EventType.LOGIN,
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                )
            except Exception:
                pass

            if user.force_password_change:
                messages.warning(request, 'Please change your password before continuing.')
                return redirect('accounts:change_password')

            next_url = request.POST.get('next') or request.GET.get('next', '')
            if next_url and next_url.startswith('/'):
                return redirect(next_url)
            return redirect('dashboard:home')

        else:
            # Log failed attempt — also wrapped
            try:
                AuditLog.log(
                    user=None,
                    event_type=AuditLog.EventType.LOGIN_FAILED,
                    ip_address=get_client_ip(request),
                    extra_data={'email': request.POST.get('email', '')},
                )
            except Exception:
                pass

    else:
        form = LoginForm(request)

    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    try:
        AuditLog.log(
            user=request.user,
            event_type=AuditLog.EventType.LOGOUT,
            ip_address=get_client_ip(request),
        )
    except Exception:
        pass
    logout(request)
    messages.success(request, 'You have been signed out successfully.')
    return redirect('accounts:login')


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = UserEditForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('accounts:profile')
    else:
        form = UserEditForm(instance=request.user)
    return render(request, 'accounts/profile.html', {'form': form})


@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = ChangePasswordForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            try:
                user.force_password_change = False
                user.save(update_fields=['force_password_change'])
            except Exception:
                pass
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully.')
            return redirect('dashboard:home')
    else:
        form = ChangePasswordForm(request.user)
    return render(request, 'accounts/change_password.html', {'form': form})


@login_required
def user_list_view(request):
    if not request.user.is_system_admin:
        messages.error(request, 'Access denied.')
        return redirect('dashboard:home')

    qs = User.objects.select_related('department').order_by('first_name')
    q = request.GET.get('q', '')
    role = request.GET.get('role', '')
    if q:
        qs = qs.filter(
            Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(email__icontains=q)
        )
    if role:
        qs = qs.filter(role=role)

    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'accounts/user_list.html', {
        'page_obj': page_obj,
        'role_choices': User.Role.choices,
        'q': q,
        'role': role,
    })


@login_required
def user_create_view(request):
    if not request.user.is_system_admin:
        messages.error(request, 'Access denied.')
        return redirect('dashboard:home')

    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.force_password_change = True
            user.save()
            messages.success(request, f'User {user.get_full_name()} created.')
            return redirect('accounts:users')
    else:
        form = UserCreateForm()

    return render(request, 'accounts/user_form.html', {'form': form, 'action': 'Create'})


@login_required
def user_edit_view(request, pk):
    if not request.user.is_system_admin:
        messages.error(request, 'Access denied.')
        return redirect('dashboard:home')

    edit_user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = UserCreateForm(request.POST, instance=edit_user)
        if form.is_valid():
            form.save()
            messages.success(request, f'User {edit_user.get_full_name()} updated.')
            return redirect('accounts:users')
    else:
        form = UserCreateForm(instance=edit_user)

    return render(request, 'accounts/user_form.html', {
        'form': form,
        'action': 'Edit',
        'edit_user': edit_user,
    })


@login_required
def user_toggle_active(request, pk):
    if not request.user.is_system_admin:
        messages.error(request, 'Access denied.')
        return redirect('dashboard:home')

    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        messages.error(request, 'You cannot deactivate your own account.')
        return redirect('accounts:users')

    user.is_active = not user.is_active
    user.save(update_fields=['is_active'])
    status = 'activated' if user.is_active else 'deactivated'
    messages.success(request, f'User {user.get_full_name()} has been {status}.')
    return redirect('accounts:users')
