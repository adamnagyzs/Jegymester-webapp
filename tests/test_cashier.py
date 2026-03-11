"""
Tests for cashier views: dashboard, verify ticket, sell ticket.
"""
from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from core.models import Movie, CinemaHall, Screening, Ticket

User = get_user_model()


class TestDataMixin:
    """Creates reusable test objects."""

    @classmethod
    def _create_movie(cls, **kwargs):
        defaults = dict(
            title='Teszt Film',
            description='Leírás',
            duration_minutes=120,
            genre='Dráma',
            director='Rendező',
            release_date='2025-01-01',
            is_active=True,
        )
        defaults.update(kwargs)
        return Movie.objects.create(**defaults)

    @classmethod
    def _create_hall(cls, **kwargs):
        defaults = dict(name='Terem 1', rows=10, seats_per_row=15)
        defaults.update(kwargs)
        return CinemaHall.objects.create(**defaults)

    @classmethod
    def _create_screening(cls, movie=None, hall=None, **kwargs):
        defaults = dict(
            movie=movie,
            hall=hall,
            start_time=timezone.now() + timedelta(days=7),
            ticket_price=Decimal('1500.00'),
            is_active=True,
        )
        defaults.update(kwargs)
        return Screening.objects.create(**defaults)

    @classmethod
    def _create_users(cls):
        cls.customer = User.objects.create_user(
            username='customer', password='testpass123',
            role=User.Role.CUSTOMER, email='cust@example.com',
        )
        cls.cashier = User.objects.create_user(
            username='cashier', password='testpass123',
            role=User.Role.CASHIER, email='cash@example.com',
        )
        cls.admin_user = User.objects.create_user(
            username='admin_user', password='testpass123',
            role=User.Role.ADMIN, email='adm@example.com',
            is_staff=True, is_superuser=True,
        )


class CashierDashboardViewTests(TestDataMixin, TestCase):

    def setUp(self):
        self._create_users()

    def test_customer_forbidden(self):
        self.client.login(username='customer', password='testpass123')
        resp = self.client.get(reverse('core:cashier_dashboard'))
        self.assertEqual(resp.status_code, 403)

    def test_cashier_allowed(self):
        self.client.login(username='cashier', password='testpass123')
        resp = self.client.get(reverse('core:cashier_dashboard'))
        self.assertEqual(resp.status_code, 200)

    def test_admin_allowed(self):
        self.client.login(username='admin_user', password='testpass123')
        resp = self.client.get(reverse('core:cashier_dashboard'))
        self.assertEqual(resp.status_code, 200)

    def test_unauthenticated_redirect(self):
        resp = self.client.get(reverse('core:cashier_dashboard'))
        self.assertEqual(resp.status_code, 302)


class VerifyTicketViewTests(TestDataMixin, TestCase):

    def setUp(self):
        self._create_users()
        self.movie = self._create_movie()
        self.hall = self._create_hall()
        self.screening = self._create_screening(movie=self.movie, hall=self.hall)
        self.ticket = Ticket.objects.create(
            screening=self.screening, seat_row=1, seat_number=1,
            guest_email='g@g.com',
        )

    def test_get_verify_page(self):
        self.client.login(username='cashier', password='testpass123')
        resp = self.client.get(
            reverse('core:verify_ticket', args=[self.ticket.ticket_code])
        )
        self.assertEqual(resp.status_code, 200)

    def test_verify_ticket_post(self):
        self.client.login(username='cashier', password='testpass123')
        resp = self.client.post(
            reverse('core:verify_ticket', args=[self.ticket.ticket_code])
        )
        self.assertEqual(resp.status_code, 302)
        self.ticket.refresh_from_db()
        self.assertTrue(self.ticket.is_verified)
        self.assertEqual(self.ticket.verified_by, self.cashier)

    def test_verify_cancelled_ticket(self):
        self.ticket.is_cancelled = True
        self.ticket.save()
        self.client.login(username='cashier', password='testpass123')
        resp = self.client.post(
            reverse('core:verify_ticket', args=[self.ticket.ticket_code])
        )
        self.ticket.refresh_from_db()
        self.assertFalse(self.ticket.is_verified)

    def test_verify_already_verified(self):
        self.ticket.is_verified = True
        self.ticket.save()
        self.client.login(username='cashier', password='testpass123')
        resp = self.client.post(
            reverse('core:verify_ticket', args=[self.ticket.ticket_code])
        )
        self.assertEqual(resp.status_code, 302)

    def test_customer_cannot_verify(self):
        self.client.login(username='customer', password='testpass123')
        resp = self.client.get(
            reverse('core:verify_ticket', args=[self.ticket.ticket_code])
        )
        self.assertEqual(resp.status_code, 403)


class CashierSellTicketViewTests(TestDataMixin, TestCase):

    def setUp(self):
        self._create_users()
        self.movie = self._create_movie()
        self.hall = self._create_hall(rows=5, seats_per_row=10)
        self.screening = self._create_screening(movie=self.movie, hall=self.hall)

    def test_get_sell_page(self):
        self.client.login(username='cashier', password='testpass123')
        resp = self.client.get(
            reverse('core:cashier_sell_ticket', args=[self.screening.pk])
        )
        self.assertEqual(resp.status_code, 200)

    def test_sell_ticket(self):
        self.client.login(username='cashier', password='testpass123')
        resp = self.client.post(
            reverse('core:cashier_sell_ticket', args=[self.screening.pk]),
            {
                'seat_rows': ['1'], 'seat_numbers': ['1'],
                'guest_email': 'buyer@test.com',
                'guest_phone': '+36301234567',
            },
        )
        self.assertEqual(resp.status_code, 302)
        t = Ticket.objects.get(screening=self.screening)
        self.assertEqual(t.sold_by, self.cashier)
        self.assertEqual(t.guest_email, 'buyer@test.com')

    def test_customer_cannot_sell(self):
        self.client.login(username='customer', password='testpass123')
        resp = self.client.get(
            reverse('core:cashier_sell_ticket', args=[self.screening.pk])
        )
        self.assertEqual(resp.status_code, 403)

    def test_sell_multiple_seats(self):
        self.client.login(username='cashier', password='testpass123')
        resp = self.client.post(
            reverse('core:cashier_sell_ticket', args=[self.screening.pk]),
            {'seat_rows': ['1', '2'], 'seat_numbers': ['1', '1']},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Ticket.objects.filter(screening=self.screening).count(), 2)

    def test_sell_past_screening_fails(self):
        past = self._create_screening(
            movie=self.movie, hall=self.hall,
            start_time=timezone.now() - timedelta(hours=1),
        )
        self.client.login(username='cashier', password='testpass123')
        resp = self.client.post(
            reverse('core:cashier_sell_ticket', args=[past.pk]),
            {'seat_rows': ['1'], 'seat_numbers': ['1']},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Ticket.objects.count(), 0)
