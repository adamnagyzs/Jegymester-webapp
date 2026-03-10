"""
Tests for the SecurityHeadersMiddleware – verifies security-related HTTP headers.
"""
from django.test import TestCase
from django.urls import reverse


class SecurityHeadersMiddlewareTests(TestCase):

    def test_csp_header_present(self):
        resp = self.client.get(reverse('core:home'))
        self.assertIn('Content-Security-Policy', resp)

    def test_permissions_policy_header(self):
        resp = self.client.get(reverse('core:home'))
        self.assertIn('Permissions-Policy', resp)

    def test_x_content_type_options(self):
        resp = self.client.get(reverse('core:home'))
        self.assertEqual(resp['X-Content-Type-Options'], 'nosniff')

    def test_referrer_policy(self):
        resp = self.client.get(reverse('core:home'))
        self.assertIn('Referrer-Policy', resp)
