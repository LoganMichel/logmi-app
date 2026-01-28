"""
Public URL configuration for app_linktree
These URLs are accessible without authentication.
"""
from django.urls import path
from .views import linktree_page, link_redirect, vcard_download

urlpatterns = [
    path('go/<uuid:link_id>', link_redirect, name='linktree-redirect'),
    path('vcard/<str:username>', vcard_download, name='linktree-vcard'),
]
