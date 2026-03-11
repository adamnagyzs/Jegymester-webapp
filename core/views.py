from __future__ import annotations

import logging
import re
from typing import Any, Callable
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.utils.html import escape
from django.http import HttpResponseForbidden, HttpResponseBadRequest, HttpRequest, HttpResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.db import transaction, IntegrityError
from django.db.models import Count, Q
from django.core.paginator import Paginator
from functools import wraps

from django.core.mail import send_mail
from django.conf import settings as django_settings

from accounts.models import User
from .models import Movie, Screening, Ticket, CinemaHall
from .validators import (
    sanitize_string, validate_seat, validate_email_input,
    validate_phone_input, validate_positive_int,
)

security_logger = logging.getLogger('core.security')


def _send_ticket_email(ticket: Ticket) -> None:
    """Send ticket confirmation email for a single ticket."""
    _send_tickets_email([ticket])


def _send_tickets_email(tickets: list[Ticket]) -> None:
    """Send ticket confirmation email with all transaction details for one or more tickets."""
    if not tickets:
        return

    first = tickets[0]
    recipient = None
    if first.user and first.user.email:
        recipient = first.user.email
    elif first.guest_email:
        recipient = first.guest_email

    if not recipient:
        return

    screening = first.screening
    movie = screening.movie

    if len(tickets) == 1:
        subject = f'Jegyvásárlás visszaigazolás – {movie.title} 🎬'
        seat_lines = (
            f'  Hely:          Sor {first.seat_row}, Szék {first.seat_number}\n'
            f'  Jegyár:        {screening.ticket_price} Ft\n'
        )
        code_info = f'Kérjük, a jegykódot ({first.ticket_code}) mutasd be a pénztárnál belépéskor.'
    else:
        subject = f'Jegyvásárlás visszaigazolás – {len(tickets)} jegy – {movie.title} 🎬'
        seat_lines = ''
        for i, t in enumerate(tickets, 1):
            seat_lines += f'  {i}. jegy:  Sor {t.seat_row}, Szék {t.seat_number} – Kód: {t.ticket_code}\n'
        total = screening.ticket_price * len(tickets)
        seat_lines += f'\n  Összesen:      {total} Ft ({len(tickets)} × {screening.ticket_price} Ft)\n'
        codes = ', '.join(t.ticket_code for t in tickets)
        code_info = f'Kérjük, a jegykódokat ({codes}) mutasd be a pénztárnál belépéskor.'

    body = (
        f'Kedves Vásárló!\n\n'
        f'Köszönjük a jegyvásárlást! Íme a tranzakció részletei:\n\n'
        f'───────────────────────────\n'
        f'  Film:          {movie.title}\n'
        f'  Időpont:       {screening.start_time.strftime("%Y.%m.%d %H:%M")}\n'
        f'  Terem:         {screening.hall.name}\n'
        f'{seat_lines}'
        f'───────────────────────────\n\n'
        f'{code_info}\n\n'
        f'Jó szórakozást kívánunk!\n\n'
        f'Üdvözlettel,\n'
        f'A Cinema csapata'
    )

    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=django_settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            fail_silently=True,
        )
    except Exception:
        pass


def cashier_required(view_func: Callable[..., HttpResponse]) -> Callable[..., HttpResponse]:
    @wraps(view_func)
    @login_required
    def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if not request.user.can_sell_tickets():  # type: ignore[union-attr]
            return HttpResponseForbidden("Nincs jogosultsága ehhez a művelethez.")
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_required(view_func: Callable[..., HttpResponse]) -> Callable[..., HttpResponse]:
    @wraps(view_func)
    @login_required
    def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if not (request.user.is_admin_user or request.user.is_superuser):  # type: ignore[union-attr]
            return HttpResponseForbidden("Nincs jogosultsága ehhez a művelethez.")
        return view_func(request, *args, **kwargs)
    return wrapper


def movie_manager_required(view_func: Callable[..., HttpResponse]) -> Callable[..., HttpResponse]:
    """Requires admin role OR 'core.manage_movies' permission"""
    @wraps(view_func)
    @login_required
    def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if not request.user.can_manage_movies():  # type: ignore[union-attr]
            return HttpResponseForbidden("Nincs jogosultsága ehhez a művelethez.")
        return view_func(request, *args, **kwargs)
    return wrapper


def screening_manager_required(view_func: Callable[..., HttpResponse]) -> Callable[..., HttpResponse]:
    """Requires admin role OR 'core.manage_screenings' permission"""
    @wraps(view_func)
    @login_required
    def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if not request.user.can_manage_screenings():  # type: ignore[union-attr]
            return HttpResponseForbidden("Nincs jogosultsága ehhez a művelethez.")
        return view_func(request, *args, **kwargs)
    return wrapper


def ticket_verifier_required(view_func: Callable[..., HttpResponse]) -> Callable[..., HttpResponse]:
    """Requires cashier/admin role OR 'core.verify_tickets' permission"""
    @wraps(view_func)
    @login_required
    def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if not request.user.can_verify_tickets():  # type: ignore[union-attr]
            return HttpResponseForbidden("Nincs jogosultsága ehhez a művelethez.")
        return view_func(request, *args, **kwargs)
    return wrapper


def cashier_area_required(view_func: Callable[..., HttpResponse]) -> Callable[..., HttpResponse]:
    """Requires sell_tickets OR verify_tickets permission (or cashier/admin role)"""
    @wraps(view_func)
    @login_required
    def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if not request.user.can_access_cashier():  # type: ignore[union-attr]
            return HttpResponseForbidden("Nincs jogosultsága ehhez a művelethez.")
        return view_func(request, *args, **kwargs)
    return wrapper


def management_required(view_func: Callable[..., HttpResponse]) -> Callable[..., HttpResponse]:
    """Requires admin role OR any management permission (manage_movies/manage_screenings)"""
    @wraps(view_func)
    @login_required
    def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if not request.user.can_access_management():  # type: ignore[union-attr]
            return HttpResponseForbidden("Nincs jogosultsága ehhez a művelethez.")
        return view_func(request, *args, **kwargs)
    return wrapper


# ============ PUBLIC VIEWS ============

def home(request):
    """Homepage with featured movies and upcoming screenings"""
    movies = Movie.objects.filter(is_active=True).only(
        'id', 'title', 'genre', 'poster_url', 'duration_minutes', 'age_rating'
    )[:6]
    screenings = Screening.objects.filter(
        is_active=True,
        start_time__gt=timezone.now()
    ).select_related('movie', 'hall').annotate(
        _sold_count=Count('tickets', filter=Q(tickets__is_cancelled=False))
    ).order_by('start_time')[:10]
    
    return render(request, 'core/home.html', {
        'movies': movies,
        'screenings': screenings,
    })


def movie_list(request):
    """List all active movies - public view"""
    movies = Movie.objects.filter(is_active=True)
    return render(request, 'core/movie_list.html', {'movies': movies})


def movie_detail(request, pk):
    """Movie detail with its screenings - public view"""
    from datetime import datetime, timedelta as td
    movie = get_object_or_404(Movie, pk=pk, is_active=True)
    selected_date = request.GET.get('date', '')
    
    screenings_qs = movie.screenings.filter(
        is_active=True,
        start_time__gt=timezone.now()
    ).select_related('hall').annotate(
        _sold_count=Count('tickets', filter=Q(tickets__is_cancelled=False))
    ).order_by('start_time')
    
    if selected_date:
        try:
            day = datetime.strptime(selected_date, '%Y-%m-%d').date()
            screenings_qs = screenings_qs.filter(start_time__date=day)
        except ValueError:
            selected_date = ''
    
    today = timezone.now().date()
    day_choices = [(today + td(days=i)) for i in range(14)]
    
    paginator = Paginator(screenings_qs, 20)
    page = request.GET.get('page')
    screenings = paginator.get_page(page)
    
    return render(request, 'core/movie_detail.html', {
        'movie': movie,
        'screenings': screenings,
        'selected_date': selected_date,
        'day_choices': day_choices,
    })


def screening_list(request):
    """List all upcoming screenings - public view, with optional date filter"""
    from datetime import datetime, timedelta as td
    selected_date = request.GET.get('date', '')
    
    screenings_qs = Screening.objects.filter(
        is_active=True,
        start_time__gt=timezone.now()
    ).select_related('movie', 'hall').annotate(
        _sold_count=Count('tickets', filter=Q(tickets__is_cancelled=False))
    ).order_by('start_time')
    
    if selected_date:
        try:
            day = datetime.strptime(selected_date, '%Y-%m-%d').date()
            screenings_qs = screenings_qs.filter(
                start_time__date=day
            )
        except ValueError:
            selected_date = ''
    
    today = timezone.now().date()
    day_choices = [(today + td(days=i)) for i in range(14)]
    
    paginator = Paginator(screenings_qs, 20)
    page = request.GET.get('page')
    screenings = paginator.get_page(page)
    
    return render(request, 'core/screening_list.html', {
        'screenings': screenings,
        'selected_date': selected_date,
        'day_choices': day_choices,
    })


def screening_detail(request, pk):
    """Screening detail with seat availability - public view"""
    screening = get_object_or_404(
        Screening.objects.select_related('movie', 'hall'),
        pk=pk,
        is_active=True
    )
    
    sold_tickets = screening.tickets.filter(is_cancelled=False).values_list(
        'seat_row', 'seat_number'
    )
    sold_seats = set(sold_tickets)
    
    return render(request, 'core/screening_detail.html', {
        'screening': screening,
        'sold_seats': sold_seats,
    })


# ============ TICKET PURCHASE ============

def buy_ticket(request, pk):
    """Buy ticket(s) for a screening - supports multiple seat selection"""
    screening = get_object_or_404(Screening, pk=pk, is_active=True)
    
    if screening.is_past:
        messages.error(request, "Ez a vetítés már lezajlott.")
        return redirect('core:screening_list')
    
    if screening.is_sold_out:
        messages.error(request, "Ez a vetítés teltházas.")
        return redirect('core:movie_detail', pk=screening.movie.pk)
    
    if request.method == 'POST':
        seat_rows = request.POST.getlist('seat_rows')
        seat_numbers = request.POST.getlist('seat_numbers')
        
        if not seat_rows or not seat_numbers or len(seat_rows) != len(seat_numbers):
            messages.error(request, "Kérjük, válassz legalább egy széket.")
            return redirect('core:buy_ticket', pk=pk)
        
        if len(seat_rows) > 10:
            messages.error(request, "Egyszerre legfeljebb 10 jegyet vásárolhatsz.")
            return redirect('core:buy_ticket', pk=pk)
        
        seats = []
        for raw_row, raw_seat in zip(seat_rows, seat_numbers):
            try:
                row, seat_num = validate_seat(raw_row, raw_seat, screening.hall)
                seats.append((row, seat_num))
            except ValueError as e:
                messages.error(request, str(e))
                return redirect('core:buy_ticket', pk=pk)
        
        if len(seats) != len(set(seats)):
            messages.error(request, "Ugyanazt a széket nem választhatod ki kétszer.")
            return redirect('core:buy_ticket', pk=pk)
        
        guest_email = None
        guest_phone = None
        if not request.user.is_authenticated:
            try:
                guest_email = validate_email_input(request.POST.get('guest_email'))
                guest_phone = validate_phone_input(request.POST.get('guest_phone'))
            except ValueError as e:
                messages.error(request, str(e))
                return redirect('core:buy_ticket', pk=pk)
        
        created_tickets = []
        try:
            with transaction.atomic():
                for seat_row, seat_number in seats:
                    if Ticket.objects.select_for_update().filter(
                        screening=screening,
                        seat_row=seat_row,
                        seat_number=seat_number,
                        is_cancelled=False
                    ).exists():
                        messages.error(
                            request,
                            f"A(z) Sor {seat_row}, Szék {seat_number} már foglalt."
                        )
                        return redirect('core:buy_ticket', pk=pk)
                
                for seat_row, seat_number in seats:
                    ticket = Ticket(
                        screening=screening,
                        seat_row=seat_row,
                        seat_number=seat_number,
                    )
                    if request.user.is_authenticated:
                        ticket.user = request.user
                    else:
                        ticket.guest_email = guest_email
                        ticket.guest_phone = guest_phone
                    ticket.save()
                    created_tickets.append(ticket)
            
        except IntegrityError:
            messages.error(request, "A foglalás nem sikerült. Kérjük, próbálja újra.")
            security_logger.warning(
                f"IntegrityError during ticket purchase: screening={pk}"
            )
            return redirect('core:buy_ticket', pk=pk)
        
        _send_tickets_email(created_tickets)
        
        if len(created_tickets) == 1:
            messages.success(
                request,
                f"Sikeres jegyvásárlás! Jegykód: {created_tickets[0].ticket_code}"
            )
        else:
            codes = ', '.join(t.ticket_code for t in created_tickets)
            messages.success(
                request,
                f"Sikeres vásárlás! {len(created_tickets)} jegy megvásárolva. Kódok: {codes}"
            )
        
        if request.user.is_authenticated:
            return redirect('core:my_tickets')
        return redirect('core:home')
    
    sold_tickets = screening.tickets.filter(is_cancelled=False).values_list(
        'seat_row', 'seat_number'
    )
    sold_seats_list = [[r, s] for r, s in sold_tickets]
    
    return render(request, 'core/buy_ticket.html', {
        'screening': screening,
        'sold_seats_json': sold_seats_list,
    })


@login_required
def my_tickets(request):
    """View user's tickets - past and future"""
    tickets = request.user.tickets.filter(is_cancelled=False).select_related(
        'screening__movie', 'screening__hall'
    )
    
    now = timezone.now()
    future_tickets = [t for t in tickets if t.screening.start_time > now]
    past_tickets = [t for t in tickets if t.screening.start_time <= now]
    
    return render(request, 'core/my_tickets.html', {
        'future_tickets': future_tickets,
        'past_tickets': past_tickets,
    })


@require_POST
@login_required
def cancel_ticket(request, pk):
    """Cancel a ticket - must be at least 4 hours before screening"""
    ticket = get_object_or_404(Ticket, pk=pk, user=request.user)
    
    if not ticket.can_be_cancelled():
        messages.error(request, "A jegy már nem törölhető (kevesebb mint 4 óra van a vetítésig).")
        return redirect('core:my_tickets')
    
    ticket.is_cancelled = True
    ticket.save()
    security_logger.info(
        f"Ticket cancelled: ticket_id={pk}, user={request.user.pk}"
    )
    messages.success(request, "A jegy sikeresen törölve.")
    return redirect('core:my_tickets')


# ============ CASHIER VIEWS ============

@cashier_area_required
def cashier_dashboard(request):
    """Cashier dashboard"""
    today_screenings = Screening.objects.filter(
        is_active=True,
        start_time__date=timezone.now().date()
    ).select_related('movie', 'hall')
    
    return render(request, 'core/cashier/dashboard.html', {
        'screenings': today_screenings,
    })


@require_http_methods(["GET", "POST"])
@ticket_verifier_required
def verify_ticket(request, ticket_code):
    """Verify and validate a ticket"""
    clean_code = re.sub(r'[^A-Za-z0-9]', '', ticket_code).upper()
    if not clean_code:
        messages.error(request, "Érvénytelen jegykód.")
        return redirect('core:cashier_dashboard')
    
    ticket = get_object_or_404(Ticket, ticket_code=clean_code)
    
    if request.method == 'POST':
        if ticket.is_cancelled:
            messages.error(request, "Ez a jegy törölve lett.")
        elif ticket.is_verified:
            messages.warning(request, "Ez a jegy már ellenőrizve volt.")
        elif ticket.screening.is_past:
            messages.error(request, "A vetítés már lezajlott.")
        else:
            ticket.is_verified = True
            ticket.verified_by = request.user
            ticket.save()
            security_logger.info(
                f"Ticket verified: code={clean_code}, by={request.user.pk}"
            )
            messages.success(request, "Jegy sikeresen ellenőrizve!")
        
        return redirect('core:cashier_dashboard')
    
    return render(request, 'core/cashier/verify_ticket.html', {'ticket': ticket})


@require_http_methods(["GET", "POST"])
@cashier_required
def cashier_sell_ticket(request, screening_pk):
    """Cashier sells ticket(s) on behalf of customer - supports multiple seats"""
    screening = get_object_or_404(Screening, pk=screening_pk, is_active=True)
    
    if screening.is_past:
        messages.error(request, "Ez a vetítés már lezajlott.")
        return redirect('core:cashier_dashboard')
    
    if request.method == 'POST':
        seat_rows = request.POST.getlist('seat_rows')
        seat_numbers = request.POST.getlist('seat_numbers')
        
        if not seat_rows or not seat_numbers or len(seat_rows) != len(seat_numbers):
            messages.error(request, "Kérjük, válassz legalább egy széket.")
            return redirect('core:cashier_sell_ticket', screening_pk=screening_pk)
        
        if len(seat_rows) > 10:
            messages.error(request, "Egyszerre legfeljebb 10 jegyet adhatsz el.")
            return redirect('core:cashier_sell_ticket', screening_pk=screening_pk)
        
        seats = []
        for raw_row, raw_seat in zip(seat_rows, seat_numbers):
            try:
                row, seat_num = validate_seat(raw_row, raw_seat, screening.hall)
                seats.append((row, seat_num))
            except ValueError as e:
                messages.error(request, str(e))
                return redirect('core:cashier_sell_ticket', screening_pk=screening_pk)
        
        if len(seats) != len(set(seats)):
            messages.error(request, "Ugyanazt a széket nem választhatod ki kétszer.")
            return redirect('core:cashier_sell_ticket', screening_pk=screening_pk)
        
        guest_email = None
        guest_phone = None
        raw_email = request.POST.get('guest_email', '').strip()
        raw_phone = request.POST.get('guest_phone', '').strip()
        
        try:
            if raw_email:
                guest_email = validate_email_input(raw_email)
            if raw_phone:
                guest_phone = validate_phone_input(raw_phone)
        except ValueError as e:
            messages.error(request, str(e))
            return redirect('core:cashier_sell_ticket', screening_pk=screening_pk)
        
        created_tickets = []
        try:
            with transaction.atomic():
                for seat_row, seat_number in seats:
                    if Ticket.objects.select_for_update().filter(
                        screening=screening,
                        seat_row=seat_row,
                        seat_number=seat_number,
                        is_cancelled=False
                    ).exists():
                        messages.error(
                            request,
                            f"A(z) Sor {seat_row}, Szék {seat_number} már foglalt."
                        )
                        return redirect('core:cashier_sell_ticket', screening_pk=screening_pk)
                
                for seat_row, seat_number in seats:
                    ticket = Ticket.objects.create(
                        screening=screening,
                        seat_row=seat_row,
                        seat_number=seat_number,
                        guest_email=guest_email,
                        guest_phone=guest_phone,
                        sold_by=request.user,
                    )
                    created_tickets.append(ticket)
        except IntegrityError:
            messages.error(request, "A jegy kiadása nem sikerült. Kérjük, próbálja újra.")
            return redirect('core:cashier_sell_ticket', screening_pk=screening_pk)
        
        security_logger.info(
            f"Cashier sold {len(created_tickets)} ticket(s): "
            f"codes={[t.ticket_code for t in created_tickets]}, "
            f"cashier={request.user.pk}, screening={screening_pk}"
        )
        _send_tickets_email(created_tickets)
        
        if len(created_tickets) == 1:
            messages.success(request, f"Jegy eladva! Kód: {created_tickets[0].ticket_code}")
        else:
            codes = ', '.join(t.ticket_code for t in created_tickets)
            messages.success(request, f"{len(created_tickets)} jegy eladva! Kódok: {codes}")
        return redirect('core:cashier_dashboard')
    
    sold_tickets = screening.tickets.filter(is_cancelled=False).values_list(
        'seat_row', 'seat_number'
    )
    sold_seats_list = [[r, s] for r, s in sold_tickets]
    
    return render(request, 'core/cashier/sell_ticket.html', {
        'screening': screening,
        'sold_seats_json': sold_seats_list,
    })


# ============ ADMIN VIEWS ============

@management_required
def admin_dashboard(request):
    """Admin dashboard overview"""
    movies_count = Movie.objects.filter(is_active=True).count()
    screenings_count = Screening.objects.filter(
        is_active=True,
        start_time__gt=timezone.now()
    ).count()
    tickets_today = Ticket.objects.filter(
        purchase_date__date=timezone.now().date(),
        is_cancelled=False
    ).count()
    users_count = User.objects.count()
    
    return render(request, 'core/admin/dashboard.html', {
        'movies_count': movies_count,
        'screenings_count': screenings_count,
        'tickets_today': tickets_today,
        'users_count': users_count,
    })


@movie_manager_required
def admin_movie_list(request):
    """List all movies for admin"""
    movies = Movie.objects.all()
    return render(request, 'core/admin/movie_list.html', {'movies': movies})


@require_http_methods(["GET", "POST"])
@movie_manager_required
def admin_movie_add(request):
    """Add new movie"""
    if request.method == 'POST':
        try:
            title = sanitize_string(request.POST.get('title', ''), max_length=200)
            description = sanitize_string(request.POST.get('description', ''), max_length=5000)
            genre = sanitize_string(request.POST.get('genre', ''), max_length=100)
            director = sanitize_string(request.POST.get('director', ''), max_length=200)
            age_rating = sanitize_string(request.POST.get('age_rating', ''), max_length=50)
            duration_minutes = validate_positive_int(
                request.POST.get('duration_minutes'), field_name='Időtartam'
            )
        except ValueError as e:
            messages.error(request, str(e))
            return render(request, 'core/admin/movie_form.html', {'movie': None})
        
        if not title:
            messages.error(request, "A cím megadása kötelező.")
            return render(request, 'core/admin/movie_form.html', {'movie': None})
        
        release_date = request.POST.get('release_date') or None
        
        poster_url = request.POST.get('poster_url', '').strip()
        
        movie = Movie.objects.create(
            title=title,
            description=description,
            duration_minutes=duration_minutes,
            genre=genre,
            director=director,
            release_date=release_date,
            age_rating=age_rating,
            poster_url=poster_url,
        )
        
        security_logger.info(
            f"Movie added: id={movie.pk}, title={title}, by={request.user.pk}"
        )
        messages.success(request, "Film sikeresen hozzáadva!")
        return redirect('core:admin_movie_list')
    
    return render(request, 'core/admin/movie_form.html', {'movie': None})


@require_http_methods(["GET", "POST"])
@movie_manager_required
def admin_movie_edit(request, pk):
    """Edit existing movie"""
    movie = get_object_or_404(Movie, pk=pk)
    
    if request.method == 'POST':
        try:
            movie.title = sanitize_string(request.POST.get('title', ''), max_length=200)
            movie.description = sanitize_string(request.POST.get('description', ''), max_length=5000)
            movie.genre = sanitize_string(request.POST.get('genre', ''), max_length=100)
            movie.director = sanitize_string(request.POST.get('director', ''), max_length=200)
            movie.age_rating = sanitize_string(request.POST.get('age_rating', ''), max_length=50)
            movie.duration_minutes = validate_positive_int(
                request.POST.get('duration_minutes'), field_name='Időtartam'
            )
        except ValueError as e:
            messages.error(request, str(e))
            return render(request, 'core/admin/movie_form.html', {'movie': movie})
        
        if not movie.title:
            messages.error(request, "A cím megadása kötelező.")
            return render(request, 'core/admin/movie_form.html', {'movie': movie})
        
        movie.release_date = request.POST.get('release_date') or None
        movie.is_active = request.POST.get('is_active') == 'on'
        movie.poster_url = request.POST.get('poster_url', '').strip()
        
        movie.save()
        security_logger.info(
            f"Movie edited: id={pk}, by={request.user.pk}"
        )
        messages.success(request, "Film sikeresen módosítva!")
        return redirect('core:admin_movie_list')
    
    return render(request, 'core/admin/movie_form.html', {'movie': movie})


@require_POST
@movie_manager_required
def admin_movie_delete(request, pk):
    """Delete movie if no active screenings"""
    movie = get_object_or_404(Movie, pk=pk)
    
    if not movie.can_be_deleted():
        messages.error(request, "A film nem törölhető, mert aktív vetítések tartoznak hozzá.")
        return redirect('core:admin_movie_list')
    
    title = movie.title
    movie.delete()
    security_logger.info(
        f"Movie deleted: id={pk}, title={title}, by={request.user.pk}"
    )
    messages.success(request, "Film sikeresen törölve!")
    return redirect('core:admin_movie_list')


@screening_manager_required
def admin_screening_list(request):
    """List all screenings for admin"""
    screenings_qs = Screening.objects.select_related('movie', 'hall').annotate(
        _sold_count=Count('tickets', filter=Q(tickets__is_cancelled=False))
    ).order_by('-start_time')
    paginator = Paginator(screenings_qs, 30)
    page = request.GET.get('page')
    screenings = paginator.get_page(page)
    return render(request, 'core/admin/screening_list.html', {'screenings': screenings})


@require_http_methods(["GET", "POST"])
@screening_manager_required
def admin_screening_add(request):
    """Add new screening"""
    movies = Movie.objects.filter(is_active=True)
    halls = CinemaHall.objects.all()
    
    if request.method == 'POST':
        try:
            movie_id = validate_positive_int(request.POST.get('movie'), field_name='Film')
            hall_id = validate_positive_int(request.POST.get('hall'), field_name='Terem')
        except ValueError as e:
            messages.error(request, str(e))
            return render(request, 'core/admin/screening_form.html', {
                'screening': None, 'movies': movies, 'halls': halls,
            })
        
        start_time = request.POST.get('start_time', '').strip()
        ticket_price = request.POST.get('ticket_price', '').strip()
        
        if not start_time:
            messages.error(request, "A vetítés időpontja kötelező.")
            return render(request, 'core/admin/screening_form.html', {
                'screening': None, 'movies': movies, 'halls': halls,
            })
        
        movie = Movie.objects.filter(pk=movie_id, is_active=True).first()
        hall = CinemaHall.objects.filter(pk=hall_id).first()
        if not movie or not hall:
            messages.error(request, "Érvénytelen film vagy terem.")
            return render(request, 'core/admin/screening_form.html', {
                'screening': None, 'movies': movies, 'halls': halls,
            })
        
        try:
            screening = Screening.objects.create(
                movie=movie,
                hall=hall,
                start_time=start_time,
                ticket_price=ticket_price,
            )
        except (ValueError, IntegrityError) as e:
            messages.error(request, f"Hiba a vetítés létrehozásakor: {e}")
            return render(request, 'core/admin/screening_form.html', {
                'screening': None, 'movies': movies, 'halls': halls,
            })
        
        security_logger.info(
            f"Screening added: id={screening.pk}, movie={movie_id}, by={request.user.pk}"
        )
        messages.success(request, "Vetítés sikeresen létrehozva!")
        return redirect('core:admin_screening_list')
    
    return render(request, 'core/admin/screening_form.html', {
        'screening': None,
        'movies': movies,
        'halls': halls,
    })


@require_http_methods(["GET", "POST"])
@screening_manager_required
def admin_screening_edit(request, pk):
    """Edit existing screening"""
    screening = get_object_or_404(Screening, pk=pk)
    movies = Movie.objects.filter(is_active=True)
    halls = CinemaHall.objects.all()
    
    if request.method == 'POST':
        try:
            movie_id = validate_positive_int(request.POST.get('movie'), field_name='Film')
            hall_id = validate_positive_int(request.POST.get('hall'), field_name='Terem')
        except ValueError as e:
            messages.error(request, str(e))
            return render(request, 'core/admin/screening_form.html', {
                'screening': screening, 'movies': movies, 'halls': halls,
            })
        
        movie = Movie.objects.filter(pk=movie_id, is_active=True).first()
        hall = CinemaHall.objects.filter(pk=hall_id).first()
        if not movie or not hall:
            messages.error(request, "Érvénytelen film vagy terem.")
            return render(request, 'core/admin/screening_form.html', {
                'screening': screening, 'movies': movies, 'halls': halls,
            })
        
        screening.movie = movie
        screening.hall = hall
        screening.start_time = request.POST.get('start_time')
        screening.ticket_price = request.POST.get('ticket_price', '').strip()
        screening.is_active = request.POST.get('is_active') == 'on'
        
        try:
            screening.save()
        except (ValueError, IntegrityError) as e:
            messages.error(request, f"Hiba a vetítés módosításakor: {e}")
            return render(request, 'core/admin/screening_form.html', {
                'screening': screening, 'movies': movies, 'halls': halls,
            })
        
        security_logger.info(
            f"Screening edited: id={pk}, by={request.user.pk}"
        )
        messages.success(request, "Vetítés sikeresen módosítva!")
        return redirect('core:admin_screening_list')
    
    return render(request, 'core/admin/screening_form.html', {
        'screening': screening,
        'movies': movies,
        'halls': halls,
    })


# ============ USER MANAGEMENT ============

@admin_required
def admin_user_list(request):
    """List all users for admin management"""
    search = request.GET.get('q', '').strip()
    role_filter = request.GET.get('role', '')

    users = User.objects.all().order_by('username')
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    if role_filter:
        users = users.filter(role=role_filter)

    return render(request, 'core/admin/user_list.html', {
        'users': users,
        'search': search,
        'role_filter': role_filter,
        'roles': User.Role.choices,
    })


@require_http_methods(["GET", "POST"])
@admin_required
def admin_user_edit(request, pk):
    """Edit a user's role, active status, and individual permissions"""
    from django.contrib.auth.models import Permission
    target_user = get_object_or_404(User, pk=pk)

    custom_perms = Permission.objects.filter(
        codename__in=['manage_movies', 'manage_screenings', 'sell_tickets', 'verify_tickets']
    ).select_related('content_type')
    
    perm_labels = {
        'manage_movies': 'Filmek kezelése',
        'manage_screenings': 'Vetítések kezelése',
        'sell_tickets': 'Jegyek eladása (pénztár)',
        'verify_tickets': 'Jegyek ellenőrzése',
    }

    if request.method == 'POST':
        new_role = request.POST.get('role', '')
        is_active = request.POST.get('is_active') == 'on'

        if new_role not in dict(User.Role.choices):
            messages.error(request, "Érvénytelen szerepkör!")
            return redirect('core:admin_user_edit', pk=pk)

        if target_user == request.user and new_role != 'admin':
            messages.error(request, "Nem vonhatod meg a saját admin jogosultságod!")
            return redirect('core:admin_user_edit', pk=pk)

        old_role = target_user.role
        target_user.role = new_role
        target_user.is_active = is_active

        if new_role == 'admin':
            target_user.is_staff = True
            target_user.is_superuser = True
        elif new_role == 'cashier':
            target_user.is_staff = True
            target_user.is_superuser = False
        else:
            target_user.is_superuser = False

        target_user.save()

        selected_perms = request.POST.getlist('permissions')
        for perm in custom_perms:
            if perm.codename in selected_perms:
                target_user.user_permissions.add(perm)
            else:
                target_user.user_permissions.remove(perm)

        if new_role == 'customer' and target_user.user_permissions.exists():
            target_user.is_staff = True
            target_user.save(update_fields=['is_staff'])
        elif new_role == 'customer':
            target_user.is_staff = False
            target_user.save(update_fields=['is_staff'])

        security_logger.info(
            f"User updated: user={target_user.username}, "
            f"old_role={old_role}, new_role={new_role}, "
            f"permissions={selected_perms}, by={request.user.pk}"
        )
        messages.success(
            request,
            f"{target_user.username} jogosultságai módosítva!"
        )
        return redirect('core:admin_user_list')

    user_perm_codenames = set(
        target_user.user_permissions.values_list('codename', flat=True)
    )

    return render(request, 'core/admin/user_edit.html', {
        'target_user': target_user,
        'roles': User.Role.choices,
        'custom_perms': custom_perms,
        'perm_labels': perm_labels,
        'user_perm_codenames': user_perm_codenames,
    })


# ============ TICKET LOOKUP ============

def ticket_lookup(request):
    """Public ticket lookup by ticket code"""
    ticket = None
    searched = False
    ticket_code = request.GET.get('ticket_code', '').strip()
    
    if ticket_code:
        searched = True
        clean_code = re.sub(r'[^A-Za-z0-9]', '', ticket_code).upper()
        if clean_code:
            ticket = Ticket.objects.filter(ticket_code=clean_code).select_related(
                'screening__movie', 'screening__hall', 'user'
            ).first()
    
    return render(request, 'core/ticket_lookup.html', {
        'ticket': ticket,
        'searched': searched,
        'ticket_code': ticket_code,
    })


# ============ ERROR VIEWS ============

def csrf_failure(request, reason=""):
    """Custom CSRF failure view"""
    security_logger.warning(
        f"CSRF failure: reason={reason}, ip={request.META.get('REMOTE_ADDR')}, "
        f"path={request.path}"
    )
    return render(request, 'core/csrf_failure.html', status=403)
