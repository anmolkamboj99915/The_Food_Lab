from decimal import Decimal

from django.db import models
from django.urls import reverse


class Bill(models.Model):
    PAYMENT_CASH = 'cash'
    PAYMENT_CARD = 'card'
    PAYMENT_UPI = 'upi'
    PAYMENT_ONLINE = 'online'
    PAYMENT_OTHER = 'other'
    PAYMENT_MODE_CHOICES = [
        (PAYMENT_CASH, 'Cash'),
        (PAYMENT_CARD, 'Card'),
        (PAYMENT_UPI, 'UPI'),
        (PAYMENT_ONLINE, 'Online'),
        (PAYMENT_OTHER, 'Other'),
    ]

    customer = models.ForeignKey('customers.Customer', on_delete=models.CASCADE, related_name='bills')
    bill_number = models.CharField(max_length=50, unique=True)
    table_number = models.CharField(max_length=30, blank=True)
    bill_date = models.DateField()
    bill_time = models.TimeField()
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    gst_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    gst_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    grand_total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    payment_mode = models.CharField(max_length=20, choices=PAYMENT_MODE_CHOICES, default=PAYMENT_CASH)
    pdf_file = models.FileField(upload_to='bills/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-bill_date', '-bill_time', '-created_at']
        indexes = [
            models.Index(fields=['bill_number']),
            models.Index(fields=['bill_date']),
            models.Index(fields=['payment_mode']),
        ]

    def __str__(self):
        return f'{self.bill_number} - {self.customer.name}'

    def get_absolute_url(self):
        return reverse('customers:detail', kwargs={'pk': self.customer_id})


class BillItem(models.Model):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=160)
    quantity = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('1.00'))
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f'{self.name} x {self.quantity}'
