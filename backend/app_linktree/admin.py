"""
Django Admin configuration for app_linktree
"""
from django.contrib import admin
from .models import Link, LinkStat, Company, UserProfile


class LinkStatInline(admin.TabularInline):
    """Inline display of link statistics in Link admin."""
    model = LinkStat
    extra = 0
    readonly_fields = ('created_at', 'via_qrcode', 'device_type', 'city', 'country', 'ip_address')
    can_delete = False
    max_num = 50  # Limit displayed stats

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Link)
class LinkAdmin(admin.ModelAdmin):
    """Admin configuration for Link model."""
    list_display = ('name', 'url_truncated', 'is_active', 'order', 'total_clicks', 'created_at')
    list_filter = ('is_active', 'created_at')
    list_editable = ('order', 'is_active')
    search_fields = ('name', 'url')
    readonly_fields = ('id', 'created_at', 'updated_at', 'total_clicks', 'qrcode_clicks')
    ordering = ('order', '-created_at')
    inlines = [LinkStatInline]
    
    fieldsets = (
        (None, {
            'fields': ('name', 'url', 'icon', 'order', 'is_active')
        }),
        ('Statistiques', {
            'fields': ('total_clicks', 'qrcode_clicks'),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def url_truncated(self, obj):
        """Display truncated URL."""
        return obj.url[:60] + '...' if len(obj.url) > 60 else obj.url
    url_truncated.short_description = 'URL'


@admin.register(LinkStat)
class LinkStatAdmin(admin.ModelAdmin):
    """Admin configuration for Link Statistics model."""
    list_display = ('link', 'created_at', 'via_qrcode', 'device_type', 'country', 'city')
    list_filter = ('via_qrcode', 'device_type', 'country', 'created_at')
    search_fields = ('link__name', 'city', 'country', 'ip_address')
    readonly_fields = ('id', 'link', 'created_at', 'via_qrcode', 'device_type', 
                       'city', 'country', 'ip_address', 'user_agent')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


# ============================================================================
# Company Admin
# ============================================================================

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    """Admin configuration for Company model."""
    list_display = ('name', 'siret', 'tva', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'siret', 'tva', 'address')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('name',)
    
    fieldsets = (
        (None, {
            'fields': ('name', 'address')
        }),
        ('Informations légales', {
            'fields': ('siret', 'tva')
        }),
        ('Métadonnées', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# ============================================================================
# UserProfile Admin
# ============================================================================

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin configuration for UserProfile model (singleton)."""
    list_display = ('full_name', 'email', 'phone', 'company_count', 'created_at')
    search_fields = ('first_name', 'last_name', 'email', 'phone')
    readonly_fields = ('id', 'created_at', 'updated_at')
    filter_horizontal = ('companies',)
    
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('first_name', 'last_name', 'email', 'phone')
        }),
        ('Sociétés', {
            'fields': ('companies',)
        }),
        ('Métadonnées', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def full_name(self, obj):
        """Display full name."""
        name = f"{obj.first_name} {obj.last_name}".strip()
        return name if name else f"Profil {obj.id}"
    full_name.short_description = 'Nom complet'

    def company_count(self, obj):
        """Display number of companies."""
        return obj.companies.count()
    company_count.short_description = 'Sociétés'

