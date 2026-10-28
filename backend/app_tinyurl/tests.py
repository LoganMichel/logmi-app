from unittest.mock import patch

from django.test import RequestFactory, TestCase

from .models import Url, UrlStat
from .views import redirect_view


class QrRedirectTests(TestCase):
    @patch('app_tinyurl.views.get_location_from_ip', return_value={})
    def test_internal_redirect_preserves_qr_and_existing_query(self, _geo: object) -> None:
        destinations: list[tuple[str, str]] = [
            ('http://testserver/logan/links/?source=card#contact',
             'http://testserver/logan/links/?source=card&qrcode=true#contact'),
            ('/logan/links/?qrcode=false', '/logan/links/?qrcode=true'),
            ('https://example.com/page?source=card', 'https://example.com/page?source=card'),
            ('https://testserver.evil.example/page', 'https://testserver.evil.example/page'),
            ('//example.com/page', '//example.com/page'),
        ]
        for index, (destination, expected) in enumerate(destinations):
            with self.subTest(destination=destination):
                code: str = f'test{index}'
                Url.objects.create(short_code=code, long_url=destination)
                response = redirect_view(RequestFactory().get(f'/{code}?qrcode=true'), code)
                self.assertEqual(response['Location'], expected)
                self.assertTrue(UrlStat.objects.get(url__short_code=code).via_qrcode)

    @patch('app_tinyurl.views.get_location_from_ip', return_value={})
    def test_direct_click_does_not_change_destination(self, _geo: object) -> None:
        destination: str = 'http://testserver/logan/links/?source=card#contact'
        Url.objects.create(short_code='test', long_url=destination)
        response = redirect_view(RequestFactory().get('/test'), 'test')
        self.assertEqual(response['Location'], destination)
        self.assertFalse(UrlStat.objects.get().via_qrcode)
