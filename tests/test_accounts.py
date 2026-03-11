"""
Tests for the accounts app.
Covers: User model, roles, permissions, signals, adapter.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()


class UserModelTests(TestCase):
    """Tests for the custom User model and role properties."""

    def setUp(self):
        self.customer = User.objects.create_user(
            username='customer', password='testpass123', role=User.Role.CUSTOMER,
            email='customer@example.com',
        )
        self.cashier = User.objects.create_user(
            username='cashier', password='testpass123', role=User.Role.CASHIER,
            email='cashier@example.com',
        )
        self.admin = User.objects.create_user(
            username='admin_user', password='testpass123', role=User.Role.ADMIN,
            email='admin@example.com',
        )
        self.superuser = User.objects.create_superuser(
            username='super', password='testpass123', email='super@example.com',
        )

    def test_customer_role_properties(self):
        self.assertTrue(self.customer.is_customer)
        self.assertFalse(self.customer.is_cashier)
        self.assertFalse(self.customer.is_admin_user)

    def test_cashier_role_properties(self):
        self.assertTrue(self.cashier.is_cashier)
        self.assertFalse(self.cashier.is_customer)
        self.assertFalse(self.cashier.is_admin_user)

    def test_admin_role_properties(self):
        self.assertTrue(self.admin.is_admin_user)
        self.assertFalse(self.admin.is_customer)
        self.assertFalse(self.admin.is_cashier)


    def test_customer_cannot_manage_movies(self):
        self.assertFalse(self.customer.can_manage_movies())

    def test_customer_cannot_manage_screenings(self):
        self.assertFalse(self.customer.can_manage_screenings())

    def test_customer_cannot_sell_tickets(self):
        self.assertFalse(self.customer.can_sell_tickets())

    def test_customer_cannot_verify_tickets(self):
        self.assertFalse(self.customer.can_verify_tickets())

    def test_customer_cannot_manage_users(self):
        self.assertFalse(self.customer.can_manage_users())

    def test_customer_cannot_access_cashier(self):
        self.assertFalse(self.customer.can_access_cashier())

    def test_customer_cannot_access_management(self):
        self.assertFalse(self.customer.can_access_management())

    def test_cashier_can_sell_tickets(self):
        self.assertTrue(self.cashier.can_sell_tickets())

    def test_cashier_can_verify_tickets(self):
        self.assertTrue(self.cashier.can_verify_tickets())

    def test_cashier_can_access_cashier(self):
        self.assertTrue(self.cashier.can_access_cashier())

    def test_cashier_cannot_manage_movies(self):
        self.assertFalse(self.cashier.can_manage_movies())

    def test_cashier_cannot_manage_users(self):
        self.assertFalse(self.cashier.can_manage_users())

    def test_admin_can_manage_movies(self):
        self.assertTrue(self.admin.can_manage_movies())

    def test_admin_can_manage_screenings(self):
        self.assertTrue(self.admin.can_manage_screenings())

    def test_admin_can_sell_tickets(self):
        self.assertTrue(self.admin.can_sell_tickets())

    def test_admin_can_verify_tickets(self):
        self.assertTrue(self.admin.can_verify_tickets())

    def test_admin_can_manage_users(self):
        self.assertTrue(self.admin.can_manage_users())

    def test_admin_can_access_cashier(self):
        self.assertTrue(self.admin.can_access_cashier())

    def test_admin_can_access_management(self):
        self.assertTrue(self.admin.can_access_management())

    def test_superuser_has_all_permissions(self):
        self.assertTrue(self.superuser.can_manage_movies())
        self.assertTrue(self.superuser.can_manage_screenings())
        self.assertTrue(self.superuser.can_sell_tickets())
        self.assertTrue(self.superuser.can_verify_tickets())
        self.assertTrue(self.superuser.can_manage_users())
        self.assertTrue(self.superuser.can_access_cashier())
        self.assertTrue(self.superuser.can_access_management())


    def test_customer_with_manage_movies_perm(self):
        """Customer given explicit manage_movies perm should be able to manage movies."""
        from django.contrib.auth.models import Permission
        perm = Permission.objects.get(codename='manage_movies')
        self.customer.user_permissions.add(perm)
        self.customer = User.objects.get(pk=self.customer.pk)
        self.assertTrue(self.customer.can_manage_movies())
        self.assertTrue(self.customer.can_access_management())

    def test_customer_with_sell_tickets_perm(self):
        from django.contrib.auth.models import Permission
        perm = Permission.objects.get(codename='sell_tickets')
        self.customer.user_permissions.add(perm)
        self.customer = User.objects.get(pk=self.customer.pk)
        self.assertTrue(self.customer.can_sell_tickets())
        self.assertTrue(self.customer.can_access_cashier())


    def test_user_str(self):
        self.assertIn('customer', str(self.customer))
        self.assertIn('Felhasználó', str(self.customer))


    def test_default_role_is_customer(self):
        u = User.objects.create_user(username='newuser', password='pass123')
        self.assertEqual(u.role, User.Role.CUSTOMER)


class SignalTests(TestCase):
    """Test the welcome email signal."""

    def test_welcome_email_sent_on_create(self):
        from django.core import mail
        User.objects.create_user(
            username='signaluser', password='pass123', email='signal@example.com'
        )
        self.assertTrue(len(mail.outbox) >= 1)
        self.assertIn('Üdvözlünk', mail.outbox[0].subject)

    def test_no_email_without_address(self):
        from django.core import mail
        mail.outbox.clear()
        User.objects.create_user(username='noemail', password='pass123', email='')
        self.assertEqual(len(mail.outbox), 0)
