# Jegymester — Modellek és adatbázis

## Áttekintés

Az alkalmazás 4 fő modellt használ a `core` appban, és 1 egyedi User modellt az `accounts` appban. Az adatbázis MySQL 8.0 (Aiven felhő), tesztekhez SQLite in-memory.

---

## User (accounts/models.py)

Egyedi felhasználó modell, az `AbstractUser`-ből származik.

| Mező | Típus | Leírás |
|---|---|---|
| `username` | CharField | Felhasználónév (Django alapértelmezett) |
| `email` | EmailField | E-mail cím |
| `role` | CharField (choices) | Szerepkör: `customer`, `cashier`, `admin` |
| `phone_number` | CharField | Telefonszám (opcionális) |
| `is_staff`, `is_superuser` | Boolean | Django belső jogosultságok |

### Szerepkörök (TextChoices)

| Érték | Magyar név | Jogosultságok |
|---|---|---|
| `customer` | Felhasználó | Böngészés, jegyvásárlás, saját jegyek |
| `cashier` | Pénztáros | + jegyeladás, jegyellenőrzés |
| `admin` | Adminisztrátor | + filmek, vetítések, felhasználók kezelése |

### Jogosultság-ellenőrző metódusok

- `is_customer` / `is_cashier` / `is_admin_user` — property-k
- `can_manage_movies()` — admin VAGY `core.manage_movies` permission
- `can_manage_screenings()` — admin VAGY `core.manage_screenings` permission
- `can_sell_tickets()` — cashier/admin VAGY `core.sell_tickets` permission
- `can_verify_tickets()` — cashier/admin VAGY `core.verify_tickets` permission
- `can_manage_users()` — csak admin
- `can_access_cashier()` — sell VAGY verify jog
- `can_access_management()` — admin VAGY manage_movies/manage_screenings jog

---

## Movie (core/models.py)

Film entitás — az adminisztrátorok kezelik.

| Mező | Típus | Leírás |
|---|---|---|
| `title` | CharField(200) | Film címe |
| `description` | TextField | Leírás |
| `duration_minutes` | PositiveIntegerField | Időtartam percben (min: 1) |
| `genre` | CharField(100) | Műfaj |
| `director` | CharField(200) | Rendező |
| `poster_url` | URLField(500) | Poszter URL (opcionális) |
| `release_date` | DateField | Megjelenés dátuma |
| `age_rating` | CharField(50) | Korhatár (opcionális) |
| `is_active` | BooleanField | Aktív-e (alapértelmezett: True) |
| `created_at` | DateTimeField | Létrehozás időpontja (auto) |
| `updated_at` | DateTimeField | Utolsó módosítás (auto) |

### Metódusok

- `has_active_screenings()` — van-e jövőbeli vetítése
- `can_be_deleted()` — törölhető-e (nincs aktív vetítés)

### Indexek

- `idx_movie_active_date` — `(is_active, -release_date)`
- `idx_movie_title` — `(title)`

### Egyedi jogosultság

- `manage_movies` — Filmek kezelése

---

## CinemaHall (core/models.py)

Moziterem — sorok × székek = kapacitás.

| Mező | Típus | Leírás |
|---|---|---|
| `name` | CharField(100) | Terem neve |
| `rows` | PositiveIntegerField | Sorok száma (1-100) |
| `seats_per_row` | PositiveIntegerField | Székek soronként (1-100) |
| `capacity` | PositiveIntegerField | Összkapacitás (automatikusan számolt, nem szerkeszthető) |

### Logika

A `save()` metódus automatikusan kiszámítja: `capacity = rows × seats_per_row`.

---

## Screening (core/models.py)

Vetítés — egy film egy teremben, adott időpontban.

| Mező | Típus | Leírás |
|---|---|---|
| `movie` | ForeignKey → Movie | Film (CASCADE) |
| `hall` | ForeignKey → CinemaHall | Terem (CASCADE) |
| `start_time` | DateTimeField | Kezdés időpontja |
| `ticket_price` | DecimalField(10,2) | Jegyár Ft-ban (min: 0) |
| `is_active` | BooleanField | Aktív-e |
| `created_at` | DateTimeField | Létrehozás (auto) |

### Property-k

- `end_time` — `start_time + duration_minutes`
- `available_seats` — szabad helyek száma (kapacitás - eladott jegyek)
- `is_sold_out` — teltházas-e
- `is_past` — elmúlt-e már a vetítés

### Indexek

- `idx_screening_active_time` — `(is_active, start_time)`
- `idx_screening_movie_time` — `(movie, is_active, start_time)`
- `idx_screening_hall_time` — `(hall, start_time)`
- `idx_screening_time` — `(start_time)`

### Egyedi jogosultság

- `manage_screenings` — Vetítések kezelése

---

## Ticket (core/models.py)

Jegy — egy vetítéshez, meghatározott székre.

| Mező | Típus | Leírás |
|---|---|---|
| `screening` | ForeignKey → Screening | Vetítés (CASCADE) |
| `user` | ForeignKey → User | Felhasználó (SET_NULL, opcionális) |
| `guest_email` | EmailField | Vendég e-mail (ha nem regisztrált) |
| `guest_phone` | CharField(20) | Vendég telefonszám (opcionális) |
| `seat_row` | PositiveIntegerField | Sor száma |
| `seat_number` | PositiveIntegerField | Szék száma |
| `purchase_date` | DateTimeField | Vásárlás dátuma (auto) |
| `is_cancelled` | BooleanField | Törölve-e |
| `is_verified` | BooleanField | Ellenőrizve-e (pénztárnál) |
| `verified_by` | ForeignKey → User | Ki ellenőrizte |
| `sold_by` | ForeignKey → User | Ki adta el (pénztáros) |
| `ticket_code` | CharField(20) | Egyedi jegykód (auto-generált, 10 karakter) |

### Kényszerek

- `unique_together`: `(screening, seat_row, seat_number)` — egy szék csak egyszer foglalható
- `ticket_code` egyedi

### Metódusok

- `can_be_cancelled()` — törölhető-e (min. 4 órával a vetítés előtt, nem törölve)
- `clean()` — validálja: van-e user VAGY guest_email; szék a terem határain belül van-e
- `save()` — automatikusan generál egyedi `ticket_code`-ot (10 alfanumerikus karakter, `secrets` modullal)

### Indexek

- `idx_ticket_screening_cancel` — `(screening, is_cancelled)`
- `idx_ticket_code` — `(ticket_code)`
- `idx_ticket_user_cancel` — `(user, is_cancelled)`
- `idx_ticket_purchase_date` — `(purchase_date)`

### Egyedi jogosultságok

- `sell_tickets` — Jegyek eladása (pénztár)
- `verify_tickets` — Jegyek ellenőrzése

---

## Kapcsolatok diagramja

```
User ──────┐
           │ 1:N
           ▼
Movie ◄─── Screening ──► CinemaHall
  1:N         │ 1:N          1:N
              ▼
           Ticket ──► User (user, verified_by, sold_by)
```

- Egy **Movie**-nak több **Screening**-je lehet
- Egy **CinemaHall**-nak több **Screening**-je lehet
- Egy **Screening**-nek több **Ticket**-je lehet
- Egy **Ticket** opcionálisan egy **User**-hez tartozik (vagy vendég adatok)
