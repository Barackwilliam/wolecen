from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid


class Department(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    head = models.ForeignKey('User', null=True, blank=True, on_delete=models.SET_NULL, related_name='headed_dept')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.code} — {self.name}"


class User(AbstractUser):
    class Role(models.TextChoices):
        REQUESTER = 'REQUESTER', _('Requester (Department)')
        REVIEWER1 = 'REVIEWER1', _('Reviewer 1 (Supervisor)')
        REVIEWER2 = 'REVIEWER2', _('Reviewer 2 (Finance Controller)')
        FINANCE = 'FINANCE', _('Finance Officer')
        AUDITOR = 'AUDITOR', _('Auditor / Verifier')
        ADMIN = 'ADMIN', _('System Administrator')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.REQUESTER)
    department = models.ForeignKey(Department, null=True, blank=True, on_delete=models.SET_NULL)
    employee_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    force_password_change = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['role']),
            models.Index(fields=['department']),
            models.Index(fields=['email']),
        ]

    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"

    @property
    def full_name(self):
        return self.get_full_name() or self.email

    @property
    def initials(self):
        parts = self.get_full_name().split()
        if len(parts) >= 2:
            return f"{parts[0][0]}{parts[-1][0]}".upper()
        return self.email[0].upper()

    # Role checks
    @property
    def is_requester(self):
        return self.role == self.Role.REQUESTER

    @property
    def is_reviewer1(self):
        return self.role == self.Role.REVIEWER1

    @property
    def is_reviewer2(self):
        return self.role == self.Role.REVIEWER2

    @property
    def is_finance(self):
        return self.role == self.Role.FINANCE

    @property
    def is_auditor(self):
        return self.role == self.Role.AUDITOR

    @property
    def is_system_admin(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    def can_approve_level1(self):
        return self.role in [self.Role.REVIEWER1, self.Role.ADMIN] or self.is_superuser

    def can_approve_level2(self):
        return self.role in [self.Role.REVIEWER2, self.Role.ADMIN] or self.is_superuser

    def can_process_payment(self):
        return self.role in [self.Role.FINANCE, self.Role.ADMIN] or self.is_superuser

    def can_verify_retirement(self):
        return self.role in [self.Role.AUDITOR, self.Role.FINANCE, self.Role.ADMIN] or self.is_superuser
