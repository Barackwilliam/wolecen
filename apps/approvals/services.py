"""
Wolecen EGL — Approval Workflow Service
Central business logic for all approval operations.
"""
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import PermissionDenied, ValidationError

from apps.payments.models import PaymentRequest, Comment
from apps.approvals.models import ApprovalAction
from apps.audit.models import AuditLog


class ApprovalService:
    """
    Handles all approval workflow transitions with full audit trail.
    All state changes go through this service — no direct model saves.
    """

    @staticmethod
    def _get_ip(request):
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded:
            return x_forwarded.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')

    @staticmethod
    def _record_action(payment_request, actor, action, prev_status, new_status, remarks='', request=None):
        ApprovalAction.objects.create(
            request=payment_request,
            actor=actor,
            action=action,
            previous_status=prev_status,
            new_status=new_status,
            remarks=remarks,
            amount_at_action=payment_request.amount_requested,
            ip_address=ApprovalService._get_ip(request) if request else None,
        )
        AuditLog.log(
            user=actor,
            event_type=AuditLog.EventType.APPROVE if 'APPROVED' in action else AuditLog.EventType.REJECT,
            model_name='PaymentRequest',
            object_id=payment_request.id,
            object_repr=str(payment_request),
            changes={'action': action, 'from': prev_status, 'to': new_status},
            ip_address=ApprovalService._get_ip(request) if request else None,
        )

    @classmethod
    @transaction.atomic
    def submit_request(cls, payment_request, user, remarks='', request=None):
        """Step 2: Requester submits the request"""
        if payment_request.requester != user and not user.is_system_admin:
            raise PermissionDenied("Only the requester can submit this request.")
        if payment_request.status not in [
            PaymentRequest.Status.DRAFT,
            PaymentRequest.Status.REJECTED_L1,
            PaymentRequest.Status.REJECTED_L2,
        ]:
            raise ValidationError("Request cannot be submitted in its current state.")

        prev = payment_request.status
        payment_request.status = PaymentRequest.Status.SUBMITTED
        payment_request.submitted_at = timezone.now()
        payment_request.save(update_fields=['status', 'submitted_at', 'updated_at'])

        cls._record_action(payment_request, user, ApprovalAction.Action.SUBMITTED, prev, payment_request.status, remarks, request)
        if remarks:
            Comment.objects.create(request=payment_request, author=user, comment_type=Comment.CommentType.GENERAL, content=remarks)

        return payment_request

    @classmethod
    @transaction.atomic
    def approve_level1(cls, payment_request, user, remarks='', amount_approved=None, request=None):
        """Step 3: Reviewer 1 approves"""
        if not user.can_approve_level1:
            raise PermissionDenied("You do not have Level 1 approval authority.")
        if payment_request.status != PaymentRequest.Status.SUBMITTED:
            raise ValidationError("Request is not awaiting Level 1 approval.")

        prev = payment_request.status
        payment_request.status = PaymentRequest.Status.APPROVED_L1
        payment_request.reviewer1 = user
        if amount_approved:
            payment_request.amount_approved = amount_approved
        payment_request.save(update_fields=['status', 'reviewer1', 'amount_approved', 'updated_at'])

        cls._record_action(payment_request, user, ApprovalAction.Action.APPROVED_L1, prev, payment_request.status, remarks, request)
        if remarks:
            Comment.objects.create(request=payment_request, author=user, comment_type=Comment.CommentType.APPROVAL, content=remarks)

        return payment_request

    @classmethod
    @transaction.atomic
    def reject_level1(cls, payment_request, user, remarks, request=None):
        """Step 3: Reviewer 1 rejects"""
        if not remarks.strip():
            raise ValidationError("Rejection reason is required.")
        if not user.can_approve_level1:
            raise PermissionDenied("You do not have Level 1 approval authority.")

        prev = payment_request.status
        payment_request.status = PaymentRequest.Status.REJECTED_L1
        payment_request.reviewer1 = user
        payment_request.save(update_fields=['status', 'reviewer1', 'updated_at'])

        cls._record_action(payment_request, user, ApprovalAction.Action.REJECTED_L1, prev, payment_request.status, remarks, request)
        Comment.objects.create(request=payment_request, author=user, comment_type=Comment.CommentType.REJECTION, content=remarks)

        return payment_request

    @classmethod
    @transaction.atomic
    def approve_level2(cls, payment_request, user, remarks='', amount_approved=None, request=None):
        """Step 4: Reviewer 2 approves"""
        if not user.can_approve_level2:
            raise PermissionDenied("You do not have Level 2 approval authority.")
        if payment_request.status != PaymentRequest.Status.APPROVED_L1:
            raise ValidationError("Request is not awaiting Level 2 approval.")

        prev = payment_request.status
        payment_request.status = PaymentRequest.Status.APPROVED_L2
        payment_request.reviewer2 = user
        if amount_approved:
            payment_request.amount_approved = amount_approved
        payment_request.save(update_fields=['status', 'reviewer2', 'amount_approved', 'updated_at'])

        cls._record_action(payment_request, user, ApprovalAction.Action.APPROVED_L2, prev, payment_request.status, remarks, request)
        if remarks:
            Comment.objects.create(request=payment_request, author=user, comment_type=Comment.CommentType.APPROVAL, content=remarks)

        return payment_request

    @classmethod
    @transaction.atomic
    def reject_level2(cls, payment_request, user, remarks, request=None):
        """Step 4: Reviewer 2 rejects"""
        if not remarks.strip():
            raise ValidationError("Rejection reason is required.")
        if not user.can_approve_level2:
            raise PermissionDenied("You do not have Level 2 approval authority.")

        prev = payment_request.status
        payment_request.status = PaymentRequest.Status.REJECTED_L2
        payment_request.reviewer2 = user
        payment_request.save(update_fields=['status', 'reviewer2', 'updated_at'])

        cls._record_action(payment_request, user, ApprovalAction.Action.REJECTED_L2, prev, payment_request.status, remarks, request)
        Comment.objects.create(request=payment_request, author=user, comment_type=Comment.CommentType.REJECTION, content=remarks)

        return payment_request

    @classmethod
    @transaction.atomic
    def process_payment(cls, payment_request, user, remarks='', request=None):
        """Step 5: Finance processes payment"""
        if not user.can_process_payment:
            raise PermissionDenied("You do not have payment processing authority.")
        if payment_request.status != PaymentRequest.Status.APPROVED_L2:
            raise ValidationError("Request is not approved for payment processing.")

        prev = payment_request.status
        payment_request.status = PaymentRequest.Status.PROCESSING
        payment_request.finance_officer = user
        payment_request.save(update_fields=['status', 'finance_officer', 'updated_at'])

        cls._record_action(payment_request, user, ApprovalAction.Action.PAYMENT_PROCESSED, prev, payment_request.status, remarks, request)
        return payment_request

    @classmethod
    @transaction.atomic
    def complete_payment(cls, payment_request, user, remarks='', payment_reference='', request=None):
        """Step 6: Mark payment as completed"""
        if not user.can_process_payment:
            raise PermissionDenied("You do not have payment completion authority.")
        if payment_request.status != PaymentRequest.Status.PROCESSING:
            raise ValidationError("Payment is not currently being processed.")

        prev = payment_request.status
        payment_request.status = PaymentRequest.Status.PAID
        payment_request.paid_at = timezone.now()
        if payment_request.is_advance_payment:
            payment_request.has_retirement = True
            payment_request.retirement_deadline = (
                timezone.now().date() + timezone.timedelta(days=30)
            )
        payment_request.save(update_fields=['status', 'paid_at', 'has_retirement', 'retirement_deadline', 'updated_at'])

        note = remarks
        if payment_reference:
            note = f"Payment Reference: {payment_reference}. {remarks}"
        cls._record_action(payment_request, user, ApprovalAction.Action.PAYMENT_COMPLETED, prev, payment_request.status, note, request)

        return payment_request

    @classmethod
    @transaction.atomic
    def submit_retirement(cls, payment_request, user, amount_actual, remarks='', request=None):
        """Step 7: Requester submits retirement"""
        if payment_request.requester != user and not user.is_system_admin:
            raise PermissionDenied("Only the requester can submit retirement.")
        if payment_request.status != PaymentRequest.Status.PAID:
            raise ValidationError("Retirement can only be submitted after payment.")

        prev = payment_request.status
        payment_request.status = PaymentRequest.Status.RETIREMENT_SUBMITTED
        payment_request.amount_actual = amount_actual
        payment_request.retired_at = timezone.now()
        payment_request.save(update_fields=['status', 'amount_actual', 'retired_at', 'updated_at'])

        cls._record_action(payment_request, user, ApprovalAction.Action.RETIREMENT_SUBMITTED, prev, payment_request.status, remarks, request)
        return payment_request

    @classmethod
    @transaction.atomic
    def approve_retirement(cls, payment_request, user, remarks='', request=None):
        """Step 8: Finance verifies and approves retirement"""
        if not user.can_verify_retirement:
            raise PermissionDenied("You do not have retirement verification authority.")
        if payment_request.status != PaymentRequest.Status.RETIREMENT_SUBMITTED:
            raise ValidationError("Retirement is not awaiting approval.")

        prev = payment_request.status
        payment_request.status = PaymentRequest.Status.CLOSED
        payment_request.auditor = user
        payment_request.closed_at = timezone.now()
        payment_request.save(update_fields=['status', 'auditor', 'closed_at', 'updated_at'])

        cls._record_action(payment_request, user, ApprovalAction.Action.RETIREMENT_APPROVED, prev, payment_request.status, remarks, request)
        cls._record_action(payment_request, user, ApprovalAction.Action.CLOSED, payment_request.status, payment_request.status, 'Process completed.', request)

        return payment_request

    @classmethod
    @transaction.atomic
    def return_retirement(cls, payment_request, user, remarks, request=None):
        """Step 8 rejected: Return for correction"""
        if not remarks.strip():
            raise ValidationError("Return reason is required.")
        if not user.can_verify_retirement:
            raise PermissionDenied("You do not have retirement verification authority.")

        prev = payment_request.status
        payment_request.status = PaymentRequest.Status.RETIREMENT_REJECTED
        payment_request.save(update_fields=['status', 'updated_at'])

        cls._record_action(payment_request, user, ApprovalAction.Action.RETIREMENT_RETURNED, prev, payment_request.status, remarks, request)
        Comment.objects.create(request=payment_request, author=user, comment_type=Comment.CommentType.REJECTION, content=f"Retirement returned: {remarks}")

        return payment_request
