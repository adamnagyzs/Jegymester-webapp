from django.contrib import admin  
from django.utils import timezone  
from django.utils.html import format_html  
from django.db.models import Count, Q, Sum  
from .models import Movie, CinemaHall, Screening, Ticket  


# ── Inline modellek ──────────────────────────────────────────

class ScreeningInline(admin.TabularInline):  
    """Show screenings inline on the Movie detail page"""
    model = Screening  
    extra = 0  
    fields = ['hall', 'start_time', 'ticket_price', 'is_active']  
    ordering = ['start_time']  
    show_change_link = True  

    def get_queryset(self, request):  
        return super().get_queryset(request).select_related('hall')  


class TicketInline(admin.TabularInline):  
    """Show tickets inline on the Screening detail page"""
    model = Ticket  
    extra = 0  
    fields = ['ticket_code', 'user', 'guest_email', 'seat_row', 'seat_number',  
              'is_cancelled', 'is_verified']  
    readonly_fields = ['ticket_code', 'purchase_date']  
    ordering = ['seat_row', 'seat_number']  
    show_change_link = True  

    def get_queryset(self, request):  
        return super().get_queryset(request).select_related('user')  


# ── Film Admin ────────────────────────────────────────────

@admin.register(Movie)  
class MovieAdmin(admin.ModelAdmin):  
    list_display = ['title', 'genre', 'director', 'duration_display',  
                    'release_date', 'age_rating', 'poster_preview',  
                    'screening_count', 'is_active']  
    list_filter = ['is_active', 'genre', 'age_rating', 'release_date']  
    search_fields = ['title', 'director', 'genre', 'description']  
    list_editable = ['is_active']  
    ordering = ['-release_date']  
    list_per_page = 25  
    date_hierarchy = 'release_date'  
    readonly_fields = ['created_at', 'updated_at', 'poster_preview_large'] 
    inlines = [ScreeningInline]  
    fieldsets = (  
        ('Alapadatok', {  
            'fields': ('title', 'description', 'genre', 'director')  
        }),
        ('Részletek', {  
            'fields': ('duration_minutes', 'release_date', 'age_rating')  
        }),
        ('Poszter', {  
            'fields': ('poster_url', 'poster_preview_large')  
        }),
        ('Állapot', {  
            'fields': ('is_active', 'created_at', 'updated_at') 
        }),
    )

    def get_queryset(self, request):  
        return super().get_queryset(request).annotate(  
            _screening_count=Count('screenings',  
                                   filter=Q(screenings__is_active=True,  
                                            screenings__start_time__gt=timezone.now()))  
        )

    @admin.display(description='Időtartam', ordering='duration_minutes')  
    def duration_display(self, obj):  
        h, m = divmod(obj.duration_minutes, 60)  
        return f'{h}ó {m}p' if h else f'{m} perc'  

    @admin.display(description='Vetítések')  
    def screening_count(self, obj):  
        return getattr(obj, '_screening_count', 0)  

    @admin.display(description='Poszter')  
    def poster_preview(self, obj):  
        if obj.poster_url:  
            return format_html(  
                '<img src="{}" style="height:40px; border-radius:4px;" />',  
                obj.poster_url  
            )
        return '—'  

    @admin.display(description='Poszter előnézet')  
    def poster_preview_large(self, obj):  
        if obj.poster_url:  
            return format_html(  
                '<img src="{}" style="max-height:300px; border-radius:8px;" />', 
                obj.poster_url  
            )
        return 'Nincs poszter'  

    actions = ['activate_movies', 'deactivate_movies']  

    @admin.action(description='Kijelölt filmek aktiválása')  
    def activate_movies(self, request, queryset):  
        count = queryset.update(is_active=True)  
        self.message_user(request, f'{count} film aktiválva.') 

    @admin.action(description='Kijelölt filmek deaktiválása')  
    def deactivate_movies(self, request, queryset):  
        count = queryset.update(is_active=False)  
        self.message_user(request, f'{count} film deaktiválva.')  


# ── Moziterem Admin ──────────────────────────────────────

@admin.register(CinemaHall) 
class CinemaHallAdmin(admin.ModelAdmin):  
    list_display = ['name', 'rows', 'seats_per_row', 'capacity', 'screening_count']  
    search_fields = ['name']  
    readonly_fields = ['capacity']  

    fieldsets = (  
        (None, {  
            'fields': ('name', 'rows', 'seats_per_row', 'capacity')  
        }),
    )

    def get_queryset(self, request): 
        return super().get_queryset(request).annotate(  
            _screening_count=Count('screenings',  
                                   filter=Q(screenings__is_active=True,  
                                            screenings__start_time__gt=timezone.now()))  
        )

    @admin.display(description='Aktív vetítések')  
    def screening_count(self, obj):  
        return getattr(obj, '_screening_count', 0)  


# ── Vetítés Admin ────────────────────────────────────────

@admin.register(Screening)  
class ScreeningAdmin(admin.ModelAdmin):  
    list_display = ['movie', 'hall', 'start_time', 'ticket_price_display',  
                    'tickets_sold', 'available_display', 'status_badge', 'is_active']  
    list_filter = ['is_active', 'hall', 'start_time', 'movie']  
    search_fields = ['movie__title', 'hall__name']  
    list_editable = ['is_active']  
    ordering = ['-start_time']  
    list_per_page = 30  
    date_hierarchy = 'start_time' 
    readonly_fields = ['created_at', 'tickets_sold', 'available_display',  
                       'revenue_display']  
    raw_id_fields = ['movie']  
    autocomplete_fields = ['movie', 'hall']  
    inlines = [TicketInline]  

    fieldsets = (  
        ('Vetítés', {  
            'fields': ('movie', 'hall', 'start_time', 'ticket_price')  
        }),
        ('Állapot', {  
            'fields': ('is_active', 'created_at')  
        }),
        ('Statisztika', {  
            'fields': ('tickets_sold', 'available_display', 'revenue_display'),  
            'classes': ('collapse',),  
        }),
    )

    def get_queryset(self, request):  
        return super().get_queryset(request).select_related(  
            'movie', 'hall'  
        ).annotate(  
            _sold_count=Count('tickets', filter=Q(tickets__is_cancelled=False)), 
            _revenue=Sum('tickets__screening__ticket_price', 
                         filter=Q(tickets__is_cancelled=False))  
        )

    @admin.display(description='Jegyár', ordering='ticket_price') 
    def ticket_price_display(self, obj):  
        return f'{obj.ticket_price:,.0f} Ft'  

    @admin.display(description='Eladott')  
    def tickets_sold(self, obj):  
        return getattr(obj, '_sold_count', 0)  

    @admin.display(description='Szabad hely')  
    def available_display(self, obj):  
        sold = getattr(obj, '_sold_count', 0)  
        total = obj.hall.capacity  
        available = total - sold  
        if available <= 0:  
            return format_html('<span style="color:red; font-weight:bold;">TELT HÁZ</span>') 
        pct = (sold / total * 100) if total else 0  
        color = 'green' if pct < 50 else ('orange' if pct < 80 else 'red')  
        return format_html(  
            '<span style="color:{}">{} / {}</span>', color, available, total 
        )

    @admin.display(description='Státusz')  
    def status_badge(self, obj):  
        if obj.start_time < timezone.now():  
            return format_html('<span style="color:gray;">⏱ Lejárt</span>')  
        sold = getattr(obj, '_sold_count', 0)  
        if sold >= obj.hall.capacity:  
            return format_html('<span style="color:red;">🔴 Telt</span>')  
        if not obj.is_active: 
            return format_html('<span style="color:gray;">⚫ Inaktív</span>')  
        return format_html('<span style="color:green;">🟢 Aktív</span>')  

    @admin.display(description='Bevétel')  
    def revenue_display(self, obj):  
        sold = getattr(obj, '_sold_count', 0)  
        revenue = obj.ticket_price * sold  
        return f'{revenue:,.0f} Ft'  

    actions = ['activate_screenings', 'deactivate_screenings'] 

    @admin.action(description='Kijelölt vetítések aktiválása')  
    def activate_screenings(self, request, queryset):  
        count = queryset.update(is_active=True)  
        self.message_user(request, f'{count} vetítés aktiválva.')  

    @admin.action(description='Kijelölt vetítések deaktiválása')  
    def deactivate_screenings(self, request, queryset):  
        count = queryset.update(is_active=False)  
        self.message_user(request, f'{count} vetítés deaktiválva.')  


# ── Jegy Admin ───────────────────────────────────────────

@admin.register(Ticket)  
class TicketAdmin(admin.ModelAdmin):  
    list_display = ['ticket_code', 'movie_title', 'screening_time',  
                    'hall_name', 'seat_display', 'buyer_display',  
                    'purchase_date', 'cancel_badge', 'verify_badge']  
    list_filter = ['is_cancelled', 'is_verified', 'screening__hall',  
                   'purchase_date', 'screening__movie']  
    search_fields = ['ticket_code', 'user__username', 'user__email',  
                     'guest_email', 'screening__movie__title']  
    ordering = ['-purchase_date'] 
    list_per_page = 30  
    date_hierarchy = 'purchase_date'  
    readonly_fields = ['ticket_code', 'purchase_date', 'screening_info']  
    raw_id_fields = ['screening', 'user', 'verified_by', 'sold_by']  

    fieldsets = (  
        ('Jegy', {  
            'fields': ('ticket_code', 'screening', 'screening_info')  
        }),
        ('Ülőhely', { 
            'fields': ('seat_row', 'seat_number')  
        }),
        ('Vásárló', {  
            'fields': ('user', 'guest_email', 'guest_phone')  
        }),
        ('Tranzakció', {  
            'fields': ('purchase_date', 'sold_by')  
        }),
        ('Állapot', {  
            'fields': ('is_cancelled', 'is_verified', 'verified_by')  
        }),
    )

    def get_queryset(self, request):  
        return super().get_queryset(request).select_related(  
            'screening__movie', 'screening__hall', 'user',  
            'verified_by', 'sold_by'  
        )

    @admin.display(description='Film', ordering='screening__movie__title')  
    def movie_title(self, obj):  
        return obj.screening.movie.title  

    @admin.display(description='Időpont', ordering='screening__start_time')  
    def screening_time(self, obj):  
        return obj.screening.start_time.strftime('%Y.%m.%d %H:%M')  

    @admin.display(description='Terem')  
    def hall_name(self, obj):  
        return obj.screening.hall.name  

    @admin.display(description='Hely') 
    def seat_display(self, obj):  
        return f'{obj.seat_row}. sor / {obj.seat_number}. szék'  

    @admin.display(description='Vásárló')  
    def buyer_display(self, obj):  
        if obj.user:  
            return obj.user.username  
        return obj.guest_email or '—'  

    @admin.display(description='Törölve', boolean=True)  
    def cancel_badge(self, obj): 
        return obj.is_cancelled  

    @admin.display(description='Ellenőrizve', boolean=True)  
    def verify_badge(self, obj):  
        return obj.is_verified  

    @admin.display(description='Vetítés info')  
    def screening_info(self, obj):  
        s = obj.screening  
        return format_html(  
            '<strong>{}</strong><br>'  
            '{} — {}<br>'  
            'Terem: {} | Jegyár: {:,.0f} Ft',  
            s.movie.title,  
            s.start_time.strftime('%Y.%m.%d %H:%M'),  
            s.end_time.strftime('%H:%M'),  
            s.hall.name,  
            s.ticket_price,  
        )

    actions = ['cancel_tickets', 'uncancel_tickets', 'mark_verified']  

    @admin.action(description='Kijelölt jegyek törlése (sztornó)') 
    def cancel_tickets(self, request, queryset):  
        count = queryset.filter(is_cancelled=False).update(is_cancelled=True)  
        self.message_user(request, f'{count} jegy sztornózva.')  

    @admin.action(description='Kijelölt jegyek visszaállítása')  
    def uncancel_tickets(self, request, queryset):  
        count = queryset.filter(is_cancelled=True).update(is_cancelled=False)  
        self.message_user(request, f'{count} jegy visszaállítva.')  

    @admin.action(description='Kijelölt jegyek ellenőrzöttnek jelölése')  
    def mark_verified(self, request, queryset):  
        count = queryset.filter(is_verified=False).update(  
            is_verified=True, verified_by=request.user  
        )
        self.message_user(request, f'{count} jegy ellenőrizve.')  
