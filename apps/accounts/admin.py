from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Department
from .forms import UserAdminForm



@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'code']


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = UserAdminForm
    list_display = ['email', 'full_name', 'role', 'department', 'employee_id', 'is_active']
    list_filter = ['role', 'is_active', 'department']
    search_fields = ['email', 'first_name', 'last_name', 'employee_id']
    ordering = ['first_name']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone', 'avatar')}),
        ('Work Info', {'fields': ('employee_id', 'role', 'department')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'force_password_change')}),
        ('Dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'first_name', 'last_name', 'role', 'department', 'password1', 'password2'),
        }),
    )
    def formfield_for_dbfield(self, db_field, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, **kwargs)

        if db_field.name == "avatar":
            formfield.widget.attrs.update({
                "role": "uploadcare-uploader",
                "data-public-key": "431f160fc3fcf0ffb783",
            })

        return formfield

    def image_preview(self, obj):
        if obj.avatar:
            return mark_safe(
                f'<img src="{obj.get_image_url()}" style="max-height:100px;" />'
            )
        return "No Image"

    image_preview.short_description = "Preview"





