from django.contrib import admin
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth.models import Group
from django.utils.html import format_html
from django.db.models import Count, Q
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'role_badge', 'phone_number',
                    'ticket_count', 'date_joined', 'last_login', 'active_badge']
    list_filter = ['role', 'is_active', 'is_staff', 'date_joined']
    search_fields = ['username', 'email', 'phone_number', 'first_name', 'last_name']
    list_per_page = 25
    ordering = ['-date_joined']

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Személyes adatok', {
            'fields': ('first_name', 'last_name', 'email', 'phone_number')
        }),
        ('Szerepkör', {
            'fields': ('role',),
            'description': 'A szerepkör határozza meg az alap hozzáférési szintet.'
        }),
        ('Jogosultságok', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups',
                        'user_permissions'),
            'classes': ('collapse',),
            'description': 'Egyedi jogosultságok a szerepkörtől függetlenül adhatók. '
                            'Keress rá: manage_movies, manage_screenings, sell_tickets, verify_tickets'
        }),
        ('Fontos dátumok', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',),
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
        ('Egyéni mezők', {
            'fields': ('role', 'phone_number'),
        }),
    )

    filter_horizontal = ('groups', 'user_permissions')
    readonly_fields = ['last_login', 'date_joined']

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _ticket_count=Count('tickets', filter=Q(tickets__is_cancelled=False))
        )

    @admin.display(description='Szerepkör', ordering='role')
    def role_badge(self, obj):
        colors = {
            'admin': '#dc3545',
            'cashier': '#ffc107',
            'customer': '#6c757d',
        }
        text_colors = {
            'admin': 'white',
            'cashier': 'black',
            'customer': 'white',
        }
        bg = colors.get(obj.role, '#6c757d')
        fg = text_colors.get(obj.role, 'white')
        return format_html(
            '<span style="background:{}; color:{}; padding:3px 8px; '
            'border-radius:4px; font-size:11px; font-weight:bold;">{}</span>',
            bg, fg, obj.get_role_display()
        )

    @admin.display(description='Aktív', boolean=True, ordering='is_active')
    def active_badge(self, obj):
        return obj.is_active

    @admin.display(description='Jegyek')
    def ticket_count(self, obj):
        return getattr(obj, '_ticket_count', 0)

    actions = ['make_customer', 'make_cashier', 'make_admin',
                'activate_users', 'deactivate_users']

    @admin.action(description='Szerepkör → Felhasználó')
    def make_customer(self, request, queryset):
        count = queryset.exclude(pk=request.user.pk).update(
            role='customer', is_staff=False, is_superuser=False
        )
        self.message_user(request, f'{count} felhasználó átállítva Felhasználó szerepkörre.')

    @admin.action(description='Szerepkör → Pénztáros')
    def make_cashier(self, request, queryset):
        count = queryset.exclude(pk=request.user.pk).update(
            role='cashier', is_staff=True, is_superuser=False
        )
        self.message_user(request, f'{count} felhasználó átállítva Pénztáros szerepkörre.')

    @admin.action(description='Szerepkör → Adminisztrátor')
    def make_admin(self, request, queryset):
        count = queryset.update(
            role='admin', is_staff=True, is_superuser=True
        )
        self.message_user(request, f'{count} felhasználó átállítva Adminisztrátor szerepkörre.')

    @admin.action(description='Kijelölt felhasználók aktiválása')
    def activate_users(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} felhasználó aktiválva.')

    @admin.action(description='Kijelölt felhasználók deaktiválása')
    def deactivate_users(self, request, queryset):
        count = queryset.exclude(pk=request.user.pk).update(is_active=False)
        self.message_user(request, f'{count} felhasználó deaktiválva.')



admin.site.unregister(Group)


@admin.register(Group)
class CustomGroupAdmin(GroupAdmin):
    list_display = ['name', 'user_count', 'permission_summary']
    search_fields = ['name']
    filter_horizontal = ['permissions']

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _user_count=Count('user')
        ).prefetch_related('permissions')

    @admin.display(description='Tagok száma')
    def user_count(self, obj):
        return getattr(obj, '_user_count', 0)

    @admin.display(description='Jogosultságok')
    def permission_summary(self, obj):
        perms = obj.permissions.all()
        if not perms:
            return '—'

        custom_codes = {
            'manage_movies': '🎬 Filmek',
            'manage_screenings': '📅 Vetítések',
            'sell_tickets': '💰 Jegy eladás',
            'verify_tickets': '✅ Jegy ellenőrzés',
        }
        labels = []
        other_count = 0
        for p in perms:
            if p.codename in custom_codes:
                labels.append(custom_codes[p.codename])
            else:
                other_count += 1
        summary = ', '.join(labels)
        if other_count:
            summary += f' (+{other_count} egyéb)' if summary else f'{other_count} jogosultság'
        return summary
