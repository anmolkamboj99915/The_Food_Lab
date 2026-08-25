from django.contrib import admin
from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'phone',
        'email',
        'visit_date',
        'bill_amount',
        'table_number',
        'email_sent',
        'whatsapp_sent',
        'created_at',
    )
    list_filter = ('visit_date', 'email_sent', 'whatsapp_sent', 'created_at')
    search_fields = ('name', 'phone', 'email')
    date_hierarchy = 'visit_date'
    ordering = ('-visit_date', '-created_at')
    readonly_fields = ('created_at', 'updated_at')
