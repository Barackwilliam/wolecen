from django.db import models
from django.conf import settings
import uuid


class ApprovalAction(models.Model):
    class Action(models.TextChoices):
        SUBMITTED = 'SUBMITTED', 'Submitted for Review'
        APPROVED_L1 = 'APPROVED_L1', 'Approved (Level 1)'
        REJECTED_L1 = 'REJECTED_L1', 'Rejected (Level 1)'
        APPROVED_L2 = 'APPROVED_L2', 'Approved (Level 2)'
        REJECTED_L2 = 'REJECTED_L2', 'Rejected (Level 2)'
        PAYMENT_PROCESSED = 'PAYMENT_PROCESSED', 'Payment Processed'
        PAYMENT_COMPLETED = 'PAYMENT_COMPLETED', 'Payment Completed'
        RETIREMENT_SUBMITTED = 'RETIREMENT_SUBMITTED', 'Retirement Submitted'
        RETIREMENT_APPROVED = 'RETIREMENT_APPROVED', 'Retirement Approved'
        RETIREMENT_RETURNED = 'RETIREMENT_RETURNED', 'Returned for Correction'
        CLOSED = 'CLOSED', 'Request Closed'
        CANCELLED = 'CANCELLED', 'Request Cancelled'
        AMOUNT_ADJUSTED = 'AMOUNT_ADJUSTED', 'Amount Adjusted'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request = models.ForeignKey(
        'payments.PaymentRequest', on_delete=models.CASCADE, related_name='approval_actions'
    )
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    action = models.CharField(max_length=30, choices=Action.choices)
    previous_status = models.CharField(max_length=30, blank=True)
    new_status = models.CharField(max_length=30, blank=True)
    remarks = models.TextField(blank=True)
    amount_at_action = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['request', 'timestamp']),
            models.Index(fields=['actor', 'timestamp']),
            models.Index(fields=['action']),
        ]

    def __str__(self):
        return f"{self.action} by {self.actor} on {self.request.request_number}"


class ApprovalDelegate(models.Model):
    """Allow users to delegate their approval authority"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    delegator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='delegated_to')
    delegate = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='delegated_from')
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.delegator} → {self.delegate} ({self.start_date} to {self.end_date})"
