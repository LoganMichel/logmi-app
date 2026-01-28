"""
Utility functions for app_tinyurl
"""
import io
import base64
import random
import string

import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer

from user_agents import parse as parse_user_agent


def generate_short_code(length=6):
    """
    Generate a random short code for URLs.
    Uses alphanumeric characters (excluding ambiguous ones like 0/O, 1/l/I).
    """
    # Exclude ambiguous characters
    chars = ''.join(c for c in string.ascii_letters + string.digits 
                    if c not in 'O0l1I')
    return ''.join(random.choice(chars) for _ in range(length))


def generate_qrcode_base64(url: str) -> str:
    """
    Generate a QR code for the given URL and return as base64 PNG.
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(
        image_factory=StyledPilImage,
        module_drawer=RoundedModuleDrawer()
    )
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    return base64.b64encode(buffer.getvalue()).decode('utf-8')


def get_client_ip(request) -> str:
    """
    Extract the client's IP address from the request.
    Handles X-Forwarded-For header for proxied requests.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_device_type(user_agent_string: str) -> str:
    """
    Determine the device type from the User-Agent string.
    Returns: 'mobile', 'tablet', 'desktop', or 'unknown'
    """
    if not user_agent_string:
        return 'unknown'
    
    try:
        user_agent = parse_user_agent(user_agent_string)
        if user_agent.is_mobile:
            return 'mobile'
        elif user_agent.is_tablet:
            return 'tablet'
        elif user_agent.is_pc:
            return 'desktop'
        else:
            return 'unknown'
    except Exception:
        return 'unknown'


def get_location_from_ip(ip: str) -> dict:
    """
    Get location information from IP address using ip-api.com.
    Returns a dict with 'city' and 'country' keys.
    """
    import requests
    from django.conf import settings
    
    # Skip private/local IPs
    if not ip or ip in ('127.0.0.1', 'localhost', '::1'):
        return {'city': None, 'country': None}
    
    try:
        api_url = getattr(settings, 'IP_API', 'http://ip-api.com/json/')
        response = requests.get(
            f"{api_url.rstrip('/')}/{ip}",
            timeout=2,  # Fast timeout to not slow down redirects
            params={'fields': 'status,country,city'}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                return {
                    'city': data.get('city'),
                    'country': data.get('country'),
                }
    except Exception:
        # Silently fail - geolocation is not critical
        pass
    
    return {'city': None, 'country': None}
