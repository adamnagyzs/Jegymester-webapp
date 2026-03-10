# Jegymester — Fájl referencia

Minden fájl és mappáinak leírása a projektben.

---

## Gyökér könyvtár

| Fájl | Leírás |
|---|---|
| `manage.py` | Django parancssori segédprogram (migrate, runserver, test, stb.) |
| `setup.py` | Interaktív telepítő script — venv létrehozás, függőségek, .env, migrate, superuser |
| `setup_data.py` | Mintaadatok (filmek, termek, vetítések) betöltése az adatbázisba |
| `download_posters.py` | Film poszterek letöltése URL-ekről a `media/posters/` mappába |
| `start.bat` | Windows indító script — aktiválja a venv-et, migrate-el, majd `runserver` |
| `requirements.txt` | Python függőségek listája (`pip freeze` kimenet) |
| `SETUP.md` | Telepítési útmutató |
| `.env` | Környezeti változók (DB jelszó, secret key, email — **titkos**, gitignore-ban) |
| `.env.example` | Példa `.env` fájl — sablonként szolgál |
| `.gitignore` | Git által figyelmen kívül hagyott fájlok |

---

## cinema_project/ — Projekt konfiguráció

| Fájl | Leírás |
|---|---|
| `__init__.py` | Python csomag inicializáló |
| `settings.py` | **Fő beállítások** — DB konfig, middleware, template engine-ek, auth, session, CSRF, HTTPS, logging, email, i18n. Környezeti változókat `python-decouple`-ön keresztül olvassa. |
| `test_settings.py` | **Teszt beállítások** — `settings.py`-ból importál, felülírja: SQLite in-memory DB, MD5 hasher (gyorsabb tesztek), locmem email backend, whitenoise és bruteforce middleware kikapcsolva |
| `urls.py` | **Gyökér URL konfiguráció** — `/admin/` (beépített Django admin), `/accounts/` (allauth), `/` (core app). Django admin felület testreszabás (cím, fejléc). |
| `wsgi.py` | WSGI belépési pont (production deployment) |
| `asgi.py` | ASGI belépési pont (async deployment) |

---

## accounts/ — Felhasználókezelés app

| Fájl | Leírás |
|---|---|
| `__init__.py` | Python csomag inicializáló |
| `apps.py` | App konfiguráció — `ready()` metódusban importálja a `signals` modult |
| `models.py` | **Custom User modell** — `AbstractUser`-ből származik. Mezők: `role` (customer/cashier/admin), `phone_number`. Property-k: `is_customer`, `is_cashier`, `is_admin_user`. Metódusok: `can_manage_movies()`, `can_manage_screenings()`, `can_sell_tickets()`, `can_verify_tickets()`, `can_manage_users()`, `can_access_cashier()`, `can_access_management()`. |
| `admin.py` | **Django admin testreszabás** — `CustomUserAdmin` (164 sor): egyedi list_display (szerepkör badge, jegyszám, aktív badge), fieldset-ek, keresés, szűrők. Statisztikai annotációk, formázott HTML kimenet. |
| `adapter.py` | **Allauth adapter** — `CustomAccountAdapter`: regisztráció után üdvözlő üzenet, login/signup redirect → `/`. |
| `signals.py` | **Üdvözlő email** — `post_save` signal: új felhasználó létrehozásakor üdvözlő e-mailt küld Gmail SMTP-n keresztül. |
| `views.py` | Üres (az allauth kezeli az auth nézeteket) |
| `tests.py` | Üres stub — tesztek a `tests/` mappában |
| `migrations/` | Adatbázis migrációk (0001_initial: User tábla) |

---

## core/ — Fő üzleti logika app

| Fájl | Leírás |
|---|---|
| `__init__.py` | Python csomag inicializáló |
| `apps.py` | App konfiguráció |
| `models.py` | **Adatmodellek** (282 sor) — `Movie` (film, 16 mező), `CinemaHall` (terem, auto kapacitás), `Screening` (vetítés, property-k: end_time, available_seats, is_sold_out, is_past), `Ticket` (jegy, auto ticket_code generálás, seat validáció, 4 órás törlési deadline). Indexek és egyedi jogosultságok definiálva. |
| `views.py` | **Összes nézet** (1015 sor) — 7 publikus view, 2 felhasználói view, 3 pénztáros view, 10 admin view, 1 hibanézet, email küldés, 8 jogosultság-dekorátor. Atomi tranzakciók `select_for_update()`-tel, lapozás, annotációk a lekérdezés optimalizálásra. |
| `urls.py` | **URL útvonalak** (42 sor) — `app_name = 'core'`, 20 URL pattern: publikus (6), jegy (3), pénztár (3), admin (8). |
| `admin.py` | **Django admin testreszabás** (334 sor) — `MovieAdmin` (poszter preview, vetítések összesítés, inline Screening), `CinemaHallAdmin` (kapacitás kijelzés), `ScreeningAdmin` (foglaltsági %, szín kód, jövedelem kalkuláció, inline Ticket), `TicketAdmin` (státusz badge-ek, szűrők, export akciók). |
| `validators.py` | **Input validáció** (140 sor) — `sanitize_string()` (XSS védelem), `validate_seat()`, `validate_email_input()`, `validate_phone_input()`, `validate_positive_int()`, `validate_file_upload()` (méret, MIME, kiterjesztés). |
| `middleware.py` | **Biztonsági middleware** (142 sor) — `SecurityHeadersMiddleware` (CSP, Permissions-Policy, X-Content-Type-Options, Referrer-Policy), `BruteForceProtectionMiddleware` (IP-alapú rate limiting, 5 perces blokkolás). |
| `templatetags/cinema_tags.py` | **Egyedi template filter** — `to_range`: egész számot range listává alakít ülőhely megjelenítéshez. |
| `views.py` | Üres stub — tesztek a `tests/` mappában |
| `tests.py` | Üres stub — tesztek a `tests/` mappában |
| `migrations/` | Adatbázis migrációk (7 db: initial, age_rating, capacity, poster_url, indexes, meta options) |

---

## templates/ — HTML sablonok

### Alap

| Fájl | Leírás |
|---|---|
| `base.html` | **Alap layout** — Bootstrap 5 CDN, navigáció (szerepkör-függő menüpontok), üzenetek (messages framework), footer, CSRF token. Minden sablon ebből öröklődik. |

### account/ — Allauth sablonok

| Fájl | Leírás |
|---|---|
| `login.html` | Bejelentkezés űrlap |
| `signup.html` | Regisztrációs űrlap |
| `logout.html` | Kijelentkezés oldal |
| `password_change.html` | Jelszó módosítás |
| `password_reset.html` | Jelszó visszaállítás kérés |
| `password_reset_done.html` | Jelszó visszaállítás email elküldve |
| `password_reset_from_key.html` | Új jelszó megadás (linkből) |
| `password_reset_from_key_done.html` | Jelszó sikeresen visszaállítva |
| `email.html` | E-mail cím kezelés |
| `email_confirm.html` | E-mail megerősítés |
| `verification_sent.html` | Verifikációs email elküldve |

### core/ — Alkalmazás sablonok

| Fájl | Leírás |
|---|---|
| `home.html` | Főoldal — kiemelt filmek grid, közelgő vetítések lista |
| `movie_list.html` | Filmek listája kártyás elrendezésben |
| `movie_detail.html` | Film részletei — poszter, adatok, vetítések dátumszűrővel |
| `screening_list.html` | Vetítések listája — dátum gyorsgombok, film és terem info |
| `screening_detail.html` | Vetítés részletei — ülőhelytérkép (foglalt/szabad), vásárlás gomb |
| `buy_ticket.html` | Jegyvásárlás — interaktív ülőhelytérkép, szék kiválasztás, vendég űrlap |
| `my_tickets.html` | Saját jegyek — jövőbeli (törlés gombbal) és múltbeli külön |
| `ticket_lookup.html` | Jegy keresés — kód megadás, jegy adatok megjelenítés |
| `csrf_failure.html` | CSRF hiba egyedi oldal |

### core/cashier/ — Pénztáros sablonok

| Fájl | Leírás |
|---|---|
| `dashboard.html` | Pénztáros dashboard — mai vetítések, gyors hozzáférés |
| `sell_ticket.html` | Jegy eladás — ülőhelytérkép + vendég adatok |
| `verify_ticket.html` | Jegy ellenőrzés — jegy adatok, érvényesítés gomb |

### core/admin/ — Admin sablonok

| Fájl | Leírás |
|---|---|
| `dashboard.html` | Admin dashboard — statisztikák (filmek, vetítések, jegyek, felhasználók) |
| `movie_list.html` | Filmek kezelése — lista, szerkesztés/törlés gombok |
| `movie_form.html` | Film hozzáadás/szerkesztés űrlap |
| `screening_list.html` | Vetítések kezelése — lapozás, szerkesztés gombok |
| `screening_form.html` | Vetítés hozzáadás/szerkesztés űrlap |
| `user_list.html` | Felhasználók kezelése — keresés, szűrés, szerkesztés |
| `user_edit.html` | Felhasználó szerkesztés — szerepkör, jogosultságok, aktív állapot |

---

## static/ — Statikus fájlok

| Fájl | Leírás |
|---|---|
| `css/style.css` | Egyedi stílusok — Bootstrap 5 kiegészítés |

---

## media/ — Feltöltött fájlok

| Mappa | Leírás |
|---|---|
| `posters/` | Film poszter képek |

---

## tests/ — Tesztek (180 db)

| Fájl | Tesztek | Leírás |
|---|---|---|
| `__init__.py` | — | Csomag inicializáló |
| `test_accounts.py` | 32 | User modell, szerepkörök, jogosultság metódusok, signal tesztek |
| `test_models.py` | 29 | Movie, CinemaHall, Screening, Ticket modell tesztek |
| `test_validators.py` | 26 | Input validáció és template tag tesztek |
| `test_views.py` | 38 | Publikus nézetek, jegyvásárlás, jegykezelés, email tesztek |
| `test_cashier.py` | 14 | Pénztáros dashboard, jegyellenőrzés, jegyeladás tesztek |
| `test_admin.py` | 30 | Admin dashboard, film/vetítés CRUD, felhasználókezelés tesztek |
| `test_middleware.py` | 4 | Security headers middleware tesztek |
| `test_urls.py` | 11 | URL routing tesztek |

Futtatás: `python manage.py test tests --settings=cinema_project.test_settings`

---

## docs/ — Dokumentáció

| Fájl | Leírás |
|---|---|
| `architecture.md` | Architektúra áttekintés, tech stack, folyamat |
| `models.md` | Modellek és adatbázis séma |
| `views_and_urls.md` | Nézetek, URL-ek, dekorátorok |
| `security_and_permissions.md` | Biztonság, jogosultságok, middleware |
| `file_reference.md` | Ez a fájl — minden fájl leírása |
