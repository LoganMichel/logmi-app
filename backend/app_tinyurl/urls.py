"""
URL configuration for app_tinyurl
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UrlViewSet, dashboard_stats

router = DefaultRouter()
router.register(r'urls', UrlViewSet, basename='url')

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/', dashboard_stats, name='dashboard-stats'),
]
