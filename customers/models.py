from django.db import models
from django.db.models import Q
from django.urls import reverse


class Customer(models.Model):
    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=20, unique=True)
    email = models.EmailField(blank=True)
    bill_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    table_number = models.CharField(max_length=30, blank=True)
    visit_date = models.DateField()
    notes = models.TextField(blank=True)
    email_sent = models.BooleanField(default=False)
    whatsapp_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-visit_date', '-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['email'],
                condition=~Q(email=''),
                name='unique_customer_email_when_present',
            ),
        ]
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['phone']),
            models.Index(fields=['email']),
            models.Index(fields=['visit_date']),
        ]

    def __str__(self):
        return f'{self.name} ({self.phone})'

    def get_absolute_url(self):
        return reverse('customers:detail', kwargs={'pk': self.pk})
