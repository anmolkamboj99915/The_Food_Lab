from django.urls import path

from .views import whatsapp_webhook

app_name = 'notifications'

urlpatterns = [
    path('webhook/', whatsapp_webhook, name='whatsapp_webhook'),
]