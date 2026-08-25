from django.db import models


class NotificationLog(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_SENT = 'sent'
    STATUS_PARTIAL = 'partial'
    STATUS_FAILED = 'failed'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_SENT, 'Sent'),
        (STATUS_PARTIAL, 'Partial'),
        (STATUS_FAILED, 'Failed'),
    ]

    customer = models.ForeignKey('customers.Customer', on_delete=models.CASCADE, related_name='notification_logs')
    bill = models.ForeignKey('billing.Bill', on_delete=models.CASCADE, related_name='notification_logs')
    email_sent = models.BooleanField(default=False)
    whatsapp_sent = models.BooleanField(default=False)
    email_time = models.DateTimeField(null=True, blank=True)
    whatsapp_time = models.DateTimeField(null=True, blank=True)
    response = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['email_sent']),
            models.Index(fields=['whatsapp_sent']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f'{self.customer.name} - {self.bill.bill_number} - {self.status}'
