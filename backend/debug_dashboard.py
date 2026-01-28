import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from rest_framework.test import APIRequestFactory
from app_tinyurl.views import dashboard_stats
from rest_framework.request import Request
from django.contrib.auth import get_user_model

User = get_user_model()
try:
    user = User.objects.first()
    if not user:
        print("No user found! Create one first.")
        sys.exit(1)
except Exception:
    print("DB error getting user")
    user = None

factory = APIRequestFactory()
request = factory.get('/api/tinyurl/dashboard/')
if user:
    request.user = user
# Wrap in DRF Request to handle authentication etc if needed, but dashboard_stats expects a Request
# drf_request = Request(request)

try:
    response = dashboard_stats(request)
    print("Status Code:", response.status_code)
    print("Data:", response.data)
except Exception as e:
    import traceback
    traceback.print_exc()
