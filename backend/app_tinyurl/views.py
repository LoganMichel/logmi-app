"""
Views for app_tinyurl
"""
from datetime import timedelta

from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.conf import settings

from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Url, UrlStat
from .serializers import (
    UrlSerializer,
    UrlStatSerializer,
    UrlStatsAggregateSerializer,
    DashboardSerializer
)
from .utils import get_client_ip, get_device_type, get_location_from_ip


class UrlViewSet(viewsets.ModelViewSet):
    """
    ViewSet for URL CRUD operations.
    Requires authentication for all operations.
    
    Endpoints:
    - GET /api/tinyurl/urls/ - List all URLs
    - POST /api/tinyurl/urls/ - Create new URL
    - GET /api/tinyurl/urls/{id}/ - Get URL details
    - PUT /api/tinyurl/urls/{id}/ - Update URL
    - DELETE /api/tinyurl/urls/{id}/ - Delete URL
    - GET /api/tinyurl/urls/{id}/stats/ - Get URL statistics
    """
    queryset = Url.objects.all()
    serializer_class = UrlSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Allow filtering by active status."""
        queryset = super().get_queryset()
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        return queryset
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get statistics for a specific URL."""
        url = self.get_object()
        
        # Date range filter
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        stats = url.stats.filter(created_at__gte=start_date)
        
        # Aggregate statistics
        total_clicks = stats.count()
        qrcode_clicks = stats.filter(via_qrcode=True).count()
        
        # Clicks by device
        clicks_by_device = dict(
            stats.values('device_type')
            .annotate(count=Count('id'))
            .values_list('device_type', 'count')
        )
        
        # Clicks by country
        clicks_by_country = list(
            stats.exclude(country__isnull=True)
            .values('country')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )
        
        # Clicks by day
        clicks_by_day = list(
            stats.annotate(date=TruncDate('created_at'))
            .values('date')
            .annotate(count=Count('id'))
            .order_by('date')
        )
        
        data = {
            'total_clicks': total_clicks,
            'qrcode_clicks': qrcode_clicks,
            'direct_clicks': total_clicks - qrcode_clicks,
            'clicks_by_device': clicks_by_device,
            'clicks_by_country': clicks_by_country,
            'clicks_by_day': clicks_by_day,
        }
        
        serializer = UrlStatsAggregateSerializer(data)
        return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """
    Get dashboard statistics.
    Requires authentication.
    
    Endpoint: GET /api/tinyurl/dashboard/
    """
    days = int(request.query_params.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    
    # URL counts
    total_urls = Url.objects.count()
    active_urls = Url.objects.filter(is_active=True).count()
    
    # Click statistics
    recent_stats = UrlStat.objects.filter(created_at__gte=start_date)
    total_clicks = recent_stats.count()
    qrcode_clicks = recent_stats.filter(via_qrcode=True).count()
    
    # Recent clicks
    recent_clicks = UrlStat.objects.select_related('url')[:10]
    
    # Top URLs
    top_urls = list(
        Url.objects.annotate(
            click_count=Count('stats', filter=Q(stats__created_at__gte=start_date))
        )
        .filter(click_count__gt=0)
        .order_by('-click_count')[:10]
        .values('id', 'short_code', 'long_url', 'click_count')
    )
    
    # Clicks by day
    clicks_by_day = list(
        recent_stats.annotate(date=TruncDate('created_at'))
        .values('date')
        .annotate(count=Count('id'))
        .order_by('date')
    )

    # Clicks by city (Top 10)
    clicks_by_city = list(
        recent_stats.exclude(city__isnull=True)
        .values('city', 'country')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    )

    # Clicks by device
    clicks_by_device = list(
        recent_stats.values('device_type')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    
    data = {
        'total_urls': total_urls,
        'active_urls': active_urls,
        'total_clicks': total_clicks,
        'qrcode_clicks': qrcode_clicks,
        'recent_clicks': UrlStatSerializer(recent_clicks, many=True).data,
        'top_urls': top_urls,
        'clicks_by_day': clicks_by_day,
        'clicks_by_city': clicks_by_city,
        'clicks_by_device': clicks_by_device,
    }
    
    return Response(data)


def redirect_view(request, short_code):
    """
    Handle URL redirection with statistics tracking.
    
    - Looks up the short code
    - Records access statistics
    - Redirects to the long URL
    """
    from django.shortcuts import render
    
    # Check if this is a reserved path
    reserved_paths = getattr(settings, 'TINYURL_RESERVED_PATHS', [
        'admin', 'api', 'app', 'static', 'media'
    ])
    if short_code.lower() in [p.lower() for p in reserved_paths]:
        return render(request, '404.html', {'redirect_url': settings.REDIRECT_URL}, status=404)
    
    try:
        # Get the URL
        url = Url.objects.get(short_code=short_code, is_active=True)
    except Url.DoesNotExist:
        return render(request, '404.html', {'redirect_url': settings.REDIRECT_URL}, status=404)
    
    # Track statistics
    via_qrcode = request.GET.get('qrcode', '').lower() == 'true'
    user_agent_string = request.META.get('HTTP_USER_AGENT', '')
    ip_address = get_client_ip(request)
    device_type = get_device_type(user_agent_string)
    location = get_location_from_ip(ip_address)
    
    UrlStat.objects.create(
        url=url,
        via_qrcode=via_qrcode,
        device_type=device_type,
        city=location.get('city'),
        country=location.get('country'),
        ip_address=ip_address,
        user_agent=user_agent_string,
    )
    
    # Redirect to long URL
    return HttpResponseRedirect(url.long_url)
