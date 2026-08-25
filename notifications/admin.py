from django.contrib import admin
from .models import NotificationLog


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = (
        'customer',
        'bill',
        'email_sent',
        'whatsapp_sent',
        'status',
        'email_time',
        'whatsapp_time',
        'created_at',
    )
    list_filter = ('status', 'email_sent', 'whatsapp_sent', 'created_at')
    search_fields = (
        'customer__name',
        'customer__phone',
        'customer__email',
        'bill__bill_number',
    )
    readonly_fields = ('created_at', 'updated_at')
