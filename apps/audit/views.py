from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.utils import timezone

from .models import AuditLog
from apps.payments.models import PaymentRequest


@login_required
def audit_log_view(request):
    if not (request.user.is_system_admin or request.user.is_auditor):
        messages.error(request, 'Access denied.')
        return redirect('dashboard:home')

    qs = AuditLog.objects.select_related('user').order_by('-timestamp')

    q = request.GET.get('q', '')
    event_type = request.GET.get('event_type', '')
    date_from = request.GET.get('date_from', '')

    if q:
        qs = qs.filter(Q(user__email__icontains=q) | Q(object_repr__icontains=q))
    if event_type:
        qs = qs.filter(event_type=event_type)
    if date_from:
        qs = qs.filter(timestamp__date__gte=date_from)

    paginator = Paginator(qs, 50)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'audit/log.html', {
        'page_obj': page_obj,
        'event_choices': AuditLog.EventType.choices,
        'total': qs.count(),
    })


@login_required
def reports_view(request):
    if not (request.user.is_system_admin or request.user.is_auditor or request.user.is_finance):
        messages.error(request, 'Access denied.')
        return redirect('dashboard:home')

    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0)

    # Summary stats
    all_req = PaymentRequest.objects.all()

    stats = {
        'total_requests': all_req.count(),
        'total_amount': all_req.aggregate(t=Sum('amount_requested'))['t'] or 0,
        'total_approved': all_req.filter(amount_approved__isnull=False).aggregate(t=Sum('amount_approved'))['t'] or 0,
        'total_paid': all_req.filter(status__in=['PAID', 'CLOSED']).aggregate(t=Sum('amount_approved'))['t'] or 0,
        'closed_count': all_req.filter(status='CLOSED').count(),
        'rejected_count': all_req.filter(status__in=['REJECTED_L1', 'REJECTED_L2']).count(),
        'pending_retirement': all_req.filter(status='PAID', has_retirement=True).count(),
    }

    # By status
    by_status = list(all_req.values('status').annotate(
        count=Count('id'), total=Sum('amount_requested')
    ).order_by('-count'))

    # By department
    by_dept = list(all_req.values('department__name').annotate(
        count=Count('id'), total=Sum('amount_requested')
    ).order_by('-total')[:10])

    # Monthly trend (last 6 months)
    monthly = []
    for i in range(5, -1, -1):
        month = now.replace(day=1) - timezone.timedelta(days=30*i)
        month_end = (month.replace(day=28) + timezone.timedelta(days=4)).replace(day=1)
        count = all_req.filter(created_at__gte=month, created_at__lt=month_end).count()
        monthly.append({'month': month.strftime('%b %Y'), 'count': count})

    return render(request, 'audit/reports.html', {
        'stats': stats,
        'by_status': by_status,
        'by_dept': by_dept,
        'monthly': monthly,
    })
