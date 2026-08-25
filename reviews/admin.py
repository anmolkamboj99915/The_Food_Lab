from django.contrib import admin
from .models import ReviewLinkClick


@admin.register(ReviewLinkClick)
class ReviewLinkClickAdmin(admin.ModelAdmin):
    list_display = ('customer', 'source', 'ip_address', 'clicked_at')
    list_filter = ('source', 'clicked_at')
    search_fields = ('customer__name', 'customer__phone', 'customer__email', 'ip_address')
    date_hierarchy = 'clicked_at'
    readonly_fields = ('clicked_at',)
