"""
Serializers for app_linktree
"""
from rest_framework import serializers
from .models import Link, LinkStat, Company, UserProfile

# Import utility functions from app_tinyurl
from app_tinyurl.utils import generate_qrcode_base64


class LinkStatSerializer(serializers.ModelSerializer):
    """Serializer for link statistics."""
    
    class Meta:
        model = LinkStat
        fields = [
            'id', 'created_at', 'via_qrcode', 'device_type',
            'city', 'country'
        ]
        read_only_fields = fields


class LinkSerializer(serializers.ModelSerializer):
    """Serializer for Link CRUD operations."""
    
    qrcode_image = serializers.SerializerMethodField()
    full_link_url = serializers.SerializerMethodField()
    total_clicks = serializers.IntegerField(read_only=True)
    qrcode_clicks = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Link
        fields = [
            'id', 'name', 'url', 'is_active', 'order', 'icon',
            'created_at', 'updated_at',
            'full_link_url', 'qrcode_image',
            'total_clicks', 'qrcode_clicks'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'total_clicks', 'qrcode_clicks']
    
    def get_qrcode_image(self, obj):
        """Generate QR code as base64 PNG for the linktree page."""
        request = self.context.get('request')
        if request:
            # QR code points to the linktree page with qrcode tracking
            full_url = request.build_absolute_uri(f'/links?qrcode=true')
        else:
            full_url = '/links?qrcode=true'
        return generate_qrcode_base64(full_url)
    
    def get_full_link_url(self, obj):
        """Return the full redirect URL for this link."""
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/links/go/{obj.id}')
        return f'/links/go/{obj.id}'


class LinkPublicSerializer(serializers.ModelSerializer):
    """Serializer for public link display (no sensitive data)."""
    
    redirect_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Link
        fields = ['id', 'name', 'url', 'icon', 'redirect_url']
    
    def get_redirect_url(self, obj):
        """Return the tracking redirect URL."""
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/links/go/{obj.id}')
        return f'/links/go/{obj.id}'


class LinkStatsAggregateSerializer(serializers.Serializer):
    """Serializer for aggregated statistics of a single link."""
    
    total_clicks = serializers.IntegerField()
    qrcode_clicks = serializers.IntegerField()
    direct_clicks = serializers.IntegerField()
    
    clicks_by_device = serializers.DictField(
        child=serializers.IntegerField()
    )
    clicks_by_country = serializers.ListField(
        child=serializers.DictField()
    )
    clicks_by_day = serializers.ListField(
        child=serializers.DictField()
    )


class DashboardSerializer(serializers.Serializer):
    """Serializer for dashboard statistics."""
    
    total_links = serializers.IntegerField()
    active_links = serializers.IntegerField()
    total_clicks = serializers.IntegerField()
    qrcode_clicks = serializers.IntegerField()
    
    recent_clicks = LinkStatSerializer(many=True)
    top_links = serializers.ListField(child=serializers.DictField())
    clicks_by_day = serializers.ListField(child=serializers.DictField())


# ============================================================================
# Company and UserProfile Serializers
# ============================================================================

class CompanySerializer(serializers.ModelSerializer):
    """Serializer for Company model."""
    
    class Meta:
        model = Company
        fields = ['id', 'name', 'address', 'siret', 'tva', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class CompanyPublicSerializer(serializers.ModelSerializer):
    """Serializer for public company display."""
    
    class Meta:
        model = Company
        fields = ['name', 'address', 'siret', 'tva']


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile CRUD operations."""
    
    companies = CompanySerializer(many=True, read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'first_name', 'last_name', 'email', 'phone',
            'profile_picture', 'companies', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserProfilePublicSerializer(serializers.ModelSerializer):
    """Serializer for public user profile display."""
    
    companies = CompanyPublicSerializer(many=True, read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ['first_name', 'last_name', 'email', 'phone', 'profile_picture', 'companies']


# ============================================================================
# Linktree Page Serializer (Updated with User Profile)
# ============================================================================

class LinktreePageSerializer(serializers.Serializer):
    """Serializer for the public linktree page with user profile."""
    
    qrcode_image = serializers.CharField()
    user = UserProfilePublicSerializer(allow_null=True)
    links = LinkPublicSerializer(many=True)

