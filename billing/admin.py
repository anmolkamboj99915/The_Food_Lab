from django.contrib import admin

from .models import Bill, BillItem


class BillItemInline(admin.TabularInline):
    model = BillItem
    extra = 0
    readonly_fields = ('total',)


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ('bill_number', 'customer', 'bill_date', 'bill_time', 'grand_total', 'payment_mode', 'pdf_file')
    list_filter = ('bill_date', 'payment_mode', 'created_at')
    search_fields = ('bill_number', 'customer__name', 'customer__phone', 'customer__email')
    date_hierarchy = 'bill_date'
    readonly_fields = ('created_at', 'updated_at')
    inlines = [BillItemInline]


@admin.register(BillItem)
class BillItemAdmin(admin.ModelAdmin):
    list_display = ('bill', 'name', 'quantity', 'price', 'total')
    search_fields = ('bill__bill_number', 'name')
