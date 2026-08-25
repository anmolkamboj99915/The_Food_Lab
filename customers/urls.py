from django.urls import path

from . import views

app_name = 'customers'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('customers/', views.customer_list, name='list'),
    path('customers/add/', views.customer_create, name='create'),
    path('customers/export/', views.export_customers_excel, name='export'),
    path('bills/<int:bill_id>/download/', views.download_bill, name='download_bill'),
    path('customers/<int:pk>/', views.customer_detail, name='detail'),
    path('customers/<int:pk>/edit/', views.customer_update, name='edit'),
    path('customers/<int:pk>/delete/', views.customer_delete, name='delete'),
    path('customers/<int:pk>/bills/add/', views.bill_create, name='bill_create'),
    path('customers/<int:pk>/bills/<int:bill_id>/edit/', views.bill_update, name='bill_edit'),
    path('customers/<int:pk>/bills/<int:bill_id>/delete/', views.bill_delete, name='bill_delete'),
    path('customers/<int:pk>/bills/<int:bill_id>/resend-bill/', views.resend_bill, name='resend_bill'),
    path('customers/<int:pk>/bills/<int:bill_id>/resend-whatsapp/', views.resend_whatsapp, name='resend_whatsapp'),
    path('customers/<int:pk>/bills/<int:bill_id>/resend-email/', views.resend_email, name='resend_email'),
]
