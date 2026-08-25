from decimal import Decimal, InvalidOperation

from django import forms
from django.utils import timezone

from billing.models import Bill

from .models import Customer


class CustomerForm(forms.ModelForm):
    bill_number = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Bill number'}),
    )
    gst = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        min_value=Decimal('0.00'),
        required=False,
        initial=Decimal('0.00'),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'GST %', 'step': '0.01', 'min': '0'}),
    )
    discount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('0.00'),
        required=False,
        initial=Decimal('0.00'),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Discount amount', 'step': '0.01', 'min': '0'}),
    )
    items_ordered = forms.CharField(
        widget=forms.Textarea(
            attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'One item per line, for example: Pasta, 2, 250',
            }
        )
    )
    payment_mode = forms.ChoiceField(
        choices=Bill.PAYMENT_MODE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    class Meta:
        model = Customer
        fields = [
            'name',
            'phone',
            'email',
            'bill_amount',
            'table_number',
            'visit_date',
            'notes',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Customer name'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Mobile number'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email address'}),
            'bill_amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Bill amount', 'step': '0.01', 'min': '0'}),
            'table_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Table number'}),
            'visit_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Notes'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.show_bill_fields = not self.instance.pk
        if not self.instance.pk and not self.initial.get('visit_date'):
            self.fields['visit_date'].initial = timezone.localdate()
        if not self.initial.get('bill_number'):
            self.fields['bill_number'].initial = f'FL-{timezone.localtime().strftime("%Y%m%d%H%M%S")}'
        if self.instance.pk:
            for field_name in ['bill_number', 'gst', 'discount', 'items_ordered', 'payment_mode']:
                self.fields[field_name].required = False
        self.fields['email'].required = False
        self.fields['bill_amount'].required = not self.instance.pk
        self.fields['table_number'].required = False
        self.fields['notes'].required = False

    def clean_phone(self):
        phone = ''.join(self.cleaned_data['phone'].split())
        queryset = Customer.objects.filter(phone__iexact=phone)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise forms.ValidationError('A customer with this mobile number already exists.')
        return phone

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if not email:
            return ''
        queryset = Customer.objects.filter(email__iexact=email)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise forms.ValidationError('A customer with this email address already exists.')
        return email

    def clean_bill_amount(self):
        bill_amount = self.cleaned_data.get('bill_amount')
        if bill_amount is None:
            if self.instance.pk:
                return bill_amount
            raise forms.ValidationError('Bill amount is required.')
        if bill_amount < 0:
            raise forms.ValidationError('Bill amount cannot be negative.')
        return bill_amount

    def clean_bill_number(self):
        bill_number = (self.cleaned_data.get('bill_number') or '').strip().upper()
        if self.instance.pk and not bill_number:
            return bill_number
        if Bill.objects.filter(bill_number__iexact=bill_number).exists():
            raise forms.ValidationError('A bill with this bill number already exists.')
        return bill_number

    def clean_items_ordered(self):
        value = self.cleaned_data.get('items_ordered', '').strip()
        if self.instance.pk and not value:
            self.cleaned_data['parsed_items'] = []
            return value
        if not value:
            raise forms.ValidationError('Items ordered are required.')

        parsed_items = []
        for line_number, raw_line in enumerate(value.splitlines(), start=1):
            line = raw_line.strip()
            if not line:
                continue
            parts = [part.strip() for part in line.split(',')]
            if len(parts) != 3:
                raise forms.ValidationError(
                    f'Line {line_number} must be written as Item Name, Quantity, Price.'
                )
            name, quantity_raw, price_raw = parts
            if not name:
                raise forms.ValidationError(f'Line {line_number} item name is required.')
            try:
                quantity = Decimal(quantity_raw)
                price = Decimal(price_raw)
            except InvalidOperation as exc:
                raise forms.ValidationError(f'Line {line_number} quantity and price must be numbers.') from exc
            if quantity <= 0 or price < 0:
                raise forms.ValidationError(f'Line {line_number} quantity must be positive and price cannot be negative.')
            parsed_items.append({'name': name, 'quantity': quantity, 'price': price})

        if not parsed_items:
            raise forms.ValidationError('At least one ordered item is required.')
        self.cleaned_data['parsed_items'] = parsed_items
        return value


class BillForm(forms.Form):
    bill_number = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Bill number'}),
    )
    bill_amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('0.00'),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Bill amount', 'step': '0.01', 'min': '0'}),
    )
    table_number = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Table number'}),
    )
    visit_date = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    gst = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        min_value=Decimal('0.00'),
        required=False,
        initial=Decimal('0.00'),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'GST %', 'step': '0.01', 'min': '0'}),
    )
    discount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('0.00'),
        required=False,
        initial=Decimal('0.00'),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Discount amount', 'step': '0.01', 'min': '0'}),
    )
    items_ordered = forms.CharField(
        widget=forms.Textarea(
            attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'One item per line, for example: Pasta, 2, 250',
            }
        )
    )
    payment_mode = forms.ChoiceField(
        choices=Bill.PAYMENT_MODE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    def __init__(self, *args, **kwargs):
        self.bill = kwargs.pop('bill', None)
        super().__init__(*args, **kwargs)
        if self.bill:
            self.fields['bill_number'].initial = self.bill.bill_number
            self.fields['bill_amount'].initial = self.bill.subtotal
            self.fields['table_number'].initial = self.bill.table_number
            self.fields['visit_date'].initial = self.bill.bill_date
            self.fields['gst'].initial = self.bill.gst_percent
            self.fields['discount'].initial = self.bill.discount_amount
            self.fields['payment_mode'].initial = self.bill.payment_mode
            self.fields['items_ordered'].initial = '\n'.join(
                f'{item.name}, {item.quantity}, {item.price}' for item in self.bill.items.all()
            )
        else:
            if not self.initial.get('bill_number'):
                self.fields['bill_number'].initial = f'FL-{timezone.localtime().strftime("%Y%m%d%H%M%S")}'
            if not self.initial.get('visit_date'):
                self.fields['visit_date'].initial = timezone.localdate()

    def clean_bill_number(self):
        bill_number = (self.cleaned_data.get('bill_number') or '').strip().upper()
        queryset = Bill.objects.filter(bill_number__iexact=bill_number)
        if self.bill:
            queryset = queryset.exclude(pk=self.bill.pk)
        if queryset.exists():
            raise forms.ValidationError('A bill with this bill number already exists.')
        return bill_number

    def clean_items_ordered(self):
        value = self.cleaned_data.get('items_ordered', '').strip()
        if not value:
            raise forms.ValidationError('Items ordered are required.')

        parsed_items = []
        for line_number, raw_line in enumerate(value.splitlines(), start=1):
            line = raw_line.strip()
            if not line:
                continue
            parts = [part.strip() for part in line.split(',')]
            if len(parts) != 3:
                raise forms.ValidationError(
                    f'Line {line_number} must be written as Item Name, Quantity, Price.'
                )
            name, quantity_raw, price_raw = parts
            if not name:
                raise forms.ValidationError(f'Line {line_number} item name is required.')
            try:
                quantity = Decimal(quantity_raw)
                price = Decimal(price_raw)
            except InvalidOperation as exc:
                raise forms.ValidationError(f'Line {line_number} quantity and price must be numbers.') from exc
            if quantity <= 0 or price < 0:
                raise forms.ValidationError(f'Line {line_number} quantity must be positive and price cannot be negative.')
            parsed_items.append({'name': name, 'quantity': quantity, 'price': price})

        if not parsed_items:
            raise forms.ValidationError('At least one ordered item is required.')
        self.cleaned_data['parsed_items'] = parsed_items
        return value
