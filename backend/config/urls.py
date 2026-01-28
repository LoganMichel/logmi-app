"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings

from app_tinyurl.views import redirect_view
from app_linktree.views import linktree_page
from config.auth_views import login_view, logout_view, me_view, csrf_view

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Authentication endpoints
    path('api/auth/login/', login_view, name='auth-login'),
    path('api/auth/logout/', logout_view, name='auth-logout'),
    path('api/auth/me/', me_view, name='auth-me'),
    path('api/auth/csrf/', csrf_view, name='auth-csrf'),
    
    # API endpoints
    path('api/tinyurl/', include('app_tinyurl.urls')),
    path('api/linktree/', include('app_linktree.urls')),
    
    # Linktree redirect
    path('links/', include('app_linktree.public_urls')),
    
    # Public profile page: /username/links
    path('<str:username>/links/', linktree_page, name='user-linktree'),
    
    # Catch-all for short URL redirects (must be last)
    path('<str:short_code>', redirect_view, name='tinyurl-redirect'),
    
    # Root redirect
    path('', RedirectView.as_view(url=settings.REDIRECT_URL), name='root-redirect'),
]

from django.conf import settings
from django.conf.urls.static import static
from django.urls import re_path
from django.views.static import serve

urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {
        'document_root': settings.MEDIA_ROOT,
    }),
]

if settings.DEBUG:
    # already handled by the above, but kept for static if needed or other debug tools
    pass
