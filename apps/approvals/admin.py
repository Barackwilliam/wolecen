from django.contrib import admin
from .models import ApprovalAction, ApprovalDelegate


@admin.register(ApprovalAction)
class ApprovalActionAdmin(admin.ModelAdmin):
    list_display = ['request', 'action', 'actor', 'timestamp']
    list_filter = ['action', 'timestamp']
    readonly_fields = ['id', 'timestamp']
    search_fields = ['request__request_number', 'actor__email']


@admin.register(ApprovalDelegate)
class ApprovalDelegateAdmin(admin.ModelAdmin):
    list_display = ['delegator', 'delegate', 'start_date', 'end_date', 'is_active']
    list_filter = ['is_active']
    search_fields = ['delegator__email', 'delegate__email']
