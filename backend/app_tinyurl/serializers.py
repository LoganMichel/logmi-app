"""
Serializers for app_tinyurl
"""
from django.conf import settings
from rest_framework import serializers
from .models import Url, UrlStat
from .utils import generate_short_code, generate_qrcode_base64


class UrlStatSerializer(serializers.ModelSerializer):
    """Serializer for URL statistics."""
    
    class Meta:
        model = UrlStat
        fields = [
            'id', 'created_at', 'via_qrcode', 'device_type',
            'city', 'country'
        ]
        read_only_fields = fields


class UrlSerializer(serializers.ModelSerializer):
    """Serializer for URL CRUD operations."""
    
    qrcode_image = serializers.SerializerMethodField()
    full_short_url = serializers.SerializerMethodField()
    total_clicks = serializers.IntegerField(read_only=True)
    qrcode_clicks = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Url
        fields = [
            'id', 'short_code', 'long_url', 'is_active',
            'created_at', 'updated_at',
            'full_short_url', 'qrcode_image',
            'total_clicks', 'qrcode_clicks'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'total_clicks', 'qrcode_clicks']
        extra_kwargs = {
            'short_code': {'required': False, 'allow_blank': True}
        }
    
    def get_qrcode_image(self, obj):
        """Generate QR code as base64 PNG."""
        request = self.context.get('request')
        if request:
            full_url = request.build_absolute_uri(f'/{obj.short_code}?qrcode=true')
        else:
            full_url = f'/{obj.short_code}?qrcode=true'
        return generate_qrcode_base64(full_url)
    
    def get_full_short_url(self, obj):
        """Return the full short URL including domain."""
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/{obj.short_code}')
        return f'/{obj.short_code}'
    
    def _ensure_short_code(self, validated_data):
        """Generate short code if not provided."""
        if not validated_data.get('short_code'):
            # Generate unique short code
            for _ in range(10):  # Max attempts
                code = generate_short_code()
                if not Url.objects.filter(short_code=code).exists():
                    validated_data['short_code'] = code
                    break
            else:
                raise serializers.ValidationError(
                    "Could not generate unique short code. Please try again."
                )
        return validated_data

    def create(self, validated_data):
        """Create URL with auto-generated short code if not provided."""
        validated_data = self._ensure_short_code(validated_data)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Update URL with auto-generated short code if cleared."""
        # print(f"DEBUG UPDATE: {validated_data}") # Uncomment for debugging
        validated_data = self._ensure_short_code(validated_data)
        return super().update(instance, validated_data)
    
    def validate_short_code(self, value):
        """Validate short code is not a reserved path."""
        reserved_paths = getattr(settings, 'TINYURL_RESERVED_PATHS', [
            'admin', 'api', 'app', 'static', 'media'
        ])
        if value.lower() in [p.lower() for p in reserved_paths]:
            raise serializers.ValidationError(
                f"'{value}' is a reserved path and cannot be used as a short code."
            )
        return value


class UrlStatsAggregateSerializer(serializers.Serializer):
    """Serializer for aggregated statistics."""
    
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
    
    total_urls = serializers.IntegerField()
    active_urls = serializers.IntegerField()
    total_clicks = serializers.IntegerField()
    qrcode_clicks = serializers.IntegerField()
    
    recent_clicks = UrlStatSerializer(many=True)
    top_urls = serializers.ListField(child=serializers.DictField())
    clicks_by_day = serializers.ListField(child=serializers.DictField())
