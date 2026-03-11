"""
Tests for admin/management views: dashboard, movies CRUD, screenings CRUD, user management.
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


class AdminDashboardViewTests(TestDataMixin, TestCase):

    def setUp(self):
        self._create_users()

    def test_customer_forbidden(self):
        self.client.login(username='customer', password='testpass123')
        resp = self.client.get(reverse('core:admin_dashboard'))
        self.assertEqual(resp.status_code, 403)

    def test_cashier_forbidden(self):
        self.client.login(username='cashier', password='testpass123')
        resp = self.client.get(reverse('core:admin_dashboard'))
        self.assertEqual(resp.status_code, 403)

    def test_admin_allowed(self):
        self.client.login(username='admin_user', password='testpass123')
        resp = self.client.get(reverse('core:admin_dashboard'))
        self.assertEqual(resp.status_code, 200)


class AdminMovieListViewTests(TestDataMixin, TestCase):

    def setUp(self):
        self._create_users()

    def test_admin_can_see_movies(self):
        self._create_movie(title='Listed')
        self.client.login(username='admin_user', password='testpass123')
        resp = self.client.get(reverse('core:admin_movie_list'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Listed')

    def test_customer_forbidden(self):
        self.client.login(username='customer', password='testpass123')
        resp = self.client.get(reverse('core:admin_movie_list'))
        self.assertEqual(resp.status_code, 403)


class AdminMovieAddViewTests(TestDataMixin, TestCase):

    def setUp(self):
        self._create_users()

    def test_add_movie_get(self):
        self.client.login(username='admin_user', password='testpass123')
        resp = self.client.get(reverse('core:admin_movie_add'))
        self.assertEqual(resp.status_code, 200)

    def test_add_movie_post(self):
        self.client.login(username='admin_user', password='testpass123')
        resp = self.client.post(reverse('core:admin_movie_add'), {
            'title': 'New Movie',
            'description': 'Description',
            'duration_minutes': '120',
            'genre': 'Action',
            'director': 'Director',
            'release_date': '2025-06-01',
            'age_rating': '12',
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Movie.objects.filter(title='New Movie').exists())

    def test_add_movie_missing_title(self):
        self.client.login(username='admin_user', password='testpass123')
        resp = self.client.post(reverse('core:admin_movie_add'), {
            'title': '',
            'description': 'Desc',
            'duration_minutes': '120',
            'genre': 'Action',
            'director': 'Dir',
            'release_date': '2025-06-01',
        })
        self.assertEqual(resp.status_code, 200)

    def test_add_movie_invalid_duration(self):
        self.client.login(username='admin_user', password='testpass123')
        resp = self.client.post(reverse('core:admin_movie_add'), {
            'title': 'Movie',
            'description': 'Desc',
            'duration_minutes': 'abc',
            'genre': 'Action',
            'director': 'Dir',
            'release_date': '2025-06-01',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Movie.objects.filter(title='Movie').exists())


class AdminMovieEditViewTests(TestDataMixin, TestCase):

    def setUp(self):
        self._create_users()
        self.movie = self._create_movie(title='Original')

    def test_edit_get(self):
        self.client.login(username='admin_user', password='testpass123')
        resp = self.client.get(
            reverse('core:admin_movie_edit', args=[self.movie.pk])
        )
        self.assertEqual(resp.status_code, 200)

    def test_edit_post(self):
        self.client.login(username='admin_user', password='testpass123')
        resp = self.client.post(
            reverse('core:admin_movie_edit', args=[self.movie.pk]),
            {
                'title': 'Updated',
                'description': 'Updated desc',
                'duration_minutes': '90',
                'genre': 'Comedy',
                'director': 'New Dir',
                'release_date': '2025-07-01',
                'is_active': 'on',
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.movie.refresh_from_db()
        self.assertEqual(self.movie.title, 'Updated')


class AdminMovieDeleteViewTests(TestDataMixin, TestCase):

    def setUp(self):
        self._create_users()

    def test_delete_movie_no_screenings(self):
        m = self._create_movie(title='Deletable')
        self.client.login(username='admin_user', password='testpass123')
        resp = self.client.post(
            reverse('core:admin_movie_delete', args=[m.pk])
        )
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Movie.objects.filter(pk=m.pk).exists())

    def test_delete_movie_with_future_screening_fails(self):
        m = self._create_movie()
        h = self._create_hall()
        self._create_screening(movie=m, hall=h)
        self.client.login(username='admin_user', password='testpass123')
        resp = self.client.post(
            reverse('core:admin_movie_delete', args=[m.pk])
        )
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Movie.objects.filter(pk=m.pk).exists())

    def test_delete_requires_post(self):
        m = self._create_movie()
        self.client.login(username='admin_user', password='testpass123')
        resp = self.client.get(
            reverse('core:admin_movie_delete', args=[m.pk])
        )
        self.assertEqual(resp.status_code, 405)


class AdminScreeningListViewTests(TestDataMixin, TestCase):

    def setUp(self):
        self._create_users()

    def test_admin_can_view(self):
        self.client.login(username='admin_user', password='testpass123')
        resp = self.client.get(reverse('core:admin_screening_list'))
        self.assertEqual(resp.status_code, 200)

    def test_customer_forbidden(self):
        self.client.login(username='customer', password='testpass123')
        resp = self.client.get(reverse('core:admin_screening_list'))
        self.assertEqual(resp.status_code, 403)


class AdminScreeningAddViewTests(TestDataMixin, TestCase):

    def setUp(self):
        self._create_users()
        self.movie = self._create_movie()
        self.hall = self._create_hall()

    def test_add_screening_get(self):
        self.client.login(username='admin_user', password='testpass123')
        resp = self.client.get(reverse('core:admin_screening_add'))
        self.assertEqual(resp.status_code, 200)

    def test_add_screening_post(self):
        self.client.login(username='admin_user', password='testpass123')
        future = (timezone.now() + timedelta(days=10)).strftime('%Y-%m-%d %H:%M')
        resp = self.client.post(reverse('core:admin_screening_add'), {
            'movie': str(self.movie.pk),
            'hall': str(self.hall.pk),
            'start_time': future,
            'ticket_price': '2000',
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Screening.objects.count(), 1)

    def test_add_screening_missing_time(self):
        self.client.login(username='admin_user', password='testpass123')
        resp = self.client.post(reverse('core:admin_screening_add'), {
            'movie': str(self.movie.pk),
            'hall': str(self.hall.pk),
            'start_time': '',
            'ticket_price': '2000',
        })
        self.assertEqual(resp.status_code, 200)


class AdminScreeningEditViewTests(TestDataMixin, TestCase):

    def setUp(self):
        self._create_users()
        self.movie = self._create_movie()
        self.hall = self._create_hall()
        self.screening = self._create_screening(movie=self.movie, hall=self.hall)

    def test_edit_get(self):
        self.client.login(username='admin_user', password='testpass123')
        resp = self.client.get(
            reverse('core:admin_screening_edit', args=[self.screening.pk])
        )
        self.assertEqual(resp.status_code, 200)

    def test_edit_post(self):
        self.client.login(username='admin_user', password='testpass123')
        future = (timezone.now() + timedelta(days=14)).strftime('%Y-%m-%d %H:%M')
        resp = self.client.post(
            reverse('core:admin_screening_edit', args=[self.screening.pk]),
            {
                'movie': str(self.movie.pk),
                'hall': str(self.hall.pk),
                'start_time': future,
                'ticket_price': '3000',
                'is_active': 'on',
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.screening.refresh_from_db()
        self.assertEqual(self.screening.ticket_price, Decimal('3000'))


class AdminUserListViewTests(TestDataMixin, TestCase):

    def setUp(self):
        self._create_users()

    def test_admin_can_view(self):
        self.client.login(username='admin_user', password='testpass123')
        resp = self.client.get(reverse('core:admin_user_list'))
        self.assertEqual(resp.status_code, 200)

    def test_customer_forbidden(self):
        self.client.login(username='customer', password='testpass123')
        resp = self.client.get(reverse('core:admin_user_list'))
        self.assertEqual(resp.status_code, 403)

    def test_cashier_forbidden(self):
        self.client.login(username='cashier', password='testpass123')
        resp = self.client.get(reverse('core:admin_user_list'))
        self.assertEqual(resp.status_code, 403)

    def test_search_filter(self):
        self.client.login(username='admin_user', password='testpass123')
        resp = self.client.get(
            reverse('core:admin_user_list'), {'q': 'customer'}
        )
        self.assertEqual(resp.status_code, 200)

    def test_role_filter(self):
        self.client.login(username='admin_user', password='testpass123')
        resp = self.client.get(
            reverse('core:admin_user_list'), {'role': 'cashier'}
        )
        self.assertEqual(resp.status_code, 200)


class AdminUserEditViewTests(TestDataMixin, TestCase):

    def setUp(self):
        self._create_users()

    def test_edit_get(self):
        self.client.login(username='admin_user', password='testpass123')
        resp = self.client.get(
            reverse('core:admin_user_edit', args=[self.customer.pk])
        )
        self.assertEqual(resp.status_code, 200)

    def test_change_role(self):
        self.client.login(username='admin_user', password='testpass123')
        resp = self.client.post(
            reverse('core:admin_user_edit', args=[self.customer.pk]),
            {'role': 'cashier', 'is_active': 'on'},
        )
        self.assertEqual(resp.status_code, 302)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.role, 'cashier')

    def test_cannot_remove_own_admin(self):
        self.client.login(username='admin_user', password='testpass123')
        resp = self.client.post(
            reverse('core:admin_user_edit', args=[self.admin_user.pk]),
            {'role': 'customer', 'is_active': 'on'},
        )
        self.admin_user.refresh_from_db()
        self.assertEqual(self.admin_user.role, User.Role.ADMIN)

    def test_invalid_role(self):
        self.client.login(username='admin_user', password='testpass123')
        resp = self.client.post(
            reverse('core:admin_user_edit', args=[self.customer.pk]),
            {'role': 'hacker', 'is_active': 'on'},
        )
        self.assertEqual(resp.status_code, 302)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.role, User.Role.CUSTOMER)

    def test_assign_permissions(self):
        from django.contrib.auth.models import Permission
        self.client.login(username='admin_user', password='testpass123')
        resp = self.client.post(
            reverse('core:admin_user_edit', args=[self.customer.pk]),
            {
                'role': 'customer',
                'is_active': 'on',
                'permissions': ['manage_movies', 'sell_tickets'],
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.customer = User.objects.get(pk=self.customer.pk)
        perms = set(self.customer.user_permissions.values_list('codename', flat=True))
        self.assertIn('manage_movies', perms)
        self.assertIn('sell_tickets', perms)
