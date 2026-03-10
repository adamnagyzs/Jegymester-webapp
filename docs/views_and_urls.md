# Jegymester — Nézetek (Views) és URL-ek

## URL struktúra

Gyökér URL konfiguráció: `cinema_project/urls.py`
- `/admin/` → Django beépített admin
- `/accounts/` → django-allauth (login, signup, logout, jelszókezelés)
- `/` → `core.urls` (az alkalmazás fő útvonalai)

---

## Publikus nézetek (bejelentkezés nem szükséges)

| URL | Név | View | Leírás |
|---|---|---|---|
| `/` | `home` | `home()` | Főoldal — kiemelt filmek (max 6), közelgő vetítések (max 10) |
| `/movies/` | `movie_list` | `movie_list()` | Aktív filmek listája |
| `/movies/<id>/` | `movie_detail` | `movie_detail()` | Film részletei + jövőbeli vetítések (dátum szűrő, lapozás) |
| `/screenings/` | `screening_list` | `screening_list()` | Jövőbeli vetítések listája (dátum szűrő, lapozás) |
| `/screenings/<id>/` | `screening_detail` | `screening_detail()` | Vetítés részletei + ülőhelytérkép (foglalt/szabad székek) |
| `/ticket-lookup/` | `ticket_lookup` | `ticket_lookup()` | Jegy keresése kód alapján (publikus, GET paraméter) |

---

## Jegyvásárlás (vendég vagy bejelentkezett)

| URL | Név | View | Leírás |
|---|---|---|---|
| `/screenings/<id>/buy/` | `buy_ticket` | `buy_ticket()` | Jegyvásárlás — GET: ülőhelytérkép, POST: foglalás |

### Működés

1. **GET** — megjeleníti a termet, foglalt székeket JSON-nal adja át a sablonnak
2. **POST** — fogadja: `seat_rows[]`, `seat_numbers[]` (max 10 szék egyszerre)
3. Ha vendég: kell `guest_email` + `guest_phone`
4. Atomi tranzakció: `select_for_update()` a race condition megelőzésére
5. Siker után visszaigazoló e-mail küldés (`_send_tickets_email`)
6. Bejelentkezett → `/my-tickets/`, vendég → `/`

---

## Felhasználói jegykezelés (bejelentkezés szükséges)

| URL | Név | View | Leírás |
|---|---|---|---|
| `/my-tickets/` | `my_tickets` | `my_tickets()` | Saját jegyek (jövőbeli + múltbeli külön) |
| `/tickets/<id>/cancel/` | `cancel_ticket` | `cancel_ticket()` | Jegy törlése (POST, min. 4 óra a vetítés előtt) |

---

## Pénztáros nézetek

Hozzáférés: `can_sell_tickets()` vagy `can_verify_tickets()` jogosultság.

| URL | Név | View | Dekorátor | Leírás |
|---|---|---|---|---|
| `/cashier/` | `cashier_dashboard` | `cashier_dashboard()` | `@cashier_area_required` | Mai vetítések listája |
| `/cashier/verify/<code>/` | `verify_ticket` | `verify_ticket()` | `@ticket_verifier_required` | Jegy ellenőrzése kód alapján |
| `/cashier/sell/<id>/` | `cashier_sell_ticket` | `cashier_sell_ticket()` | `@cashier_required` | Jegy eladás ügyfél nevében |

### Jegyellenőrzés folyamata

1. GET — jegy adatainak megjelenítése
2. POST — ellenőrzés: nem törölve? nem korábbi? nem ellenőrizve már? → `is_verified = True`

### Pénztári eladás

- Ugyanaz, mint `buy_ticket`, de a `sold_by` mező kitöltődik a pénztárossal
- Vendég email/telefon opcionális

---

## Adminisztrátori nézetek

Hozzáférés: `admin` szerepkör vagy egyedi jogosultságok.

### Dashboard

| URL | Név | View | Dekorátor |
|---|---|---|---|
| `/management/` | `admin_dashboard` | `admin_dashboard()` | `@management_required` |

Megjelenít: aktív filmek száma, jövőbeli vetítések, mai jegyek, összes felhasználó.

### Film kezelés

| URL | Név | View | Dekorátor | HTTP |
|---|---|---|---|---|
| `/management/movies/` | `admin_movie_list` | `admin_movie_list()` | `@movie_manager_required` | GET |
| `/management/movies/add/` | `admin_movie_add` | `admin_movie_add()` | `@movie_manager_required` | GET/POST |
| `/management/movies/<id>/edit/` | `admin_movie_edit` | `admin_movie_edit()` | `@movie_manager_required` | GET/POST |
| `/management/movies/<id>/delete/` | `admin_movie_delete` | `admin_movie_delete()` | `@movie_manager_required` | POST |

- Törlés csak akkor, ha nincs aktív (jövőbeli) vetítés
- Input validáció: `sanitize_string()`, `validate_positive_int()`

### Vetítés kezelés

| URL | Név | View | Dekorátor | HTTP |
|---|---|---|---|---|
| `/management/screenings/` | `admin_screening_list` | `admin_screening_list()` | `@screening_manager_required` | GET |
| `/management/screenings/add/` | `admin_screening_add` | `admin_screening_add()` | `@screening_manager_required` | GET/POST |
| `/management/screenings/<id>/edit/` | `admin_screening_edit` | `admin_screening_edit()` | `@screening_manager_required` | GET/POST |

- Lapozás: 30 elemű oldalak
- Film és terem kiválasztása legördülő listából

### Felhasználó kezelés

| URL | Név | View | Dekorátor | HTTP |
|---|---|---|---|---|
| `/management/users/` | `admin_user_list` | `admin_user_list()` | `@admin_required` | GET |
| `/management/users/<id>/edit/` | `admin_user_edit` | `admin_user_edit()` | `@admin_required` | GET/POST |

- Keresés: felhasználónév, email, név alapján
- Szűrés: szerepkör alapján
- Szerkesztés: szerepkör, aktív állapot, egyedi jogosultságok
- Védelem: saját admin jog nem vonható meg

---

## Hibakezelés

| View | Leírás |
|---|---|
| `csrf_failure()` | Egyedi CSRF hiba oldal (403) — naplózza a biztonsági eseményt |

---

## Dekorátorok (core/views.py)

| Dekorátor | Ellenőrzés |
|---|---|
| `@cashier_required` | `can_sell_tickets()` |
| `@admin_required` | `is_admin_user` vagy `is_superuser` |
| `@movie_manager_required` | `can_manage_movies()` |
| `@screening_manager_required` | `can_manage_screenings()` |
| `@ticket_verifier_required` | `can_verify_tickets()` |
| `@cashier_area_required` | `can_access_cashier()` |
| `@management_required` | `can_access_management()` |

Mindegyik `@login_required`-et is tartalmaz. Sikertelen hozzáférés → HTTP 403.

---

## E-mail küldés

- **Jegyvásárlás visszaigazolás** — `_send_tickets_email()`: film, időpont, terem, szék, jegykód, összeg
- Egy jegy vagy több jegy (összesítve) is támogatott
- **Üdvözlő email** — `accounts/signals.py`: regisztráció után automatikusan
