from django.urls import path
from . import views

app_name = 'approvals'

urlpatterns = [
    # Queues
    path('level-1/', views.pending_l1_view, name='pending_l1'),
    path('level-2/', views.pending_l2_view, name='pending_l2'),
    path('finance/', views.finance_queue_view, name='finance_queue'),
    path('retirement/', views.retirement_queue_view, name='retirement_queue'),
    # Actions
    path('<uuid:pk>/approve-l1/', views.approve_l1_view, name='approve_l1'),
    path('<uuid:pk>/reject-l1/', views.reject_l1_view, name='reject_l1'),
    path('<uuid:pk>/approve-l2/', views.approve_l2_view, name='approve_l2'),
    path('<uuid:pk>/reject-l2/', views.reject_l2_view, name='reject_l2'),
    path('<uuid:pk>/process-payment/', views.process_payment_view, name='process_payment'),
    path('<uuid:pk>/complete-payment/', views.complete_payment_view, name='complete_payment'),
    path('<uuid:pk>/approve-retirement/', views.approve_retirement_view, name='approve_retirement'),
    path('<uuid:pk>/return-retirement/', views.return_retirement_view, name='return_retirement'),
]
