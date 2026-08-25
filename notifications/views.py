import logging
import json

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger('notifications.whatsapp')


@csrf_exempt
def whatsapp_webhook(request):
    if request.method == 'GET':
        mode = request.GET.get('hub.mode')
        verify_token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')

        if (
            mode == 'subscribe'
            and verify_token
            and verify_token == settings.WHATSAPP_VERIFY_TOKEN
        ):
            logger.info('WhatsApp webhook verification successful.')
            return HttpResponse(challenge, status=200)

        logger.warning('WhatsApp webhook verification failed.')
        return HttpResponse('Forbidden', status=403)

    if request.method == 'POST':
        try:
            payload = json.loads(request.body.decode('utf-8') or '{}')
        except json.JSONDecodeError:
            logger.warning('WhatsApp webhook event received with invalid JSON.')
            return JsonResponse({'status': 'invalid_json'}, status=400)

        logger.info('WhatsApp webhook event received: %s', _summarize_webhook_payload(payload))
        return JsonResponse({'status': 'ok'}, status=200)

    return HttpResponse('Method Not Allowed', status=405)


def _summarize_webhook_payload(payload):
    entries = payload.get('entry', []) if isinstance(payload, dict) else []
    summaries = []
    for entry in entries:
        for change in entry.get('changes', []):
            value = change.get('value', {})
            statuses = value.get('statuses', [])
            messages = value.get('messages', [])
            if statuses:
                summaries.extend(
                    f"status={status.get('status')} id={status.get('id')} recipient={status.get('recipient_id')}"
                    for status in statuses
                )
            if messages:
                summaries.extend(
                    f"message type={message.get('type')} from={message.get('from')} id={message.get('id')}"
                    for message in messages
                )
    return '; '.join(summaries) or 'no message/status summary'
