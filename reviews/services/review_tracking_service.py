from reviews.models import ReviewLinkClick


class ReviewTrackingService:
    @staticmethod
    def count_clicks():
        return ReviewLinkClick.objects.count()

    @staticmethod
    def track_click(request, customer=None, source='dashboard'):
        forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        ip_address = forwarded_for.split(',')[0].strip() if forwarded_for else request.META.get('REMOTE_ADDR')
        return ReviewLinkClick.objects.create(
            customer=customer,
            source=source,
            ip_address=ip_address or None,
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
        )
