from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('', views.payment_list_view, name='list'),
    path('new/', views.payment_create_view, name='create'),
    path('my/', views.my_requests_view, name='my_requests'),
    path('<uuid:pk>/', views.payment_detail_view, name='detail'),
    path('<uuid:pk>/edit/', views.payment_edit_view, name='edit'),
    path('<uuid:pk>/submit/', views.submit_request_view, name='submit'),
    path('<uuid:pk>/comment/', views.add_comment_view, name='add_comment'),
    path('<uuid:pk>/retirement/', views.submit_retirement_view, name='submit_retirement'),
    path('<uuid:pk>/upload/', views.upload_doc_view, name='upload_doc'),
    path('<uuid:pk>/pdf/', views.export_pdf_view, name='export_pdf'),
    path('<uuid:pk>/print/', views.print_view, name='print'),
    path('export/excel/', views.export_excel_view, name='export_excel'),
]
