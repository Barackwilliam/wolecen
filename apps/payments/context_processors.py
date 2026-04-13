from apps.payments.models import PaymentRequest


def notification_count(request):
    """
    Adds pending counts to every template context.
    Properties (no parentheses) since can_* are now @property on User model.
    """
    if not request.user.is_authenticated:
        return {}

    counts = {}
    user = request.user

    try:
        if user.can_approve_level1:
            counts['pending_l1_count'] = PaymentRequest.objects.filter(
                status=PaymentRequest.Status.SUBMITTED
            ).count()

        if user.can_approve_level2:
            counts['pending_l2_count'] = PaymentRequest.objects.filter(
                status=PaymentRequest.Status.APPROVED_L1
            ).count()

        if user.can_process_payment:
            counts['finance_count'] = PaymentRequest.objects.filter(
                status__in=[PaymentRequest.Status.APPROVED_L2, PaymentRequest.Status.PROCESSING]
            ).count()

        if user.can_verify_retirement:
            counts['retirement_count'] = PaymentRequest.objects.filter(
                status=PaymentRequest.Status.RETIREMENT_SUBMITTED
            ).count()

        counts['notification_count'] = sum(counts.values())

    except Exception:
        # Never break a page render due to notification count failure
        counts['notification_count'] = 0

    return counts
