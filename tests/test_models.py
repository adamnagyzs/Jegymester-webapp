"""
Tests for core models: Movie, CinemaHall, Screening, Ticket.
"""
from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

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


class MovieModelTests(TestDataMixin, TestCase):

    def test_str(self):
        m = self._create_movie(title='Inception')
        self.assertEqual(str(m), 'Inception')

    def test_has_active_screenings_false(self):
        m = self._create_movie()
        self.assertFalse(m.has_active_screenings())

    def test_has_active_screenings_true(self):
        m = self._create_movie()
        h = self._create_hall()
        self._create_screening(movie=m, hall=h)
        self.assertTrue(m.has_active_screenings())

    def test_can_be_deleted_no_screenings(self):
        m = self._create_movie()
        self.assertTrue(m.can_be_deleted())

    def test_can_be_deleted_with_future_screening(self):
        m = self._create_movie()
        h = self._create_hall()
        self._create_screening(movie=m, hall=h)
        self.assertFalse(m.can_be_deleted())

    def test_can_be_deleted_with_past_screening_only(self):
        m = self._create_movie()
        h = self._create_hall()
        self._create_screening(
            movie=m, hall=h,
            start_time=timezone.now() - timedelta(days=1),
        )
        self.assertTrue(m.can_be_deleted())

    def test_ordering_by_release_date_desc(self):
        m1 = self._create_movie(title='Old', release_date='2020-01-01')
        m2 = self._create_movie(title='New', release_date='2025-06-01')
        movies = list(Movie.objects.all())
        self.assertEqual(movies[0], m2)
        self.assertEqual(movies[1], m1)

    def test_is_active_default_true(self):
        m = self._create_movie()
        self.assertTrue(m.is_active)


class CinemaHallModelTests(TestDataMixin, TestCase):

    def test_capacity_auto_calculated(self):
        h = self._create_hall(rows=5, seats_per_row=8)
        self.assertEqual(h.capacity, 40)

    def test_str(self):
        h = self._create_hall(name='VIP', rows=2, seats_per_row=10)
        self.assertIn('VIP', str(h))
        self.assertIn('20', str(h))

    def test_capacity_updates_on_save(self):
        h = self._create_hall(rows=3, seats_per_row=10)
        self.assertEqual(h.capacity, 30)
        h.rows = 5
        h.save()
        self.assertEqual(h.capacity, 50)


class ScreeningModelTests(TestDataMixin, TestCase):

    def setUp(self):
        self.movie = self._create_movie(duration_minutes=90)
        self.hall = self._create_hall(rows=5, seats_per_row=10)
        self.future = self._create_screening(
            movie=self.movie, hall=self.hall,
            start_time=timezone.now() + timedelta(days=3),
        )
        self.past = self._create_screening(
            movie=self.movie, hall=self.hall,
            start_time=timezone.now() - timedelta(hours=5),
        )

    def test_str(self):
        s = str(self.future)
        self.assertIn(self.movie.title, s)
        self.assertIn(self.hall.name, s)

    def test_end_time(self):
        expected = self.future.start_time + timedelta(minutes=90)
        self.assertEqual(self.future.end_time, expected)

    def test_available_seats_no_tickets(self):
        self.assertEqual(self.future.available_seats, 50)

    def test_available_seats_with_ticket(self):
        Ticket.objects.create(
            screening=self.future, seat_row=1, seat_number=1,
            guest_email='a@b.com',
        )
        self.assertEqual(self.future.available_seats, 49)

    def test_available_seats_cancelled_not_counted(self):
        Ticket.objects.create(
            screening=self.future, seat_row=1, seat_number=1,
            guest_email='a@b.com', is_cancelled=True,
        )
        self.assertEqual(self.future.available_seats, 50)

    def test_is_sold_out(self):
        hall = self._create_hall(rows=1, seats_per_row=2)
        s = self._create_screening(movie=self.movie, hall=hall)
        Ticket.objects.create(screening=s, seat_row=1, seat_number=1, guest_email='a@b.com')
        Ticket.objects.create(screening=s, seat_row=1, seat_number=2, guest_email='a@b.com')
        self.assertTrue(s.is_sold_out)

    def test_is_past(self):
        self.assertTrue(self.past.is_past)
        self.assertFalse(self.future.is_past)

    def test_ordering_by_start_time_asc(self):
        screenings = list(Screening.objects.all())
        self.assertEqual(screenings[0], self.past)
        self.assertEqual(screenings[1], self.future)


class TicketModelTests(TestDataMixin, TestCase):

    def setUp(self):
        self._create_users()
        self.movie = self._create_movie()
        self.hall = self._create_hall(rows=5, seats_per_row=10)
        self.screening = self._create_screening(
            movie=self.movie, hall=self.hall,
            start_time=timezone.now() + timedelta(days=3),
        )

    def test_auto_ticket_code(self):
        t = Ticket.objects.create(
            screening=self.screening, seat_row=1, seat_number=1,
            user=self.customer,
        )
        self.assertTrue(len(t.ticket_code) == 10)
        self.assertTrue(t.ticket_code.isalnum())

    def test_unique_ticket_code(self):
        t1 = Ticket.objects.create(
            screening=self.screening, seat_row=1, seat_number=1,
            user=self.customer,
        )
        t2 = Ticket.objects.create(
            screening=self.screening, seat_row=1, seat_number=2,
            user=self.customer,
        )
        self.assertNotEqual(t1.ticket_code, t2.ticket_code)

    def test_unique_seat_per_screening(self):
        Ticket.objects.create(
            screening=self.screening, seat_row=1, seat_number=1,
            user=self.customer,
        )
        with self.assertRaises(Exception):
            Ticket.objects.create(
                screening=self.screening, seat_row=1, seat_number=1,
                guest_email='x@x.com',
            )

    def test_can_be_cancelled_future(self):
        t = Ticket.objects.create(
            screening=self.screening, seat_row=1, seat_number=1,
            user=self.customer,
        )
        self.assertTrue(t.can_be_cancelled())

    def test_cannot_be_cancelled_too_late(self):
        near_screening = self._create_screening(
            movie=self.movie, hall=self.hall,
            start_time=timezone.now() + timedelta(hours=2),
        )
        t = Ticket.objects.create(
            screening=near_screening, seat_row=1, seat_number=1,
            user=self.customer,
        )
        self.assertFalse(t.can_be_cancelled())

    def test_cannot_be_cancelled_already_cancelled(self):
        t = Ticket.objects.create(
            screening=self.screening, seat_row=1, seat_number=1,
            user=self.customer, is_cancelled=True,
        )
        self.assertFalse(t.can_be_cancelled())

    def test_clean_requires_user_or_guest_email(self):
        t = Ticket(
            screening=self.screening, seat_row=1, seat_number=1,
        )
        with self.assertRaises(ValidationError):
            t.clean()

    def test_clean_validates_seat_row_bounds(self):
        t = Ticket(
            screening=self.screening, seat_row=99, seat_number=1,
            user=self.customer,
        )
        with self.assertRaises(ValidationError):
            t.clean()

    def test_clean_validates_seat_number_bounds(self):
        t = Ticket(
            screening=self.screening, seat_row=1, seat_number=99,
            user=self.customer,
        )
        with self.assertRaises(ValidationError):
            t.clean()

    def test_str(self):
        t = Ticket.objects.create(
            screening=self.screening, seat_row=1, seat_number=1,
            user=self.customer,
        )
        self.assertIn(t.ticket_code, str(t))
