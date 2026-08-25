import logging
from pathlib import Path

import requests
from django.conf import settings

logger = logging.getLogger('notifications.whatsapp')


class WhatsAppService:
    API_VERSION = 'v20.0'

    @classmethod
    def send_bill_pdf(cls, customer, bill):
        phone = cls._normalize_phone(customer.phone)
        credential_error = cls._credential_error()
        if credential_error:
            logger.warning('WhatsApp PDF skipped for customer_id=%s bill_id=%s: %s', customer.pk, bill.pk, credential_error)
            return {'sent': False, 'response': {'error': credential_error}}
        if not phone:
            return {'sent': False, 'response': {'error': 'Customer phone is invalid.'}}
        if not bill.pdf_file:
            return {'sent': False, 'response': {'error': 'Bill PDF has not been generated.'}}

        upload_result = cls._upload_media(Path(bill.pdf_file.path), 'application/pdf')
        if not upload_result['sent']:
            return upload_result

        media_id = upload_result['response']['id']
        payload = {
            'messaging_product': 'whatsapp',
            'to': phone,
            'type': 'document',
            'document': {
                'id': media_id,
                'filename': Path(bill.pdf_file.name).name,
                'caption': f'Food Lab Bill {bill.bill_number}',
            },
        }
        return cls._post_message(payload, customer.pk, bill.pk, 'PDF')

    @classmethod
    def send_thank_you_message(cls, customer, bill=None):
        phone = cls._normalize_phone(customer.phone)
        credential_error = cls._credential_error()
        if credential_error:
            logger.warning('WhatsApp message skipped for customer_id=%s: %s', customer.pk, credential_error)
            return {'sent': False, 'response': {'error': credential_error}}
        if not phone:
            return {'sent': False, 'response': {'error': 'Customer phone is invalid.'}}

        message = (
            f'Hi {customer.name} \U0001f44b\n\n'
            'Thank you for visiting Food Lab \u2764\ufe0f\n\n'
            'Your bill is attached.\n\n'
            'We hope you enjoyed your meal.\n\n'
            '\u2b50\u2b50\u2b50\u2b50\u2b50\n\n'
            'Please support us with a review.\n\n'
            'Google Review\n\n'
            f'{settings.FOOD_LAB_GOOGLE_REVIEW_URL}\n\n'
            'Follow us\n\n'
            f'{settings.FOOD_LAB_INSTAGRAM_URL}\n\n'
            'Special offers are regularly posted on our Instagram page.\n\n'
            'We look forward to serving you again.\n\n'
            'Regards\n\n'
            'Food Lab'
        )
        payload = {
            'messaging_product': 'whatsapp',
            'to': phone,
            'type': 'text',
            'text': {'preview_url': True, 'body': message},
        }
        return cls._post_message(payload, customer.pk, getattr(bill, 'pk', None), 'thank-you')

    @classmethod
    def _upload_media(cls, file_path, mime_type):
        url = f'https://graph.facebook.com/{cls.API_VERSION}/{settings.WHATSAPP_PHONE_NUMBER_ID}/media'
        headers = {'Authorization': f'Bearer {settings.WHATSAPP_ACCESS_TOKEN}'}
        data = {'messaging_product': 'whatsapp', 'type': mime_type}
        try:
            with open(file_path, 'rb') as upload_file:
                response = requests.post(
                    url,
                    headers=headers,
                    data=data,
                    files={'file': (file_path.name, upload_file, mime_type)},
                    timeout=30,
                )
            response.raise_for_status()
            payload = response.json()
            logger.info('WhatsApp media upload success media_id=%s', payload.get('id'))
            return {'sent': True, 'response': payload}
        except requests.HTTPError as exc:
            error_payload = cls._error_payload(exc.response)
            logger.warning('WhatsApp media upload failed for file=%s: %s', file_path, error_payload['error'])
            return {'sent': False, 'response': error_payload}
        except (OSError, requests.RequestException, ValueError) as exc:
            logger.exception('WhatsApp media upload failure for file=%s', file_path)
            return {'sent': False, 'response': {'error': str(exc)}}

    @classmethod
    def _post_message(cls, payload, customer_id, bill_id, message_type):
        url = f'https://graph.facebook.com/{cls.API_VERSION}/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages'
        headers = {
            'Authorization': f'Bearer {settings.WHATSAPP_ACCESS_TOKEN}',
            'Content-Type': 'application/json',
        }
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            response_payload = response.json()
            logger.info(
                'WhatsApp %s success for customer_id=%s bill_id=%s',
                message_type,
                customer_id,
                bill_id,
            )
            return {'sent': True, 'response': response_payload}
        except requests.HTTPError as exc:
            error_payload = cls._error_payload(exc.response)
            logger.warning(
                'WhatsApp %s failed for customer_id=%s bill_id=%s: %s',
                message_type,
                customer_id,
                bill_id,
                error_payload['error'],
            )
            return {'sent': False, 'response': error_payload}
        except (requests.RequestException, ValueError) as exc:
            logger.exception(
                'WhatsApp %s failure for customer_id=%s bill_id=%s',
                message_type,
                customer_id,
                bill_id,
            )
            return {'sent': False, 'response': {'error': str(exc)}}

    @staticmethod
    def _error_payload(response):
        if response is None:
            return {'error': 'WhatsApp request failed without a response.'}

        try:
            payload = response.json()
        except ValueError:
            payload = {'raw': response.text}

        meta_error = payload.get('error') if isinstance(payload, dict) else None
        if isinstance(meta_error, dict):
            message = meta_error.get('message') or response.reason
            details = meta_error.get('error_data', {}).get('details')
            if details:
                message = f'{message} Details: {details}'
        else:
            message = response.reason or 'WhatsApp request failed.'

        return {
            'error': f'{response.status_code} {message}',
            'meta_response': payload,
        }

    @staticmethod
    def _credential_error():
        if not settings.WHATSAPP_ACCESS_TOKEN:
            return 'WHATSAPP_ACCESS_TOKEN is missing.'
        if not settings.WHATSAPP_PHONE_NUMBER_ID:
            return 'WHATSAPP_PHONE_NUMBER_ID is missing.'
        return ''

    @staticmethod
    def _normalize_phone(phone):
        if not phone:
            return ''
        digits = ''.join(character for character in phone if character.isdigit())
        if len(digits) == 10:
            return f'91{digits}'
        if len(digits) >= 11:
            return digits
        return ''
