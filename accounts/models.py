from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User model with role-based permissions.
    Roles: CUSTOMER (Felhasználó), CASHIER (Pénztáros), ADMIN (Adminisztrátor)
    """
    
    class Role(models.TextChoices):
        CUSTOMER = 'customer', 'Felhasználó'
        CASHIER = 'cashier', 'Pénztáros'
        ADMIN = 'admin', 'Adminisztrátor'
    
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CUSTOMER,
        verbose_name='Szerepkör'
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Telefonszám'
    )
    
    class Meta:
        verbose_name = 'Felhasználó'
        verbose_name_plural = 'Felhasználók'
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    @property
    def is_cashier(self):
        return self.role == self.Role.CASHIER
    
    @property
    def is_admin_user(self):
        return self.role == self.Role.ADMIN
    
    @property
    def is_customer(self):
        return self.role == self.Role.CUSTOMER


    def can_manage_movies(self):
        """Check if user can manage movies (admin role OR explicit permission)"""
        return self.is_admin_user or self.is_superuser or self.has_perm('core.manage_movies')

    def can_manage_screenings(self):
        """Check if user can manage screenings (admin role OR explicit permission)"""
        return self.is_admin_user or self.is_superuser or self.has_perm('core.manage_screenings')

    def can_sell_tickets(self):
        """Check if user can sell tickets (cashier/admin role OR explicit permission)"""
        return self.is_cashier or self.is_admin_user or self.is_superuser or self.has_perm('core.sell_tickets')

    def can_verify_tickets(self):
        """Check if user can verify tickets (cashier/admin role OR explicit permission)"""
        return self.is_cashier or self.is_admin_user or self.is_superuser or self.has_perm('core.verify_tickets')

    def can_manage_users(self):
        """Check if user can manage other users (admin only)"""
        return self.is_admin_user or self.is_superuser

    def can_access_cashier(self):
        """Check if user can access the cashier area (sell OR verify tickets)"""
        return self.can_sell_tickets() or self.can_verify_tickets()

    def can_access_management(self):
        """Check if user can access the management/admin dashboard"""
        return (self.is_admin_user or self.is_superuser
                or self.has_perm('core.manage_movies')
                or self.has_perm('core.manage_screenings'))
