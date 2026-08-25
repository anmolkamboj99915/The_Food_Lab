from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.utils import timezone

from billing.models import Bill, BillItem


MONEY_QUANT = Decimal('0.01')


class BillService:
    @staticmethod
    @transaction.atomic
    def create_bill_for_customer(customer, cleaned_data):
        bill_values = BillService._bill_values(cleaned_data)

        bill = Bill.objects.create(
            customer=customer,
            bill_number=cleaned_data['bill_number'],
            table_number=cleaned_data.get('table_number', ''),
            bill_date=cleaned_data['visit_date'],
            bill_time=timezone.localtime().time(),
            subtotal=bill_values['subtotal'],
            gst_percent=bill_values['gst_percent'],
            gst_amount=bill_values['gst_amount'],
            discount_amount=bill_values['discount_amount'],
            grand_total=bill_values['grand_total'],
            payment_mode=cleaned_data['payment_mode'],
        )

        BillService._replace_items(bill, cleaned_data['parsed_items'])
        return bill

    @staticmethod
    @transaction.atomic
    def update_bill(bill, cleaned_data):
        bill_values = BillService._bill_values(cleaned_data)
        bill.bill_number = cleaned_data['bill_number']
        bill.table_number = cleaned_data.get('table_number', '')
        bill.bill_date = cleaned_data['visit_date']
        bill.subtotal = bill_values['subtotal']
        bill.gst_percent = bill_values['gst_percent']
        bill.gst_amount = bill_values['gst_amount']
        bill.discount_amount = bill_values['discount_amount']
        bill.grand_total = bill_values['grand_total']
        bill.payment_mode = cleaned_data['payment_mode']
        bill.save(update_fields=[
            'bill_number',
            'table_number',
            'bill_date',
            'subtotal',
            'gst_percent',
            'gst_amount',
            'discount_amount',
            'grand_total',
            'payment_mode',
            'updated_at',
        ])
        bill.items.all().delete()
        BillService._replace_items(bill, cleaned_data['parsed_items'])
        if hasattr(bill, '_prefetched_objects_cache'):
            bill._prefetched_objects_cache.pop('items', None)
        return bill

    @staticmethod
    def _bill_values(cleaned_data):
        items_data = cleaned_data['parsed_items']
        subtotal = sum(
            (item['quantity'] * item['price']).quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)
            for item in items_data
        )
        form_bill_amount = cleaned_data.get('bill_amount') or subtotal
        if form_bill_amount != subtotal:
            subtotal = form_bill_amount.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)

        gst_percent = (cleaned_data.get('gst') or Decimal('0.00')).quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)
        discount_amount = (cleaned_data.get('discount') or Decimal('0.00')).quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)
        gst_amount = (subtotal * gst_percent / Decimal('100')).quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)
        grand_total = (subtotal + gst_amount - discount_amount).quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)
        if grand_total < 0:
            grand_total = Decimal('0.00')

        return {
            'subtotal': subtotal,
            'gst_percent': gst_percent,
            'gst_amount': gst_amount,
            'discount_amount': discount_amount,
            'grand_total': grand_total,
        }

    @staticmethod
    def _replace_items(bill, items_data):
        BillItem.objects.bulk_create(
            [
                BillItem(
                    bill=bill,
                    name=item['name'],
                    quantity=item['quantity'],
                    price=item['price'],
                    total=(item['quantity'] * item['price']).quantize(MONEY_QUANT, rounding=ROUND_HALF_UP),
                )
                for item in items_data
            ]
        )
