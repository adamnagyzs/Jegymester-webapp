"""
Tests for URL routing – every named URL resolves to the expected path.
"""
from django.test import TestCase
from django.urls import reverse


class URLRoutingTests(TestCase):
    """Verify all URL names resolve correctly."""

    def test_home_url(self):
        self.assertEqual(reverse('core:home'), '/')

    def test_movie_list_url(self):
        self.assertEqual(reverse('core:movie_list'), '/movies/')

    def test_movie_detail_url(self):
        self.assertEqual(reverse('core:movie_detail', args=[1]), '/movies/1/')

    def test_screening_list_url(self):
        self.assertEqual(reverse('core:screening_list'), '/screenings/')

    def test_buy_ticket_url(self):
        self.assertEqual(reverse('core:buy_ticket', args=[1]), '/screenings/1/buy/')

    def test_my_tickets_url(self):
        self.assertEqual(reverse('core:my_tickets'), '/my-tickets/')

    def test_ticket_lookup_url(self):
        self.assertEqual(reverse('core:ticket_lookup'), '/ticket-lookup/')

    def test_cashier_dashboard_url(self):
        self.assertEqual(reverse('core:cashier_dashboard'), '/cashier/')

    def test_admin_dashboard_url(self):
        self.assertEqual(reverse('core:admin_dashboard'), '/management/')

    def test_admin_movie_add_url(self):
        self.assertEqual(reverse('core:admin_movie_add'), '/management/movies/add/')

    def test_admin_screening_add_url(self):
        self.assertEqual(
            reverse('core:admin_screening_add'), '/management/screenings/add/'
        )
