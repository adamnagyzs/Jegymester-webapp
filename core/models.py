from __future__ import annotations  

from typing import Any  
from django.db import models  
from django.conf import settings  
from django.core.validators import MinValueValidator, MaxValueValidator  
from django.core.exceptions import ValidationError  
from django.utils import timezone  
from datetime import timedelta  
import secrets  
import string  


class Movie(models.Model):  
    """Film model - managed by administrators"""
    
    title = models.CharField(max_length=200, verbose_name='Cím')  
    description = models.TextField(verbose_name='Leírás')  
    duration_minutes = models.PositiveIntegerField(  
        verbose_name='Időtartam (perc)',  
        validators=[MinValueValidator(1)]  
    )
    genre = models.CharField(max_length=100, verbose_name='Műfaj') 
    director = models.CharField(max_length=200, verbose_name='Rendező')  
    poster_url = models.URLField(  
        max_length=500,  
        blank=True,  
        default='',  
        verbose_name='Poszter URL'  
    )
    release_date = models.DateField(verbose_name='Megjelenés dátuma')  
    age_rating = models.CharField(  
        max_length=50,  
        blank=True,  
        verbose_name='Korhatár'  
    )
    is_active = models.BooleanField(default=True, verbose_name='Aktív')  
    created_at = models.DateTimeField(auto_now_add=True)  
    updated_at = models.DateTimeField(auto_now=True)  
    
    class Meta:  
        verbose_name = 'Film'  
        verbose_name_plural = 'Filmek'  
        ordering = ['-release_date']  
        permissions = [  
            ('manage_movies', 'Filmek kezelése'), 
        ]
        indexes = [  
            models.Index(fields=['is_active', '-release_date'], name='idx_movie_active_date'),  
            models.Index(fields=['title'], name='idx_movie_title'),  
        ]
    
    def __str__(self):  
        return self.title  
    
    def has_active_screenings(self) -> bool:  
        """Check if movie has any future screenings"""
        return self.screenings.filter(start_time__gt=timezone.now()).exists()  
    
    def can_be_deleted(self) -> bool:  
        """Movie can only be deleted if no active screenings exist"""
        return not self.has_active_screenings()  


class CinemaHall(models.Model):  
    """Cinema hall/theater room"""
    
    name = models.CharField(max_length=100, verbose_name='Terem neve') 
    capacity = models.PositiveIntegerField(  
        verbose_name='Férőhelyek száma',  
        validators=[MinValueValidator(1), MaxValueValidator(1000)], 
        editable=False,  
    )
    rows = models.PositiveIntegerField(  
        verbose_name='Sorok száma',  
        validators=[MinValueValidator(1), MaxValueValidator(100)] 
    )
    seats_per_row = models.PositiveIntegerField(  
        verbose_name='Székek soronként', 
        validators=[MinValueValidator(1), MaxValueValidator(100)]  
    )
    
    class Meta:  
        verbose_name = 'Moziterem'  
        verbose_name_plural = 'Mozitermek'  
    
    def __str__(self):  
        return f"{self.name} ({self.capacity} férőhely)"  
    
    def save(self, *args: Any, **kwargs: Any) -> None:  
        self.capacity = self.rows * self.seats_per_row  
        super().save(*args, **kwargs)  


class Screening(models.Model):  
    """Movie screening/showing"""
    
    movie = models.ForeignKey(  
        Movie,  
        on_delete=models.CASCADE,  
        related_name='screenings',  
        verbose_name='Film'  
    )
    hall = models.ForeignKey(  
        CinemaHall,  
        on_delete=models.CASCADE,  
        related_name='screenings',  
        verbose_name='Terem'  
    )
    start_time = models.DateTimeField(verbose_name='Kezdés időpontja')  
    ticket_price = models.DecimalField(  
        max_digits=10,  
        decimal_places=2,  
        verbose_name='Jegyár (Ft)',  
        validators=[MinValueValidator(0)]  
    )
    is_active = models.BooleanField(default=True, verbose_name='Aktív') 
    created_at = models.DateTimeField(auto_now_add=True) 
    
    class Meta:  
        verbose_name = 'Vetítés'  
        verbose_name_plural = 'Vetítések'  
        ordering = ['start_time']  
        permissions = [  
            ('manage_screenings', 'Vetítések kezelése'), 
        ]
        indexes = [  
            models.Index(fields=['is_active', 'start_time'], name='idx_screening_active_time'), 
            models.Index(fields=['movie', 'is_active', 'start_time'], name='idx_screening_movie_time'),  
            models.Index(fields=['hall', 'start_time'], name='idx_screening_hall_time'),  
            models.Index(fields=['start_time'], name='idx_screening_time'),  
        ]
    
    def __str__(self):  
        return f"{self.movie.title} - {self.start_time.strftime('%Y.%m.%d %H:%M')} ({self.hall.name})"  
    
    @property  
    def end_time(self):  
        return self.start_time + timedelta(minutes=self.movie.duration_minutes)  
    
    @property  
    def available_seats(self) -> int:  
        if hasattr(self, '_sold_count'): 
            return self.hall.capacity - self._sold_count  
        sold_tickets: int = self.tickets.filter(is_cancelled=False).count()  
        return self.hall.capacity - sold_tickets  
    
    @property  
    def is_sold_out(self) -> bool:  
        return self.available_seats <= 0  
    @property  
    def is_past(self) -> bool:  
        return self.start_time < timezone.now()  


class Ticket(models.Model):  
    """Ticket for a screening"""
    
    screening = models.ForeignKey(  
        Screening,  
        on_delete=models.CASCADE,  
        related_name='tickets',  
        verbose_name='Vetítés' 
    )
    user = models.ForeignKey( 
        settings.AUTH_USER_MODEL,  
        on_delete=models.SET_NULL,  
        null=True,  
        blank=True, 
        related_name='tickets',  
        verbose_name='Felhasználó' 
    )
    guest_email = models.EmailField(  
        blank=True,  
        null=True,  
        verbose_name='Vendég e-mail'  
    )
    guest_phone = models.CharField(  
        max_length=20, 
        blank=True,  
        null=True,  
        verbose_name='Vendég telefonszám'  
    )
    
    seat_row = models.PositiveIntegerField(verbose_name='Sor')  
    seat_number = models.PositiveIntegerField(verbose_name='Szék')  
    
    purchase_date = models.DateTimeField(auto_now_add=True, verbose_name='Vásárlás dátuma')  
    is_cancelled = models.BooleanField(default=False, verbose_name='Törölve')  
    is_verified = models.BooleanField(default=False, verbose_name='Ellenőrizve') 
    verified_by = models.ForeignKey(  
        settings.AUTH_USER_MODEL,  
        on_delete=models.SET_NULL,  
        null=True,  
        blank=True, 
        related_name='verified_tickets',  
        verbose_name='Ellenőrizte'  
    )
    
    sold_by = models.ForeignKey(  
        settings.AUTH_USER_MODEL,  
        on_delete=models.SET_NULL,  
        null=True,  
        blank=True,  
        related_name='sold_tickets',  
        verbose_name='Eladta'  
    )
    
    ticket_code = models.CharField( 
        max_length=20,  
        unique=True,  
        verbose_name='Jegykód'  
    )
    
    class Meta:  
        verbose_name = 'Jegy'  
        verbose_name_plural = 'Jegyek'  
        unique_together = ['screening', 'seat_row', 'seat_number'] 
        ordering = ['-purchase_date'] 
        permissions = [  
            ('sell_tickets', 'Jegyek eladása (pénztár)'),  
            ('verify_tickets', 'Jegyek ellenőrzése'),  
        ]
        indexes = [  
            models.Index(fields=['screening', 'is_cancelled'], name='idx_ticket_screening_cancel'),  
            models.Index(fields=['ticket_code'], name='idx_ticket_code'),  
            models.Index(fields=['user', 'is_cancelled'], name='idx_ticket_user_cancel'),  
            models.Index(fields=['purchase_date'], name='idx_ticket_purchase_date'),  
        ]
    
    def __str__(self):  
        return f"Jegy: {self.ticket_code} - {self.screening}"  
    
    def can_be_cancelled(self) -> bool:  
        """
        Tickets can only be cancelled at least 4 hours before screening
        """
        cancellation_deadline = self.screening.start_time - timedelta(hours=4)  
        return timezone.now() < cancellation_deadline and not self.is_cancelled  
    
    def clean(self) -> None:  
        """Validate ticket data before saving"""
        super().clean()  
        if not self.user and not self.guest_email:  
            raise ValidationError(  
                "Vagy bejelentkezett felhasználó, vagy vendég e-mail szükséges."  
            )

        if self.screening_id: 
            hall = self.screening.hall  
            if self.seat_row < 1 or self.seat_row > hall.rows:  
                raise ValidationError(  
                    f"Érvénytelen sorszám: {self.seat_row}. Érvényes: 1-{hall.rows}"  
                )
            if self.seat_number < 1 or self.seat_number > hall.seats_per_row:  
                raise ValidationError(  
                    f"Érvénytelen székszám: {self.seat_number}. Érvényes: 1-{hall.seats_per_row}"  
                )
    
    @staticmethod  
    def _generate_ticket_code(length: int = 10) -> str:  
        """Generate a cryptographically secure, unique ticket code"""
        alphabet = string.ascii_uppercase + string.digits  
        return ''.join(secrets.choice(alphabet) for _ in range(length))  
    
    def save(self, *args: Any, **kwargs: Any) -> None:  
        if not self.ticket_code:  
            for _ in range(10): 
                code = self._generate_ticket_code()  
                if not Ticket.objects.filter(ticket_code=code).exists():  
                    self.ticket_code = code  
                    break  
            else:  
                raise RuntimeError("Nem sikerült egyedi jegykódot generálni.")  
        super().save(*args, **kwargs)  
