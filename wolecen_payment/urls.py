from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

admin.site.site_header = 'Wolecen EGL — Admin Portal'
admin.site.site_title = 'Wolecen Admin'
admin.site.index_title = 'System Administration'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(pattern_name='dashboard:home'), name='root'),
    path('auth/', include('apps.accounts.urls', namespace='accounts')),
    path('dashboard/', include('apps.payments.urls_dashboard', namespace='dashboard')),
    path('payments/', include('apps.payments.urls', namespace='payments')),
    path('approvals/', include('apps.approvals.urls', namespace='approvals')),
    path('audit/', include('apps.audit.urls', namespace='audit')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
