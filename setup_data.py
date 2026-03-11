"""
Initial data setup script for Cinema Project
Creates admin user, cinema halls, sample movies, and screenings
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cinema_project.settings')
django.setup()

from django.utils import timezone
from datetime import timedelta
from accounts.models import User
from core.models import Movie, CinemaHall, Screening

# Set admin password and make it admin role
print("Setting up admin user...")
admin, created = User.objects.get_or_create(
    username='admin',
    defaults={
        'email': 'admin@cinema.hu',
        'role': 'admin',
        'is_staff': True,
        'is_superuser': True,
    }
)
admin.set_password('admin123')
admin.role = 'admin'
admin.is_staff = True
admin.is_superuser = True
admin.save()
print(f"✓ Admin user configured (username: admin, password: admin123)")

# Create cashier user
print("\nCreating cashier user...")
cashier, created = User.objects.get_or_create(
    username='penztar',
    defaults={
        'email': 'penztar@cinema.hu',
        'role': 'cashier',
    }
)
if created:
    cashier.set_password('penztar123')
    cashier.save()
    print(f"✓ Cashier user created (username: penztar, password: penztar123)")
else:
    print(f"✓ Cashier user already exists")

# Create test customer
print("\nCreating test customer...")
customer, created = User.objects.get_or_create(
    username='felhasznalo',
    defaults={
        'email': 'felhasznalo@email.hu',
        'role': 'customer',
        'phone_number': '+36301234567',
    }
)
if created:
    customer.set_password('user123')
    customer.save()
    print(f"✓ Customer user created (username: felhasznalo, password: user123)")
else:
    print(f"✓ Customer user already exists")

# Create Cinema Halls
print("\nCreating cinema halls...")
halls_data = [
    {'name': 'Nagyterem', 'rows': 10, 'seats_per_row': 15},
    {'name': 'Kisterem', 'rows': 6, 'seats_per_row': 10},
    {'name': 'VIP Terem', 'rows': 5, 'seats_per_row': 6},
]

for hall_data in halls_data:
    hall, created = CinemaHall.objects.get_or_create(
        name=hall_data['name'],
        defaults=hall_data
    )
    if not created:
        hall.rows = hall_data['rows']
        hall.seats_per_row = hall_data['seats_per_row']
        hall.save()
    status = "created" if created else "updated"
    print(f"✓ {hall.name} ({hall.rows}×{hall.seats_per_row} = {hall.capacity} seats) - {status}")

# Create Movies
print("\nCreating movies...")
movies_data = [
    {
        'title': 'A Keresztapa',
        'description': 'Az olasz-amerikai Corleone család történetét bemutató klasszikus bűnügyi dráma. Don Vito Corleone, a Keresztapa, a New York-i alvilág egyik leghatalmasabb maffiafőnöke. A film a család hatalmi harcait és belső konfliktusait mutatja be.',
        'duration_minutes': 175,
        'genre': 'Dráma/Krimi',
        'director': 'Francis Ford Coppola',
        'release_date': '1972-03-24',
        'age_rating': '18+',
        'poster_url': 'https://m.media-amazon.com/images/M/MV5BM2MyNjYxNmUtYTAwNi00MTYxLWJmNWYtYzZlODY3ZTk3OTFlXkEyXkFqcGdeQXVyNzkwMjQ5NzM@._V1_SX300.jpg',
    },
    {
        'title': 'Csillagok Háborúja: Egy Új Remény',
        'description': 'Egy messzi-messzi galaxisban Luke Skywalker egy fiatal farmerfiú, aki kalandos utazásra indul, hogy megmentse Leia hercegnőt a gonosz Galaktikus Birodalom fogságából.',
        'duration_minutes': 121,
        'genre': 'Sci-Fi/Kaland',
        'director': 'George Lucas',
        'release_date': '1977-05-25',
        'age_rating': '12+',
        'poster_url': 'https://m.media-amazon.com/images/M/MV5BOTA5NjhiOTAtZWM0ZC00MWNhLThiMzEtZDFkOTk2OTU1ZDJkXkEyXkFqcGdeQXVyMTA4NDI1NTQx._V1_SX300.jpg',
    },
    {
        'title': 'Eredet',
        'description': 'Dom Cobb egy tehetséges tolvaj, aki az álommegosztás művészetének mestere. Utolsó munkája során nem ellopni, hanem beültetni kell egy ötletet valaki elméjébe.',
        'duration_minutes': 148,
        'genre': 'Sci-Fi/Thriller',
        'director': 'Christopher Nolan',
        'release_date': '2010-07-16',
        'age_rating': '16+',
        'poster_url': 'https://m.media-amazon.com/images/M/MV5BMjAxMzY3NjcxNF5BMl5BanBnXkFtZTcwNTI5OTM0Mw@@._V1_SX300.jpg',
    },
    {
        'title': 'A Sötét Lovag',
        'description': 'Batman szembenéz a káosz megtestesítőjével, a Jokerrel, aki Gotham városát terrorral fenyegeti. Christian Bale és Heath Ledger emlékezetes alakítása.',
        'duration_minutes': 152,
        'genre': 'Akció/Dráma',
        'director': 'Christopher Nolan',
        'release_date': '2008-07-18',
        'age_rating': '16+',
        'poster_url': 'https://m.media-amazon.com/images/M/MV5BMTMxNTMwODM0NF5BMl5BanBnXkFtZTcwODAyMTk2Mw@@._V1_SX300.jpg',
    },
    {
        'title': 'Toy Story 4',
        'description': 'Woody és barátai új kalandba keverednek, amikor Forky, az új játék eltűnik. A csapatnak össze kell fognia, hogy megmentsék a kis villát.',
        'duration_minutes': 100,
        'genre': 'Animáció/Kaland',
        'director': 'Josh Cooley',
        'release_date': '2019-06-21',
        'age_rating': 'Korhatár nélkül',
        'poster_url': 'https://m.media-amazon.com/images/M/MV5BMTYzMDM4NzkxOV5BMl5BanBnXkFtZTgwNzM1Mzg2NzM@._V1_SX300.jpg',
    },
    {
        'title': 'Dűne',
        'description': 'Paul Atreides, egy briliáns és tehetséges fiatalember, aki a képzeletét meghaladó sorsra született. Az univerzum legveszélyesebb bolygójára kell utaznia.',
        'duration_minutes': 155,
        'genre': 'Sci-Fi/Dráma',
        'director': 'Denis Villeneuve',
        'release_date': '2021-10-22',
        'age_rating': '12+',
        'poster_url': 'https://m.media-amazon.com/images/M/MV5BMDQ0NjgyN2YtNWViNS00YjA3LTkxNDktYzFkZTExZGMxZDkxXkEyXkFqcGdeQXVyODE5NzE3OTE@._V1_SX300.jpg',
    },
]

for movie_data in movies_data:
    movie, created = Movie.objects.get_or_create(
        title=movie_data['title'],
        defaults=movie_data
    )
    status = "created" if created else "exists"
    print(f"✓ {movie.title} ({movie.duration_minutes} min) - {status}")

# Create Screenings — spread across the whole year, varied start times
print("\nCreating screenings...")
# Remove all past screenings (that have no sold tickets)
from django.db.models import Count
past = Screening.objects.filter(start_time__lt=timezone.now())
past_empty = past.annotate(ticket_count=Count('tickets')).filter(ticket_count=0)
deleted_count = past_empty.delete()[0]
if deleted_count:
    print(f"  Cleaned up {deleted_count} past empty screenings")

now = timezone.now()
halls = list(CinemaHall.objects.all())
movies = list(Movie.objects.all())

# Varied time slots — different start minutes so screenings don't all begin on the hour
time_slots = [
    (10, 0),   # 10:00
    (11, 30),  # 11:30
    (13, 15),  # 13:15
    (14, 45),  # 14:45
    (16, 0),   # 16:00
    (17, 30),  # 17:30
    (19, 0),   # 19:00
    (20, 45),  # 20:45
]
prices = [1500, 1800, 2000, 2200, 2500, 2800]

# Collect existing screening keys to avoid duplicates
existing = set(
    Screening.objects.values_list('movie_id', 'hall_id', 'start_time')
)

total_days = 365
new_screenings = []

for day_offset in range(total_days):
    day_start = (now + timedelta(days=day_offset)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    # Number of screenings varies by day of week
    weekday = day_start.weekday()
    if weekday in (4, 5, 6):  # Fri/Sat/Sun — more screenings
        slots_today = 5
    elif weekday in (0, 3):   # Mon/Thu
        slots_today = 4
    else:                     # Tue/Wed
        slots_today = 3

    slot_offset = day_offset % len(time_slots)

    for slot_idx in range(slots_today):
        slot = time_slots[(slot_offset + slot_idx) % len(time_slots)]
        movie = movies[(day_offset + slot_idx) % len(movies)]
        hall = halls[(day_offset + slot_idx) % len(halls)]
        price = prices[(day_offset + slot_idx) % len(prices)]
        screening_time = day_start.replace(hour=slot[0], minute=slot[1])

        if screening_time <= now:
            continue

        key = (movie.pk, hall.pk, screening_time)
        if key in existing:
            continue

        existing.add(key)
        new_screenings.append(Screening(
            movie=movie,
            hall=hall,
            start_time=screening_time,
            ticket_price=price,
            is_active=True,
        ))

# Bulk create in batches — much faster than individual inserts
batch_size = 200
for i in range(0, len(new_screenings), batch_size):
    Screening.objects.bulk_create(new_screenings[i:i + batch_size], ignore_conflicts=True)

print(f"  ✓ {len(new_screenings)} new screenings created across {total_days} days")
print(f"  Total screenings in database: {Screening.objects.count()}")

print(f"\n{'='*50}")
print("✓ Setup complete!")
print(f"{'='*50}")
print(f"\nUsers:")
print(f"  Admin:    username=admin, password=admin123")
print(f"  Cashier:  username=penztar, password=penztar123")
print(f"  Customer: username=felhasznalo, password=user123")
print(f"\nData created:")
print(f"  - {CinemaHall.objects.count()} cinema halls")
print(f"  - {Movie.objects.count()} movies")
print(f"  - {Screening.objects.count()} screenings")
