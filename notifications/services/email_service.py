import logging
import smtplib
from email.mime.image import MIMEImage

from django.conf import settings
from django.contrib.staticfiles import finders
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger('notifications.email')


class EmailService:
    SMTP_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

    @staticmethod
    def send_thank_you_email(customer, bill=None):
        if not customer.email:
            logger.info('Email skipped for customer_id=%s because no email is available.', customer.pk)
            return {'sent': False, 'response': {'error': 'Customer email is empty.'}}

        configuration_error = EmailService._configuration_error()
        if configuration_error:
            logger.warning(
                'Email skipped for customer_id=%s bill_id=%s email=%s: %s',
                customer.pk,
                getattr(bill, 'pk', None),
                customer.email,
                configuration_error,
            )
            return {'sent': False, 'response': {'error': configuration_error}}

        context = {
            'customer': customer,
            'bill': bill,
            'restaurant_name': settings.RESTAURANT_NAME,
            'google_review_url': settings.FOOD_LAB_GOOGLE_REVIEW_URL,
            'instagram_url': settings.FOOD_LAB_INSTAGRAM_URL,
            'instagram_username': settings.FOOD_LAB_INSTAGRAM_USERNAME,
            'logo_url': settings.RESTAURANT_LOGO_URL,
            'instagram_qr_content_id': 'instagram_qr',
        }
        subject = 'Thank You For Visiting Food Lab \u2764\ufe0f'
        html_body = render_to_string('emails/customer_thank_you.html', context)
        text_body = EmailService._text_body(customer, bill)

        try:
            message = EmailMultiAlternatives(
                subject=subject,
                body=text_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[customer.email],
            )
            message.attach_alternative(html_body, 'text/html')
            EmailService._attach_instagram_qr(message)
            if bill and bill.pdf_file:
                message.attach_file(bill.pdf_file.path, mimetype='application/pdf')
            sent_count = message.send(fail_silently=False)
            logger.info('Email success for customer_id=%s bill_id=%s email=%s', customer.pk, getattr(bill, 'pk', None), customer.email)
            return {'sent': sent_count > 0, 'response': {'sent_count': sent_count}}
        except (OSError, smtplib.SMTPException) as exc:
            logger.warning(
                'Email delivery failed for customer_id=%s bill_id=%s email=%s: %s',
                customer.pk,
                getattr(bill, 'pk', None),
                customer.email,
                exc,
            )
            return {'sent': False, 'response': {'error': str(exc)}}
        except Exception as exc:
            logger.exception('Email failure for customer_id=%s bill_id=%s email=%s', customer.pk, getattr(bill, 'pk', None), customer.email)
            return {'sent': False, 'response': {'error': str(exc)}}

    @staticmethod
    def _text_body(customer, bill):
        bill_lines = ''
        if bill:
            bill_lines = (
                f'\nBill Number: {bill.bill_number}'
                f'\nGrand Total: Rs. {bill.grand_total}'
                f'\nPayment Mode: {bill.get_payment_mode_display()}\n'
            )
        return (
            f'Hi {customer.name},\n\n'
            'Thank you for visiting Food Lab.\n'
            f'{bill_lines}\n'
            f'Google Review: {settings.FOOD_LAB_GOOGLE_REVIEW_URL}\n'
            f'Instagram: {settings.FOOD_LAB_INSTAGRAM_URL}\n\n'
            'See you again!\nFood Lab'
        )

    @staticmethod
    def _attach_instagram_qr(message):
        qr_path = finders.find('images/instagram_qr.jpg')
        if not qr_path:
            logger.warning('Instagram QR image was not found at static/images/instagram_qr.jpg.')
            return

        with open(qr_path, 'rb') as image_file:
            image = MIMEImage(image_file.read())
        image.add_header('Content-ID', '<instagram_qr>')
        image.add_header('Content-Disposition', 'inline', filename='instagram_qr.jpg')
        message.attach(image)

    @staticmethod
    def _configuration_error():
        email_backend = getattr(settings, 'EMAIL_BACKEND', '')
        if email_backend.lower() != EmailService.SMTP_BACKEND.lower():
            return ''
        if not getattr(settings, 'EMAIL_HOST', ''):
            return 'EMAIL_HOST is missing.'
        return ''


EmailNotificationService = EmailService
