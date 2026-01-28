"""
URL configuration for app_linktree API
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LinkViewSet, 
    UserProfileViewSet, 
    CompanyViewSet, 
    dashboard_stats
)

router = DefaultRouter()
router.register(r'links', LinkViewSet, basename='link')
router.register(r'profile', UserProfileViewSet, basename='profile')
router.register(r'companies', CompanyViewSet, basename='company')

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/', dashboard_stats, name='linktree-dashboard-stats'),
]
