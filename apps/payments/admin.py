from django.contrib import admin
from .forms import RequestDocumentAdminForm

from .models import PaymentRequest, RequestDocument, Comment, PaymentCategory


@admin.register(PaymentCategory)
class PaymentCategoryAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'is_active', 'max_amount']
    list_filter = ['is_active']


class DocumentInline(admin.TabularInline):
    model = RequestDocument
    extra = 0
    readonly_fields = ['uploaded_by', 'uploaded_at', 'file_size']


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    readonly_fields = ['author', 'created_at']


@admin.register(PaymentRequest)
class PaymentRequestAdmin(admin.ModelAdmin):
    list_display = ['request_number', 'title', 'requester', 'department', 'amount_requested', 'status', 'priority', 'created_at']
    list_filter = ['status', 'priority', 'department', 'created_at']
    search_fields = ['request_number', 'title', 'requester__email', 'requester__first_name']
    readonly_fields = ['request_number', 'created_at', 'updated_at', 'data_hash']
    inlines = [DocumentInline, CommentInline]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

    fieldsets = (
        ('Reference', {'fields': ('request_number', 'status', 'priority')}),
        ('Request', {'fields': ('title', 'description', 'purpose', 'category')}),
        ('Financial', {'fields': ('amount_requested', 'amount_approved', 'amount_actual', 'currency', 'payment_method')}),
        ('Beneficiary', {'fields': ('beneficiary_name', 'beneficiary_bank', 'beneficiary_account')}),
        ('Relations', {'fields': ('requester', 'department', 'reviewer1', 'reviewer2', 'finance_officer', 'auditor')}),
        ('Dates', {'fields': ('created_at', 'updated_at', 'submitted_at', 'needed_by_date', 'paid_at', 'retired_at', 'closed_at')}),
        ('Flags', {'fields': ('is_advance_payment', 'has_retirement', 'retirement_deadline', 'data_hash')}),
    )



@admin.register(RequestDocument)
class RequestDocumentAdmin(admin.ModelAdmin):
    form = RequestDocumentAdminForm
    list_display = ['id', 'request', 'doc_type', 'title', 'file', 'file_size']
    list_filter = ['id', 'request', 'title']
    search_fields = ['id', 'doc_type', 'title', 'file']
    ordering = ['title']
    
    def formfield_for_dbfield(self, db_field, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, **kwargs)

        if db_field.name == "file":
            formfield.widget.attrs.update({
                "role": "uploadcare-uploader",
                "data-public-key": "431f160fc3fcf0ffb783",
            })

        return formfield

    def image_preview(self, obj):
        if obj.file:
            return mark_safe(
                f'<img src="{obj.get_image_url()}" style="max-height:100px;" />'
            )
        return "No Image"

    image_preview.short_description = "Preview"
