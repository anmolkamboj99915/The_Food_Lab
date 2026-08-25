import logging

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from billing.models import Bill
from billing.services.bill_service import BillService
from notifications.models import NotificationLog
from notifications.services.email_service import EmailService
from notifications.services.whatsapp_service import WhatsAppService
from pdf.services.pdf_service import PDFService

from customers.models import Customer

logger = logging.getLogger(__name__)


class CustomerService:
    @staticmethod
    def dashboard_stats():
        today = timezone.localdate()
        today_bills = Bill.objects.filter(bill_date=today)
        return {
            'todays_customers': Customer.objects.filter(visit_date=today).count(),
            'todays_bills': today_bills.count(),
            'revenue': today_bills.aggregate(total=Sum('grand_total'))['total'] or 0,
            'whatsapp_delivered': NotificationLog.objects.filter(whatsapp_sent=True).count(),
            'emails_delivered': NotificationLog.objects.filter(email_sent=True).count(),
            'review_requests_sent': NotificationLog.objects.filter(whatsapp_sent=True).count(),
            'total_customers': Customer.objects.count(),
        }

    @staticmethod
    @transaction.atomic
    def save_customer_and_notify(form):
        customer = form.save()
        bill = BillService.create_bill_for_customer(customer, form.cleaned_data)
        CustomerService.sync_customer_latest_bill(customer)
        transaction.on_commit(lambda: CustomerService.process_bill_notifications(customer.pk, bill.pk))
        return customer

    @staticmethod
    @transaction.atomic
    def add_bill_and_notify(customer, form):
        bill = BillService.create_bill_for_customer(customer, form.cleaned_data)
        CustomerService.sync_customer_latest_bill(customer)
        transaction.on_commit(lambda: CustomerService.process_bill_notifications(customer.pk, bill.pk))
        return bill

    @staticmethod
    def sync_customer_latest_bill(customer):
        latest_bill = customer.bills.first()
        customer.bill_amount = latest_bill.grand_total if latest_bill else None
        customer.table_number = latest_bill.table_number if latest_bill else ''
        customer.visit_date = latest_bill.bill_date if latest_bill else customer.visit_date
        customer.email_sent = latest_bill.notification_logs.filter(email_sent=True).exists() if latest_bill else False
        customer.whatsapp_sent = latest_bill.notification_logs.filter(whatsapp_sent=True).exists() if latest_bill else False
        customer.save(update_fields=[
            'bill_amount',
            'table_number',
            'visit_date',
            'email_sent',
            'whatsapp_sent',
            'updated_at',
        ])

    @staticmethod
    def process_bill_notifications(customer_id, bill_id):
        customer = Customer.objects.get(pk=customer_id)
        bill = Bill.objects.select_related('customer').prefetch_related('items').get(pk=bill_id)
        log = NotificationLog.objects.create(customer=customer, bill=bill, status=NotificationLog.STATUS_PENDING)

        response_payload = {}
        try:
            PDFService.generate_bill_pdf(bill)
            response_payload['pdf'] = {'generated': True, 'path': bill.pdf_file.name}
        except Exception as exc:
            logger.exception('PDF generation failed for customer_id=%s bill_id=%s', customer.pk, bill.pk)
            response_payload['pdf'] = {'generated': False, 'error': str(exc)}
            log.response = response_payload
            log.status = NotificationLog.STATUS_FAILED
            log.save(update_fields=['response', 'status', 'updated_at'])
            return log

        whatsapp_pdf_result = WhatsAppService.send_bill_pdf(customer, bill)
        whatsapp_message_result = WhatsAppService.send_thank_you_message(customer, bill)
        email_result = EmailService.send_thank_you_email(customer, bill)

        whatsapp_sent = whatsapp_pdf_result['sent'] and whatsapp_message_result['sent']
        email_sent = email_result['sent']
        now = timezone.now()

        response_payload.update({
            'whatsapp_pdf': whatsapp_pdf_result['response'],
            'whatsapp_message': whatsapp_message_result['response'],
            'email': email_result['response'],
        })

        log.email_sent = email_sent
        log.whatsapp_sent = whatsapp_sent
        log.email_time = now if email_sent else None
        log.whatsapp_time = now if whatsapp_sent else None
        log.response = response_payload
        if email_sent and whatsapp_sent:
            log.status = NotificationLog.STATUS_SENT
        elif email_sent or whatsapp_sent:
            log.status = NotificationLog.STATUS_PARTIAL
        else:
            log.status = NotificationLog.STATUS_FAILED
        log.save()

        customer.email_sent = email_sent
        customer.whatsapp_sent = whatsapp_sent
        if customer.bills.first() == bill:
            customer.save(update_fields=['email_sent', 'whatsapp_sent', 'updated_at'])
        return log

    @staticmethod
    def resend_bill(customer, bill):
        if not bill.pdf_file:
            PDFService.generate_bill_pdf(bill)
        result = WhatsAppService.send_bill_pdf(customer, bill)
        CustomerService._record_resend_log(customer, bill, {'whatsapp_pdf_resend': result['response']}, whatsapp_sent=result['sent'])
        return result

    @staticmethod
    def resend_whatsapp(customer, bill):
        if not bill.pdf_file:
            PDFService.generate_bill_pdf(bill)
        pdf_result = WhatsAppService.send_bill_pdf(customer, bill)
        message_result = WhatsAppService.send_thank_you_message(customer, bill)
        sent = pdf_result['sent'] and message_result['sent']
        CustomerService._record_resend_log(
            customer,
            bill,
            {'whatsapp_pdf_resend': pdf_result['response'], 'whatsapp_message_resend': message_result['response']},
            whatsapp_sent=sent,
        )
        customer.whatsapp_sent = sent
        customer.save(update_fields=['whatsapp_sent', 'updated_at'])
        return {'sent': sent, 'response': {'pdf': pdf_result['response'], 'message': message_result['response']}}

    @staticmethod
    def resend_email(customer, bill):
        result = EmailService.send_thank_you_email(customer, bill)
        CustomerService._record_resend_log(customer, bill, {'email_resend': result['response']}, email_sent=result['sent'])
        customer.email_sent = result['sent']
        customer.save(update_fields=['email_sent', 'updated_at'])
        return result

    @staticmethod
    def _record_resend_log(customer, bill, response, email_sent=False, whatsapp_sent=False):
        NotificationLog.objects.create(
            customer=customer,
            bill=bill,
            email_sent=email_sent,
            whatsapp_sent=whatsapp_sent,
            email_time=timezone.now() if email_sent else None,
            whatsapp_time=timezone.now() if whatsapp_sent else None,
            response=response,
            status=NotificationLog.STATUS_SENT if email_sent or whatsapp_sent else NotificationLog.STATUS_FAILED,
        )
