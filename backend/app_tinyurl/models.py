"""
Models for app_tinyurl - URL Shortener with Statistics
"""
import uuid
from django.db import models


class Url(models.Model):
    """
    Represents a shortened URL mapping.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    short_code = models.CharField(max_length=50, unique=True, db_index=True)
    long_url = models.URLField(max_length=2048)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'URL'
        verbose_name_plural = 'URLs'

    def __str__(self):
        return f"{self.short_code} -> {self.long_url[:50]}..."

    @property
    def total_clicks(self):
        return self.stats.count()

    @property
    def qrcode_clicks(self):
        return self.stats.filter(via_qrcode=True).count()


class UrlStat(models.Model):
    """
    Represents a single access/click on a shortened URL.
    Tracks device type, location, and QR code usage.
    """
    DEVICE_TYPES = [
        ('mobile', 'Mobile'),
        ('tablet', 'Tablet'),
        ('desktop', 'Desktop'),
        ('unknown', 'Unknown'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    url = models.ForeignKey(
        Url,
        on_delete=models.CASCADE,
        related_name='stats'
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    via_qrcode = models.BooleanField(default=False)
    device_type = models.CharField(
        max_length=20,
        choices=DEVICE_TYPES,
        default='unknown'
    )
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'URL Statistic'
        verbose_name_plural = 'URL Statistics'

    def __str__(self):
        return f"{self.url.short_code} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
