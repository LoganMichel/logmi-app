from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase

from app_tinyurl.models import Url, UrlStat
from app_tinyurl.views import redirect_view
from .models import Link, LinkStat
from .serializers import LinkSerializer
from .views import link_redirect, linktree_page


class QrTrackingTests(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='diagnostic')
        self.link = Link.objects.create(
            name='Test', user=self.user, url='https://example.com/destination'
        )

    def test_generated_qr_targets_owner_page(self) -> None:
        with patch('app_linktree.serializers.generate_qrcode_base64', return_value='image') as generate:
            LinkSerializer(self.link, context={'request': self.factory.get('/')}).data
        generate.assert_called_once_with('http://testserver/diagnostic/links/?qrcode=true')

    def test_unowned_link_qr_targets_tracked_link(self) -> None:
        self.link.user = None
        self.link.save()
        with patch('app_linktree.serializers.generate_qrcode_base64', return_value='image') as generate:
            LinkSerializer(self.link).data
        generate.assert_called_once_with(f'/links/go/{self.link.id}?qrcode=true')

    def test_qr_page_propagates_marker_to_outgoing_link(self) -> None:
        response = linktree_page(self.factory.get('/diagnostic/links/?qrcode=TRUE'), 'diagnostic')
        self.assertContains(response, f'href="/links/go/{self.link.id}?qrcode=true"')

    def test_direct_page_does_not_add_marker(self) -> None:
        response = linktree_page(self.factory.get('/diagnostic/links/'), 'diagnostic')
        self.assertContains(response, f'href="/links/go/{self.link.id}"')
        self.assertNotContains(response, '?qrcode=true')

    @patch('app_linktree.views.get_location_from_ip', return_value={})
    @patch('app_tinyurl.views.get_location_from_ip', return_value={})
    def test_legacy_qr_redirect_page_and_click_keep_attribution(self, _tiny_geo: object, _link_geo: object) -> None:
        Url.objects.create(short_code='links', long_url='http://testserver/diagnostic/links/')
        response = redirect_view(self.factory.get('/links?qrcode=true'), 'links')
        self.assertEqual(response['Location'], 'http://testserver/diagnostic/links/?qrcode=true')
        self.assertTrue(UrlStat.objects.get().via_qrcode)
        page = linktree_page(self.factory.get(response['Location']), 'diagnostic')
        self.assertContains(page, f'href="/links/go/{self.link.id}?qrcode=true"')
        result = link_redirect(self.factory.get(f'/links/go/{self.link.id}?qrcode=true'), self.link.id)
        self.assertEqual(result['Location'], self.link.url)
        self.assertTrue(LinkStat.objects.get().via_qrcode)
