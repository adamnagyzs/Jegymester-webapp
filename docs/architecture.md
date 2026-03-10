# Jegymester — Architektúra áttekintés

## Mi ez az alkalmazás?

A **Jegymester** egy Django-alapú online mozijegy-értékesítő és vetítéskezelő platform. A felhasználók filmeket böngészhetnek, vetítéseket nézhetnek meg, jegyeket vásárolhatnak (bejelentkezve vagy vendégként), a pénztárosok jegyeket adhatnak el és ellenőrizhetnek, az adminisztrátorok pedig filmeket, vetítéseket és felhasználókat kezelhetnek.

---

## Technológiai stack

| Réteg | Technológia |
|---|---|
| Backend keretrendszer | Django 6.0 |
| Adatbázis | MySQL 8.0 (Aiven felhő), tesztekhez SQLite in-memory |
| Autentikáció | django-allauth (email + jelszó) |
| Űrlapok | django-crispy-forms + crispy-bootstrap5 |
| Template engine | Django Templates (+ django-jinja .jinja2 támogatás) |
| Statikus fájlok | WhiteNoise |
| Konfiguráció | python-decouple (`.env` fájl) |
| E-mail | Gmail SMTP |
| Nyelv | Python 3.10+ |

---

## Projekt struktúra

```
Rendszerfejlesztés/
│
├── cinema_project/          # Django projekt konfiguráció
│   ├── settings.py          # Fő beállítások
│   ├── test_settings.py     # Teszt beállítások (SQLite)
│   ├── urls.py              # Gyökér URL konfiguráció
│   ├── wsgi.py              # WSGI belépési pont
│   └── asgi.py              # ASGI belépési pont
│
├── accounts/                # Felhasználókezelés app
│   ├── models.py            # Custom User modell (szerepkörökkel)
│   ├── admin.py             # Django admin regisztráció
│   ├── adapter.py           # Allauth adapter testreszabás
│   ├── signals.py           # Üdvözlő email küldés regisztrációkor
│   └── apps.py              # App konfiguráció
│
├── core/                    # Fő üzleti logika app
│   ├── models.py            # Movie, CinemaHall, Screening, Ticket
│   ├── views.py             # Összes nézet (publikus, pénztár, admin)
│   ├── urls.py              # URL útvonalak
│   ├── admin.py             # Django admin testreszabás
│   ├── validators.py        # Input validáció és tisztítás
│   ├── middleware.py         # Biztonsági fejlécek, brute-force védelem
│   └── templatetags/
│       └── cinema_tags.py   # Egyedi template szűrők
│
├── templates/               # HTML sablonok
│   ├── base.html            # Alap layout
│   ├── account/             # Allauth sablonok (login, signup, stb.)
│   └── core/                # Alkalmazás sablonok
│       ├── home.html
│       ├── movie_list.html / movie_detail.html
│       ├── screening_list.html / screening_detail.html
│       ├── buy_ticket.html / my_tickets.html
│       ├── ticket_lookup.html
│       ├── cashier/         # Pénztáros nézetek
│       └── admin/           # Adminisztrátori nézetek
│
├── static/css/style.css     # Egyedi stílusok
├── media/posters/           # Feltöltött poszterek
├── tests/                   # Tesztek (180 db)
│
├── manage.py                # Django CLI
├── setup.py                 # Automatikus telepítő script
├── setup_data.py            # Mintaadatok betöltése
├── download_posters.py      # Film poszterek letöltése
├── start.bat                # Indító script (Windows)
├── requirements.txt         # Python függőségek
└── .env                     # Környezeti változók (titkos)
```

---

## Az alkalmazás folyamata

```
Felhasználó (böngésző)
        │
        ▼
  Django URL Router (cinema_project/urls.py → core/urls.py)
        │
        ▼
  Middleware lánc
  ├── SecurityHeadersMiddleware (CSP, Referrer-Policy, stb.)
  ├── BruteForceProtectionMiddleware (rate limiting)
  └── Django alapértelmezett middleware-ek
        │
        ▼
  View függvények (core/views.py)
  ├── Publikus nézetek (home, movie_list, screening_list, stb.)
  ├── Jegyvásárlás (buy_ticket – vendég vagy bejelentkezett)
  ├── Pénztáros nézetek (cashier_dashboard, verify_ticket, sell_ticket)
  └── Admin nézetek (dashboard, film/vetítés/felhasználó kezelés)
        │
        ▼
  Modellek (core/models.py, accounts/models.py)
        │
        ▼
  MySQL adatbázis
```

---

## Három szerepkör

| Szerepkör | Hozzáférés |
|---|---|
| **Customer** (Felhasználó) | Filmek böngészése, jegyvásárlás, saját jegyek kezelése |
| **Cashier** (Pénztáros) | Jegyeladás, jegyellenőrzés, pénztáros dashboard |
| **Admin** (Adminisztrátor) | Minden + filmek/vetítések/felhasználók kezelése |

Az egyedi jogosultságok (`manage_movies`, `manage_screenings`, `sell_tickets`, `verify_tickets`) szerepkörtől függetlenül is kioszthatók.

---

## Biztonság

- **CSP fejlécek** – SecurityHeadersMiddleware
- **Brute-force védelem** – IP-alapú rate limiting érzékeny végpontokra
- **CSRF védelem** – session-alapú token, egyedi hibaoldal
- **Input validáció** – központosított `validators.py` (XSS, SQL injection megelőzés)
- **HTTPS kényszerítés** – production módban HSTS + SSL redirect
- **Session biztonság** – HttpOnly, Secure, SameSite cookie-k
