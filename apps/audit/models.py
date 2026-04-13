from django.db import models
from django.conf import settings
import uuid
import json


class AuditLog(models.Model):
    class EventType(models.TextChoices):
        CREATE = 'CREATE', 'Record Created'
        UPDATE = 'UPDATE', 'Record Updated'
        DELETE = 'DELETE', 'Record Deleted'
        LOGIN = 'LOGIN', 'User Login'
        LOGOUT = 'LOGOUT', 'User Logout'
        LOGIN_FAILED = 'LOGIN_FAILED', 'Failed Login Attempt'
        APPROVE = 'APPROVE', 'Approval Action'
        REJECT = 'REJECT', 'Rejection Action'
        EXPORT = 'EXPORT', 'Data Export'
        VIEW = 'VIEW', 'Record Viewed'
        PAYMENT = 'PAYMENT', 'Payment Action'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    event_type = models.CharField(max_length=20, choices=EventType.choices)
    model_name = models.CharField(max_length=50, blank=True)
    object_id = models.CharField(max_length=100, blank=True)
    object_repr = models.CharField(max_length=200, blank=True)
    changes = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    extra_data = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['event_type', 'timestamp']),
            models.Index(fields=['model_name', 'object_id']),
        ]

    def __str__(self):
        return f"{self.event_type} by {self.user} at {self.timestamp}"

    @classmethod
    def log(cls, user, event_type, model_name='', object_id='', object_repr='',
            changes=None, ip_address=None, user_agent='', extra_data=None):
        return cls.objects.create(
            user=user,
            event_type=event_type,
            model_name=model_name,
            object_id=str(object_id),
            object_repr=object_repr,
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent,
            extra_data=extra_data,
        )
