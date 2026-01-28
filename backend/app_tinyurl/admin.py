"""
Django Admin configuration for app_tinyurl
"""
from django.contrib import admin
from .models import Url, UrlStat


class UrlStatInline(admin.TabularInline):
    """Inline display of URL statistics in URL admin."""
    model = UrlStat
    extra = 0
    readonly_fields = ('created_at', 'via_qrcode', 'device_type', 'city', 'country', 'ip_address')
    can_delete = False
    max_num = 50  # Limit displayed stats

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Url)
class UrlAdmin(admin.ModelAdmin):
    """Admin configuration for URL model."""
    list_display = ('short_code', 'long_url_truncated', 'is_active', 'total_clicks', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('short_code', 'long_url')
    readonly_fields = ('id', 'created_at', 'updated_at', 'total_clicks', 'qrcode_clicks')
    ordering = ('-created_at',)
    inlines = [UrlStatInline]
    
    fieldsets = (
        (None, {
            'fields': ('short_code', 'long_url', 'is_active')
        }),
        ('Statistics', {
            'fields': ('total_clicks', 'qrcode_clicks'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def long_url_truncated(self, obj):
        """Display truncated long URL."""
        return obj.long_url[:60] + '...' if len(obj.long_url) > 60 else obj.long_url
    long_url_truncated.short_description = 'Long URL'


@admin.register(UrlStat)
class UrlStatAdmin(admin.ModelAdmin):
    """Admin configuration for URL Statistics model."""
    list_display = ('url', 'created_at', 'via_qrcode', 'device_type', 'country', 'city')
    list_filter = ('via_qrcode', 'device_type', 'country', 'created_at')
    search_fields = ('url__short_code', 'city', 'country', 'ip_address')
    readonly_fields = ('id', 'url', 'created_at', 'via_qrcode', 'device_type', 
                       'city', 'country', 'ip_address', 'user_agent')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
