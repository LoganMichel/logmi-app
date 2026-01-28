"""
Views for app_linktree
"""
from datetime import timedelta

from django.db.models import Count
from django.db.models.functions import TruncDate
from django.http import HttpResponseRedirect, Http404, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.conf import settings

from .models import Link, LinkStat, UserProfile, Company
from .serializers import (
    LinkSerializer,
    LinkStatSerializer,
    LinkStatsAggregateSerializer,
    DashboardSerializer,
    LinkPublicSerializer,
    LinktreePageSerializer,
    UserProfilePublicSerializer,
    UserProfileSerializer,
    CompanySerializer
)

# Import utility functions from app_tinyurl
from app_tinyurl.utils import (
    get_client_ip, 
    get_device_type, 
    get_location_from_ip,
    generate_qrcode_base64
)


class LinkViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Link CRUD operations.
    Requires authentication for all operations.
    
    Endpoints:
    - GET /api/linktree/links/ - List all links
    - POST /api/linktree/links/ - Create new link
    - GET /api/linktree/links/{id}/ - Get link details
    - PUT /api/linktree/links/{id}/ - Update link
    - DELETE /api/linktree/links/{id}/ - Delete link
    - GET /api/linktree/links/{id}/stats/ - Get link statistics
    """
    queryset = Link.objects.all()
    serializer_class = LinkSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter links by current user and active status."""
        queryset = Link.objects.filter(user=self.request.user)
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        return queryset

    def perform_create(self, serializer):
        """Associate link with current user."""
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get statistics for a specific link."""
        link = self.get_object()
        
        # Date range filter
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        stats = link.stats.filter(created_at__gte=start_date)
        
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
        
        serializer = LinkStatsAggregateSerializer(data)
        return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """
    Get dashboard statistics.
    Requires authentication.
    
    Endpoint: GET /api/linktree/dashboard/
    """
    days = int(request.query_params.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    
    # Link counts
    total_links = Link.objects.count()
    active_links = Link.objects.filter(is_active=True).count()
    
    # Click statistics
    recent_stats = LinkStat.objects.filter(created_at__gte=start_date)
    total_clicks = recent_stats.count()
    qrcode_clicks = recent_stats.filter(via_qrcode=True).count()
    
    # Recent clicks
    recent_clicks = LinkStat.objects.select_related('link')[:10]
    
    # Top links
    top_links = list(
        Link.objects.annotate(click_count=Count('stats'))
        .filter(stats__created_at__gte=start_date)
        .order_by('-click_count')[:10]
        .values('id', 'name', 'url', 'click_count')
    )
    
    # Clicks by day
    clicks_by_day = list(
        recent_stats.annotate(date=TruncDate('created_at'))
        .values('date')
        .annotate(count=Count('id'))
        .order_by('date')
    )
    
    data = {
        'total_links': total_links,
        'active_links': active_links,
        'total_clicks': total_clicks,
        'qrcode_clicks': qrcode_clicks,
        'recent_clicks': LinkStatSerializer(recent_clicks, many=True).data,
        'top_links': top_links,
        'clicks_by_day': clicks_by_day,
    }
    
    return Response(data)


# ============================================================================
# PUBLIC VIEWS (No authentication required)
# ============================================================================

from django.contrib.auth.models import User

def linktree_page(request, username):
    """
    Public page displaying all active links for a specific user.
    Renders an HTML template.
    """
    from django.shortcuts import render
    
    try:
        # Get user by username
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return render(request, '404.html', {'redirect_url': settings.REDIRECT_URL}, status=404)
    
    # Get all active links for this user ordered by order field
    links = Link.objects.filter(user=user, is_active=True).order_by('order', '-created_at')
    
    # Get user profile
    user_profile = UserProfile.objects.filter(user=user).first()
    
    context = {
        'links': links,
        'user_profile': user_profile,
        'user': user,
    }
    
    return render(request, 'linktree/public_page.html', context)


def vcard_download(request, username):
    """
    Generate and download a vCard (.vcf) file for the user's profile.
    
    Endpoint: GET /{username}/links/vcard
    """
    from django.http import HttpResponse
    
    try:
        # Get user by username
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        from django.shortcuts import render
        return render(request, '404.html', {'redirect_url': settings.REDIRECT_URL}, status=404)
    
    # Get user profile
    user_profile = UserProfile.objects.filter(user=user).first()
    
    if not user_profile:
        # If user exists but has no profile, maybe valid but empty vCard, or 404? 
        # Using 404 for consistency if profile is required for vCard
        from django.shortcuts import render
        return render(request, '404.html', {'redirect_url': settings.REDIRECT_URL}, status=404)
    
    # ... (rest of vCard generation logic) ...
    # Build vCard content (vCard 3.0 format)
    vcard_lines = [
        "BEGIN:VCARD",
        "VERSION:3.0",
    ]
    
    # Name
    first_name = user_profile.first_name or ""
    last_name = user_profile.last_name or ""
    if first_name or last_name:
        vcard_lines.append(f"N:{last_name};{first_name};;;")
        vcard_lines.append(f"FN:{first_name} {last_name}".strip())
    else:
        vcard_lines.append(f"FN:{user.username}")
    
    # Email
    if user_profile.email:
        vcard_lines.append(f"EMAIL;TYPE=INTERNET:{user_profile.email}")
    
    # Phone
    if user_profile.phone:
        vcard_lines.append(f"TEL;TYPE=CELL:{user_profile.phone}")
    
    # Companies
    companies = user_profile.companies.all()
    if companies:
        company = companies.first()  # Use first company for ORG
        vcard_lines.append(f"ORG:{company.name}")
        if company.address:
            # Replace newlines with semicolons for vCard format
            address = company.address.replace('\n', ';').replace('\r', '')
            vcard_lines.append(f"ADR;TYPE=WORK:;;{address};;;;")
    
    vcard_lines.append("END:VCARD")
    
    # Join with CRLF as per vCard spec
    vcard_content = "\r\n".join(vcard_lines)
    
    # Create response
    response = HttpResponse(vcard_content, content_type='text/vcard; charset=utf-8')
    filename = f"{first_name}_{last_name}".strip('_') or username
    response['Content-Disposition'] = f'attachment; filename="{filename}.vcf"'
    
    return response


def link_redirect(request, link_id):
    """
    Handle link redirection with statistics tracking.
    
    - Looks up the link by ID
    - Records access statistics
    - Redirects to the external URL
    
    Endpoint: GET /links/go/{link_id}
    
    Query params:
    - qrcode: If 'true', marks this click as coming from QR code
    """
    from django.shortcuts import render
    
    try:
        # Get the link
        link = Link.objects.get(id=link_id, is_active=True)
    except (Link.DoesNotExist, Exception): # Catch invalid UUID or not found
        return render(request, '404.html', {'redirect_url': settings.REDIRECT_URL}, status=404)
    
    # Track statistics
    via_qrcode = request.GET.get('qrcode', '').lower() == 'true'
    user_agent_string = request.META.get('HTTP_USER_AGENT', '')
    ip_address = get_client_ip(request)
    device_type = get_device_type(user_agent_string)
    location = get_location_from_ip(ip_address)
    
    LinkStat.objects.create(
        link=link,
        via_qrcode=via_qrcode,
        device_type=device_type,
        city=location.get('city'),
        country=location.get('country'),
        ip_address=ip_address,
        user_agent=user_agent_string,
    )
    
    # Redirect to external URL
    return HttpResponseRedirect(link.url)


# ============================================================================
# USER PROFILE AND COMPANY VIEWS
# ============================================================================

class UserProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for UserProfile.
    
    Endpoints:
    - GET /api/linktree/profile/ - Get current user's profile
    - PATCH /api/linktree/profile/ - Partial update profile
    """
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    
    def get_queryset(self):
        """Only return the current user's profile."""
        return UserProfile.objects.filter(user=self.request.user)
    
    def get_object(self):
        """Get or create the current user's profile."""
        profile, _ = UserProfile.objects.get_or_create(user=self.request.user)
        return profile
    
    def list(self, request, *args, **kwargs):
        """Return the current user's profile as a single object."""
        profile = self.get_object()
        serializer = self.get_serializer(profile)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put', 'patch'], url_path='')
    def update_profile(self, request):
        """Update the current user's profile."""
        profile = self.get_object()
        serializer = self.get_serializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def add_company(self, request):
        """Add an existing company to the user's profile."""
        company_id = request.data.get('company_id')
        if not company_id:
            return Response(
                {'error': 'company_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            company = Company.objects.get(id=company_id)
        except Company.DoesNotExist:
            return Response(
                {'error': 'Company not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        profile = self.get_object()
        profile.companies.add(company)
        serializer = self.get_serializer(profile)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def remove_company(self, request):
        """Remove a company from the user's profile."""
        company_id = request.data.get('company_id')
        if not company_id:
            return Response(
                {'error': 'company_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            company = Company.objects.get(id=company_id)
        except Company.DoesNotExist:
            return Response(
                {'error': 'Company not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        profile = self.get_object()
        profile.companies.remove(company)
        serializer = self.get_serializer(profile)
        return Response(serializer.data)


class CompanyViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Company CRUD operations.
    
    Endpoints:
    - GET /api/linktree/companies/ - List all companies
    - POST /api/linktree/companies/ - Create new company
    - GET /api/linktree/companies/{id}/ - Get company details
    - PUT /api/linktree/companies/{id}/ - Update company
    - DELETE /api/linktree/companies/{id}/ - Delete company
    """
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter companies by current user's profile if requested."""
        queryset = super().get_queryset()
        mine_only = self.request.query_params.get('mine', '').lower() == 'true'
        if mine_only:
            profile = UserProfile.objects.filter(user=self.request.user).first()
            if profile:
                queryset = profile.companies.all()
            else:
                queryset = Company.objects.none()
        return queryset
    
    def perform_create(self, serializer):
        """Link the created company to the current user's profile."""
        company = serializer.save()
        profile, _ = UserProfile.objects.get_or_create(user=self.request.user)
        profile.companies.add(company)
