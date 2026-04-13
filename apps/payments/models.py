from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator
import uuid
import hashlib


def generate_request_number():
    """Generate unique reference like WEG-2024-00001"""
    from django.utils import timezone
    year = timezone.now().year
    count = PaymentRequest.objects.filter(created_at__year=year).count() + 1
    return f"WEG-{year}-{count:05d}"


class PaymentCategory(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    requires_additional_docs = models.BooleanField(default=False)
    max_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'Payment Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class PaymentRequest(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        SUBMITTED = 'SUBMITTED', 'Submitted'
        UNDER_REVIEW1 = 'UNDER_REVIEW1', 'Under Review (Level 1)'
        APPROVED_L1 = 'APPROVED_L1', 'Approved by Supervisor'
        REJECTED_L1 = 'REJECTED_L1', 'Rejected by Supervisor'
        UNDER_REVIEW2 = 'UNDER_REVIEW2', 'Under Review (Level 2)'
        APPROVED_L2 = 'APPROVED_L2', 'Approved by Finance Controller'
        REJECTED_L2 = 'REJECTED_L2', 'Rejected by Finance Controller'
        PROCESSING = 'PROCESSING', 'Finance Processing'
        PAID = 'PAID', 'Payment Completed'
        RETIREMENT_PENDING = 'RETIREMENT_PENDING', 'Awaiting Retirement'
        RETIREMENT_SUBMITTED = 'RETIREMENT_SUBMITTED', 'Retirement Submitted'
        RETIREMENT_APPROVED = 'RETIREMENT_APPROVED', 'Retirement Approved'
        RETIREMENT_REJECTED = 'RETIREMENT_REJECTED', 'Retirement Correction Needed'
        CLOSED = 'CLOSED', 'Closed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    class Priority(models.TextChoices):
        LOW = 'LOW', 'Low'
        NORMAL = 'NORMAL', 'Normal'
        HIGH = 'HIGH', 'High'
        URGENT = 'URGENT', 'Urgent'

    # Identifiers
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request_number = models.CharField(max_length=20, unique=True, editable=False)

    # Relationships
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='payment_requests'
    )
    department = models.ForeignKey(
        'accounts.Department', on_delete=models.PROTECT, related_name='payment_requests'
    )
    category = models.ForeignKey(
        PaymentCategory, on_delete=models.PROTECT, null=True, blank=True
    )

    # Request details
    title = models.CharField(max_length=200)
    description = models.TextField()
    amount_requested = models.DecimalField(
        max_digits=15, decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    amount_approved = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    amount_actual = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='TZS')

    # Purpose & context
    purpose = models.TextField()
    beneficiary_name = models.CharField(max_length=200, blank=True)
    beneficiary_account = models.CharField(max_length=50, blank=True)
    beneficiary_bank = models.CharField(max_length=100, blank=True)
    payment_method = models.CharField(max_length=50, default='Bank Transfer')

    # Status
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.DRAFT)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.NORMAL)

    # Dates
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    needed_by_date = models.DateField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    retired_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    # Approval chain
    reviewer1 = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='review1_requests'
    )
    reviewer2 = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='review2_requests'
    )
    finance_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='finance_requests'
    )
    auditor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='audit_requests'
    )

    # Flags
    is_advance_payment = models.BooleanField(default=False)
    has_retirement = models.BooleanField(default=False)
    retirement_deadline = models.DateField(null=True, blank=True)

    # Checksum for integrity
    data_hash = models.CharField(max_length=64, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['requester']),
            models.Index(fields=['department']),
            models.Index(fields=['request_number']),
            models.Index(fields=['created_at']),
            models.Index(fields=['priority', 'status']),
        ]
        permissions = [
            ('can_view_all_requests', 'Can view all payment requests'),
            ('can_export_reports', 'Can export reports'),
        ]

    def __str__(self):
        return f"{self.request_number} — {self.title}"

    def save(self, *args, **kwargs):
        if not self.request_number:
            self.request_number = generate_request_number()
        self.data_hash = self._compute_hash()
        super().save(*args, **kwargs)

    def _compute_hash(self):
        data = f"{self.title}{self.amount_requested}{self.purpose}{self.requester_id}"
        return hashlib.sha256(data.encode()).hexdigest()

    @property
    def status_badge_class(self):
        mapping = {
            'DRAFT': 'secondary',
            'SUBMITTED': 'info',
            'UNDER_REVIEW1': 'warning',
            'APPROVED_L1': 'primary',
            'REJECTED_L1': 'danger',
            'UNDER_REVIEW2': 'warning',
            'APPROVED_L2': 'success',
            'REJECTED_L2': 'danger',
            'PROCESSING': 'info',
            'PAID': 'success',
            'RETIREMENT_PENDING': 'warning',
            'RETIREMENT_SUBMITTED': 'info',
            'RETIREMENT_APPROVED': 'success',
            'RETIREMENT_REJECTED': 'danger',
            'CLOSED': 'dark',
            'CANCELLED': 'secondary',
        }
        return mapping.get(self.status, 'secondary')

    @property
    def progress_percent(self):
        steps = {
            'DRAFT': 5, 'SUBMITTED': 15, 'UNDER_REVIEW1': 25,
            'APPROVED_L1': 35, 'UNDER_REVIEW2': 50, 'APPROVED_L2': 60,
            'PROCESSING': 70, 'PAID': 80, 'RETIREMENT_PENDING': 82,
            'RETIREMENT_SUBMITTED': 90, 'RETIREMENT_APPROVED': 95,
            'CLOSED': 100, 'CANCELLED': 100,
            'REJECTED_L1': 30, 'REJECTED_L2': 55, 'RETIREMENT_REJECTED': 88,
        }
        return steps.get(self.status, 0)

    @property
    def amount_variance(self):
        if self.amount_actual:
            base = self.amount_approved if self.amount_approved else self.amount_requested
            return self.amount_actual - base
        return None

    def get_current_action_user(self):
        """Returns who should act on this request currently"""
        if self.status == self.Status.SUBMITTED:
            return 'Reviewer 1 (Supervisor)'
        elif self.status == self.Status.APPROVED_L1:
            return 'Reviewer 2 (Finance Controller)'
        elif self.status == self.Status.APPROVED_L2:
            return 'Finance Officer'
        elif self.status == self.Status.PAID:
            return 'Requester (Retirement)'
        elif self.status == self.Status.RETIREMENT_SUBMITTED:
            return 'Auditor / Finance Verifier'
        return None


class RequestDocument(models.Model):
    class DocType(models.TextChoices):
        SUPPORTING = 'SUPPORTING', 'Supporting Document'
        QUOTE = 'QUOTE', 'Quotation'
        INVOICE = 'INVOICE', 'Invoice'
        RECEIPT = 'RECEIPT', 'Receipt'
        CONTRACT = 'CONTRACT', 'Contract'
        OTHER = 'OTHER', 'Other'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request = models.ForeignKey(PaymentRequest, on_delete=models.CASCADE, related_name='documents')
    doc_type = models.CharField(max_length=20, choices=DocType.choices, default=DocType.SUPPORTING)
    title = models.CharField(max_length=200)
    file = models.CharField(max_length=255, blank=True, null=True)
    file_size = models.PositiveIntegerField(default=0)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_retirement_doc = models.BooleanField(default=False)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.doc_type}: {self.title}"

    # Open Graph image (Facebook / WhatsApp preview)
    def get_og_image_url(self):
        if self.file:
            return f"https://ucarecdn.com/{self.file}/-/resize/1200x630/-/format/auto/"
        return ""

    # Optimized image for normal website usage
    def get_image_url(self):
        if self.file:
            return f"https://ucarecdn.com/{self.file}/-/format/jpg/-/quality/smart/"
        return ""


class Comment(models.Model):
    class CommentType(models.TextChoices):
        GENERAL = 'GENERAL', 'General'
        APPROVAL = 'APPROVAL', 'Approval Note'
        REJECTION = 'REJECTION', 'Rejection Reason'
        QUERY = 'QUERY', 'Query'
        SYSTEM = 'SYSTEM', 'System Message'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request = models.ForeignKey(PaymentRequest, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    comment_type = models.CharField(max_length=15, choices=CommentType.choices, default=CommentType.GENERAL)
    content = models.TextField()
    is_internal = models.BooleanField(default=False, help_text='Internal notes not visible to requester')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.author} on {self.request.request_number}"