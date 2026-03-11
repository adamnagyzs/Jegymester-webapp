"""
Tests for public views, ticket purchase, ticket management, and email.
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


# ═════════════════════════════════════════════════
#  PUBLIC VIEW TESTS
# ═════════════════════════════════════════════════

class HomeViewTests(TestDataMixin, TestCase):

    def test_home_status_200(self):
        resp = self.client.get(reverse('core:home'))
        self.assertEqual(resp.status_code, 200)

    def test_home_shows_movies(self):
        m = self._create_movie(title='Visible Film')
        resp = self.client.get(reverse('core:home'))
        self.assertContains(resp, 'Visible Film')

    def test_home_hides_inactive_movies(self):
        self._create_movie(title='Hidden', is_active=False)
        resp = self.client.get(reverse('core:home'))
        self.assertNotContains(resp, 'Hidden')


class MovieListViewTests(TestDataMixin, TestCase):

    def test_status_200(self):
        resp = self.client.get(reverse('core:movie_list'))
        self.assertEqual(resp.status_code, 200)

    def test_shows_active_movies(self):
        self._create_movie(title='Active Movie')
        self._create_movie(title='Inactive', is_active=False)
        resp = self.client.get(reverse('core:movie_list'))
        self.assertContains(resp, 'Active Movie')
        self.assertNotContains(resp, 'Inactive')


class MovieDetailViewTests(TestDataMixin, TestCase):

    def test_status_200(self):
        m = self._create_movie()
        resp = self.client.get(reverse('core:movie_detail', args=[m.pk]))
        self.assertEqual(resp.status_code, 200)

    def test_inactive_movie_404(self):
        m = self._create_movie(is_active=False)
        resp = self.client.get(reverse('core:movie_detail', args=[m.pk]))
        self.assertEqual(resp.status_code, 404)

    def test_shows_screenings(self):
        m = self._create_movie()
        h = self._create_hall()
        self._create_screening(movie=m, hall=h)
        resp = self.client.get(reverse('core:movie_detail', args=[m.pk]))
        self.assertEqual(resp.status_code, 200)


class ScreeningListViewTests(TestDataMixin, TestCase):

    def test_status_200(self):
        resp = self.client.get(reverse('core:screening_list'))
        self.assertEqual(resp.status_code, 200)

    def test_date_filter(self):
        m = self._create_movie()
        h = self._create_hall()
        future = timezone.now() + timedelta(days=5)
        self._create_screening(movie=m, hall=h, start_time=future)
        date_str = future.strftime('%Y-%m-%d')
        resp = self.client.get(reverse('core:screening_list'), {'date': date_str})
        self.assertEqual(resp.status_code, 200)


class ScreeningDetailViewTests(TestDataMixin, TestCase):

    def test_status_200(self):
        m = self._create_movie()
        h = self._create_hall()
        s = self._create_screening(movie=m, hall=h)
        resp = self.client.get(reverse('core:screening_detail', args=[s.pk]))
        self.assertEqual(resp.status_code, 200)

    def test_inactive_screening_404(self):
        m = self._create_movie()
        h = self._create_hall()
        s = self._create_screening(movie=m, hall=h, is_active=False)
        resp = self.client.get(reverse('core:screening_detail', args=[s.pk]))
        self.assertEqual(resp.status_code, 404)

    def test_sold_seats_in_context(self):
        m = self._create_movie()
        h = self._create_hall()
        s = self._create_screening(movie=m, hall=h)
        Ticket.objects.create(
            screening=s, seat_row=1, seat_number=1, guest_email='a@b.com',
        )
        resp = self.client.get(reverse('core:screening_detail', args=[s.pk]))
        self.assertIn((1, 1), resp.context['sold_seats'])


class TicketLookupViewTests(TestDataMixin, TestCase):

    def setUp(self):
        self.movie = self._create_movie()
        self.hall = self._create_hall()
        self.screening = self._create_screening(movie=self.movie, hall=self.hall)

    def test_get_status_200(self):
        resp = self.client.get(reverse('core:ticket_lookup'))
        self.assertEqual(resp.status_code, 200)

    def test_lookup_existing_ticket(self):
        t = Ticket.objects.create(
            screening=self.screening, seat_row=1, seat_number=1,
            guest_email='g@g.com',
        )
        resp = self.client.get(
            reverse('core:ticket_lookup'), {'ticket_code': t.ticket_code}
        )
        self.assertContains(resp, t.ticket_code)

    def test_lookup_nonexistent_ticket(self):
        resp = self.client.get(
            reverse('core:ticket_lookup'), {'ticket_code': 'ZZZZZZZZZZ'}
        )
        self.assertEqual(resp.status_code, 200)


# ═════════════════════════════════════════════════
#  TICKET PURCHASE TESTS
# ═════════════════════════════════════════════════

class BuyTicketViewTests(TestDataMixin, TestCase):

    def setUp(self):
        self._create_users()
        self.movie = self._create_movie()
        self.hall = self._create_hall(rows=5, seats_per_row=10)
        self.screening = self._create_screening(movie=self.movie, hall=self.hall)

    def test_get_buy_page(self):
        resp = self.client.get(
            reverse('core:buy_ticket', args=[self.screening.pk])
        )
        self.assertEqual(resp.status_code, 200)

    def test_buy_ticket_authenticated(self):
        self.client.login(username='customer', password='testpass123')
        resp = self.client.post(
            reverse('core:buy_ticket', args=[self.screening.pk]),
            {'seat_rows': ['1'], 'seat_numbers': ['1']},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Ticket.objects.filter(user=self.customer).count(), 1)

    def test_buy_ticket_guest(self):
        resp = self.client.post(
            reverse('core:buy_ticket', args=[self.screening.pk]),
            {
                'seat_rows': ['2'], 'seat_numbers': ['3'],
                'guest_email': 'guest@example.com',
                'guest_phone': '+36301234567',
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Ticket.objects.filter(guest_email='guest@example.com').count(), 1)

    def test_buy_multiple_tickets(self):
        self.client.login(username='customer', password='testpass123')
        resp = self.client.post(
            reverse('core:buy_ticket', args=[self.screening.pk]),
            {'seat_rows': ['1', '1', '2'], 'seat_numbers': ['1', '2', '1']},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Ticket.objects.filter(user=self.customer).count(), 3)

    def test_buy_already_taken_seat(self):
        Ticket.objects.create(
            screening=self.screening, seat_row=1, seat_number=1,
            guest_email='a@a.com',
        )
        self.client.login(username='customer', password='testpass123')
        resp = self.client.post(
            reverse('core:buy_ticket', args=[self.screening.pk]),
            {'seat_rows': ['1'], 'seat_numbers': ['1']},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            Ticket.objects.filter(screening=self.screening, is_cancelled=False).count(), 1
        )

    def test_buy_past_screening_redirects(self):
        past = self._create_screening(
            movie=self.movie, hall=self.hall,
            start_time=timezone.now() - timedelta(hours=1),
        )
        resp = self.client.get(reverse('core:buy_ticket', args=[past.pk]))
        self.assertEqual(resp.status_code, 302)

    def test_buy_no_seats_selected(self):
        self.client.login(username='customer', password='testpass123')
        resp = self.client.post(
            reverse('core:buy_ticket', args=[self.screening.pk]),
            {},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Ticket.objects.count(), 0)

    def test_buy_duplicate_seat_in_request(self):
        self.client.login(username='customer', password='testpass123')
        resp = self.client.post(
            reverse('core:buy_ticket', args=[self.screening.pk]),
            {'seat_rows': ['1', '1'], 'seat_numbers': ['1', '1']},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Ticket.objects.count(), 0)

    def test_buy_more_than_10_tickets(self):
        self.client.login(username='customer', password='testpass123')
        rows = [str(i) for i in range(1, 12)]
        seats = ['1'] * 11
        resp = self.client.post(
            reverse('core:buy_ticket', args=[self.screening.pk]),
            {'seat_rows': rows, 'seat_numbers': seats},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Ticket.objects.count(), 0)

    def test_buy_invalid_seat(self):
        self.client.login(username='customer', password='testpass123')
        resp = self.client.post(
            reverse('core:buy_ticket', args=[self.screening.pk]),
            {'seat_rows': ['99'], 'seat_numbers': ['1']},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Ticket.objects.count(), 0)

    def test_guest_missing_email(self):
        resp = self.client.post(
            reverse('core:buy_ticket', args=[self.screening.pk]),
            {
                'seat_rows': ['1'], 'seat_numbers': ['1'],
                'guest_email': '',
                'guest_phone': '+36301234567',
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Ticket.objects.count(), 0)


# ═════════════════════════════════════════════════
#  TICKET MANAGEMENT TESTS
# ═════════════════════════════════════════════════

class MyTicketsViewTests(TestDataMixin, TestCase):

    def setUp(self):
        self._create_users()

    def test_requires_login(self):
        resp = self.client.get(reverse('core:my_tickets'))
        self.assertEqual(resp.status_code, 302)

    def test_shows_user_tickets(self):
        self.client.login(username='customer', password='testpass123')
        m = self._create_movie()
        h = self._create_hall()
        s = self._create_screening(movie=m, hall=h)
        Ticket.objects.create(
            screening=s, seat_row=1, seat_number=1, user=self.customer,
        )
        resp = self.client.get(reverse('core:my_tickets'))
        self.assertEqual(resp.status_code, 200)


class CancelTicketViewTests(TestDataMixin, TestCase):

    def setUp(self):
        self._create_users()
        self.movie = self._create_movie()
        self.hall = self._create_hall()
        self.screening = self._create_screening(movie=self.movie, hall=self.hall)

    def test_cancel_ticket(self):
        self.client.login(username='customer', password='testpass123')
        t = Ticket.objects.create(
            screening=self.screening, seat_row=1, seat_number=1,
            user=self.customer,
        )
        resp = self.client.post(reverse('core:cancel_ticket', args=[t.pk]))
        self.assertEqual(resp.status_code, 302)
        t.refresh_from_db()
        self.assertTrue(t.is_cancelled)

    def test_cancel_requires_login(self):
        t = Ticket.objects.create(
            screening=self.screening, seat_row=1, seat_number=1,
            user=self.customer,
        )
        resp = self.client.post(reverse('core:cancel_ticket', args=[t.pk]))
        self.assertEqual(resp.status_code, 302)
        t.refresh_from_db()
        self.assertFalse(t.is_cancelled)

    def test_cancel_near_screening_fails(self):
        near = self._create_screening(
            movie=self.movie, hall=self.hall,
            start_time=timezone.now() + timedelta(hours=2),
        )
        self.client.login(username='customer', password='testpass123')
        t = Ticket.objects.create(
            screening=near, seat_row=1, seat_number=1, user=self.customer,
        )
        resp = self.client.post(reverse('core:cancel_ticket', args=[t.pk]))
        t.refresh_from_db()
        self.assertFalse(t.is_cancelled)

    def test_cancel_other_users_ticket_404(self):
        other = User.objects.create_user(username='other', password='pass123')
        t = Ticket.objects.create(
            screening=self.screening, seat_row=1, seat_number=1, user=other,
        )
        self.client.login(username='customer', password='testpass123')
        resp = self.client.post(reverse('core:cancel_ticket', args=[t.pk]))
        self.assertEqual(resp.status_code, 404)

    def test_cancel_requires_post(self):
        self.client.login(username='customer', password='testpass123')
        t = Ticket.objects.create(
            screening=self.screening, seat_row=1, seat_number=1,
            user=self.customer,
        )
        resp = self.client.get(reverse('core:cancel_ticket', args=[t.pk]))
        self.assertEqual(resp.status_code, 405)


# ═════════════════════════════════════════════════
#  EMAIL TESTS
# ═════════════════════════════════════════════════

class TicketEmailTests(TestDataMixin, TestCase):

    def setUp(self):
        self._create_users()
        self.movie = self._create_movie()
        self.hall = self._create_hall()
        self.screening = self._create_screening(movie=self.movie, hall=self.hall)

    def test_email_sent_on_purchase(self):
        from django.core import mail
        mail.outbox.clear()
        self.client.login(username='customer', password='testpass123')
        self.client.post(
            reverse('core:buy_ticket', args=[self.screening.pk]),
            {'seat_rows': ['1'], 'seat_numbers': ['1']},
        )
        ticket_emails = [
            e for e in mail.outbox if 'Jegyvásárlás' in e.subject
        ]
        self.assertTrue(len(ticket_emails) >= 1)

    def test_email_sent_to_guest(self):
        from django.core import mail
        mail.outbox.clear()
        self.client.post(
            reverse('core:buy_ticket', args=[self.screening.pk]),
            {
                'seat_rows': ['3'], 'seat_numbers': ['3'],
                'guest_email': 'guestbuyer@test.com',
                'guest_phone': '+36301234567',
            },
        )
        recipients = [e.to[0] for e in mail.outbox if 'Jegyvásárlás' in e.subject]
        self.assertIn('guestbuyer@test.com', recipients)
