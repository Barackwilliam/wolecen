from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['event_type', 'user', 'model_name', 'object_repr', 'ip_address', 'timestamp']
    list_filter = ['event_type', 'timestamp']
    # readonly_fields = list(AuditLog._meta.get_fields())
    readonly_fields = [field.name for field in AuditLog._meta.get_fields()]
    search_fields = ['user__email', 'object_repr', 'ip_address']
    date_hierarchy = 'timestamp'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
