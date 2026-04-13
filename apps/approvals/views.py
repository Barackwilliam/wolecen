from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator

from apps.payments.models import PaymentRequest
from apps.approvals.services import ApprovalService


@login_required
def pending_l1_view(request):
    if not request.user.can_approve_level1:
        messages.error(request, 'Access denied.')
        return redirect('dashboard:home')

    qs = PaymentRequest.objects.filter(
        status=PaymentRequest.Status.SUBMITTED
    ).select_related('requester', 'department').order_by('-priority', '-submitted_at')

    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'approvals/queue.html', {
        'page_obj': page_obj,
        'queue_title': 'Level 1 Approval Queue',
        'queue_subtitle': 'Requests awaiting Supervisor approval',
        'queue_type': 'L1',
        'total': qs.count(),
    })


@login_required
def pending_l2_view(request):
    if not request.user.can_approve_level2:
        messages.error(request, 'Access denied.')
        return redirect('dashboard:home')

    qs = PaymentRequest.objects.filter(
        status=PaymentRequest.Status.APPROVED_L1
    ).select_related('requester', 'department', 'reviewer1').order_by('-priority', '-created_at')

    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'approvals/queue.html', {
        'page_obj': page_obj,
        'queue_title': 'Level 2 Approval Queue',
        'queue_subtitle': 'Requests awaiting Finance Controller approval',
        'queue_type': 'L2',
        'total': qs.count(),
    })


@login_required
def finance_queue_view(request):
    if not request.user.can_process_payment:
        messages.error(request, 'Access denied.')
        return redirect('dashboard:home')

    qs = PaymentRequest.objects.filter(
        status__in=[PaymentRequest.Status.APPROVED_L2, PaymentRequest.Status.PROCESSING]
    ).select_related('requester', 'department', 'reviewer2').order_by('-priority', '-created_at')

    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'approvals/queue.html', {
        'page_obj': page_obj,
        'queue_title': 'Finance Payment Queue',
        'queue_subtitle': 'Approved requests awaiting payment processing',
        'queue_type': 'FINANCE',
        'total': qs.count(),
    })


@login_required
def retirement_queue_view(request):
    if not request.user.can_verify_retirement:
        messages.error(request, 'Access denied.')
        return redirect('dashboard:home')

    qs = PaymentRequest.objects.filter(
        status=PaymentRequest.Status.RETIREMENT_SUBMITTED
    ).select_related('requester', 'department').order_by('-retired_at')

    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'approvals/queue.html', {
        'page_obj': page_obj,
        'queue_title': 'Retirement Verification Queue',
        'queue_subtitle': 'Submitted retirements awaiting finance verification',
        'queue_type': 'RETIREMENT',
        'total': qs.count(),
    })


# ─── APPROVAL ACTIONS ─────────────────────────────────────────
@login_required
@require_POST
def approve_l1_view(request, pk):
    payment = get_object_or_404(PaymentRequest, pk=pk)
    try:
        ApprovalService.approve_level1(
            payment, request.user,
            remarks=request.POST.get('remarks', ''),
            amount_approved=request.POST.get('amount_approved') or None,
            request=request,
        )
        messages.success(request, f'{payment.request_number} approved and forwarded to Level 2.')
    except Exception as e:
        messages.error(request, str(e))
    return redirect('payments:detail', pk=pk)


@login_required
@require_POST
def reject_l1_view(request, pk):
    payment = get_object_or_404(PaymentRequest, pk=pk)
    try:
        ApprovalService.reject_level1(
            payment, request.user,
            remarks=request.POST.get('remarks', ''),
            request=request,
        )
        messages.warning(request, f'{payment.request_number} rejected and returned to requester.')
    except Exception as e:
        messages.error(request, str(e))
    return redirect('payments:detail', pk=pk)


@login_required
@require_POST
def approve_l2_view(request, pk):
    payment = get_object_or_404(PaymentRequest, pk=pk)
    try:
        ApprovalService.approve_level2(
            payment, request.user,
            remarks=request.POST.get('remarks', ''),
            amount_approved=request.POST.get('amount_approved') or None,
            request=request,
        )
        messages.success(request, f'{payment.request_number} approved by Finance Controller. Forwarded to payment processing.')
    except Exception as e:
        messages.error(request, str(e))
    return redirect('payments:detail', pk=pk)


@login_required
@require_POST
def reject_l2_view(request, pk):
    payment = get_object_or_404(PaymentRequest, pk=pk)
    try:
        ApprovalService.reject_level2(
            payment, request.user,
            remarks=request.POST.get('remarks', ''),
            request=request,
        )
        messages.warning(request, f'{payment.request_number} rejected by Finance Controller.')
    except Exception as e:
        messages.error(request, str(e))
    return redirect('payments:detail', pk=pk)


@login_required
@require_POST
def process_payment_view(request, pk):
    payment = get_object_or_404(PaymentRequest, pk=pk)
    try:
        ApprovalService.process_payment(
            payment, request.user,
            remarks=request.POST.get('remarks', ''),
            request=request,
        )
        messages.info(request, f'Payment processing initiated for {payment.request_number}.')
    except Exception as e:
        messages.error(request, str(e))
    return redirect('payments:detail', pk=pk)


@login_required
@require_POST
def complete_payment_view(request, pk):
    payment = get_object_or_404(PaymentRequest, pk=pk)
    try:
        ApprovalService.complete_payment(
            payment, request.user,
            remarks=request.POST.get('remarks', ''),
            payment_reference=request.POST.get('payment_reference', ''),
            request=request,
        )
        messages.success(request, f'Payment for {payment.request_number} marked as complete.')
    except Exception as e:
        messages.error(request, str(e))
    return redirect('payments:detail', pk=pk)


@login_required
@require_POST
def approve_retirement_view(request, pk):
    payment = get_object_or_404(PaymentRequest, pk=pk)
    try:
        ApprovalService.approve_retirement(
            payment, request.user,
            remarks=request.POST.get('remarks', ''),
            request=request,
        )
        messages.success(request, f'{payment.request_number} retirement approved. Request CLOSED.')
    except Exception as e:
        messages.error(request, str(e))
    return redirect('payments:detail', pk=pk)


@login_required
@require_POST
def return_retirement_view(request, pk):
    payment = get_object_or_404(PaymentRequest, pk=pk)
    try:
        ApprovalService.return_retirement(
            payment, request.user,
            remarks=request.POST.get('remarks', ''),
            request=request,
        )
        messages.warning(request, f'Retirement for {payment.request_number} returned for correction.')
    except Exception as e:
        messages.error(request, str(e))
    return redirect('payments:detail', pk=pk)
