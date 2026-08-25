from django.db import models


class ReviewLinkClick(models.Model):
    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='review_clicks',
    )
    source = models.CharField(max_length=50, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    clicked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-clicked_at']
        indexes = [
            models.Index(fields=['clicked_at']),
            models.Index(fields=['source']),
        ]

    def __str__(self):
        customer_name = self.customer.name if self.customer else 'Anonymous'
        return f'{customer_name} review click at {self.clicked_at:%Y-%m-%d %H:%M}'
