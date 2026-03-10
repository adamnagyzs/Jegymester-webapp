# Jegymester — Biztonság és jogosultságok

## Autentikáció

Az alkalmazás a **django-allauth** csomagot használja az autentikációhoz.

### Bejelentkezés

- Felhasználónév VAGY e-mail + jelszó
- URL: `/accounts/login/`
- Sikeres bejelentkezés után: `/` (főoldal) — az `CustomAccountAdapter` irányít

### Regisztráció

- Kötelező: e-mail, felhasználónév, jelszó (kétszer)
- URL: `/accounts/signup/`
- Sikeres regisztráció: üdvözlő üzenet + üdvözlő e-mail (`signals.py`)
- Alapértelmezett szerepkör: `customer`
- E-mail verifikáció: kikapcsolva (`ACCOUNT_EMAIL_VERIFICATION = 'none'`)

### Jelszókövetelmények

- Min. 8 karakter
- Nem hasonlíthat a felhasználó adataihoz
- Nem lehet túl gyakori jelszó
- Nem lehet csak szám

### Session kezelés

| Beállítás | Érték |
|---|---|
| `SESSION_COOKIE_HTTPONLY` | True — JS nem fér hozzá |
| `SESSION_COOKIE_SECURE` | True (production) — csak HTTPS |
| `SESSION_COOKIE_SAMESITE` | Lax |
| `SESSION_COOKIE_AGE` | 86400 (24 óra) |
| `SESSION_SAVE_EVERY_REQUEST` | True — frissít minden kérésnél |

---

## Szerepkör-alapú hozzáférés (RBAC)

### Három szerepkör

| Szerepkör | `role` érték | `is_staff` | `is_superuser` |
|---|---|---|---|
| Felhasználó | `customer` | False* | False |
| Pénztáros | `cashier` | True | False |
| Adminisztrátor | `admin` | True | True |

*Ha a customer-nek egyedi jogosultságokat adnak, `is_staff` True-ra áll.

### Hozzáférési mátrix

| Funkció | Customer | Cashier | Admin |
|---|---|---|---|
| Filmek böngészése | ✅ | ✅ | ✅ |
| Jegyvásárlás (online) | ✅ | ✅ | ✅ |
| Saját jegyek kezelése | ✅ | ✅ | ✅ |
| Pénztáros dashboard | ❌ | ✅ | ✅ |
| Jegy eladás (pénztár) | ❌ | ✅ | ✅ |
| Jegy ellenőrzés | ❌ | ✅ | ✅ |
| Admin dashboard | ❌ | ❌ | ✅ |
| Filmek kezelése | ❌ | ❌ | ✅ |
| Vetítések kezelése | ❌ | ❌ | ✅ |
| Felhasználók kezelése | ❌ | ❌ | ✅ |

---

## Egyedi (granulált) jogosultságok

A `core` modellekhez tartozó egyedi Django permission-ök, amelyek szerepkörtől függetlenül is kioszthatók:

| Jogosultság | Codename | Leírás |
|---|---|---|
| Filmek kezelése | `manage_movies` | Film CRUD műveletek |
| Vetítések kezelése | `manage_screenings` | Vetítés CRUD műveletek |
| Jegyek eladása | `sell_tickets` | Pénztári jegyeladás |
| Jegyek ellenőrzése | `verify_tickets` | Jegyellenőrzés |

### Példa: Customer + `manage_movies`

Egy customer, akinek kiosztják a `manage_movies` jogot:
- Elérhet a `/management/movies/` oldalakra
- Tud filmeket hozzáadni, szerkeszteni, törölni
- NEM érheti el a vetítés- vagy felhasználókezelést

### Hogyan működik?

A `User` modell `can_*` metódusai ellenőrzik:
```python
def can_manage_movies(self):
    return self.is_admin_user or self.is_superuser or self.has_perm('core.manage_movies')
```

A view dekorátorok ezeket hívják (pl. `@movie_manager_required`).

---

## Biztonsági middleware

### SecurityHeadersMiddleware (`core/middleware.py`)

Minden válaszhoz hozzáadja:

| Fejléc | Érték | Cél |
|---|---|---|
| `Content-Security-Policy` | `default-src 'self'; script-src 'self' 'unsafe-inline' cdn.jsdelivr.net; ...` | XSS megelőzés |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=(), ...` | Funkciók korlátozása |
| `X-Content-Type-Options` | `nosniff` | MIME type sniffing megelőzés |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Referrer adatok korlátozása |

### BruteForceProtectionMiddleware (`core/middleware.py`)

IP-alapú rate limiting POST kérésekre:

| Végpont | Limit | Ablak |
|---|---|---|
| `/accounts/login/` | 10 próbálkozás | 60 másodperc |
| `/accounts/signup/` | 10 próbálkozás | 60 másodperc |
| Jegyvásárlás | 20 próbálkozás | 60 másodperc |

Blokkolás időtartama: **5 perc** a limit túllépése után.

---

## CSRF védelem

| Beállítás | Érték |
|---|---|
| `CSRF_COOKIE_HTTPONLY` | True |
| `CSRF_COOKIE_SECURE` | True (production) |
| `CSRF_USE_SESSIONS` | True — token session-ben tárolva |
| `CSRF_FAILURE_VIEW` | `core.views.csrf_failure` — egyedi hibaoldal |

---

## Input validáció (`core/validators.py`)

Központosított validációs felület — minden felhasználói input ezen megy át.

| Függvény | Feladat |
|---|---|
| `sanitize_string(value, max_length)` | HTML tag eltávolítás, null byte eltávolítás, hossz korlátozás |
| `validate_seat(row, seat, hall)` | Szék koordináta ellenőrzés a terem méretei alapján |
| `validate_email_input(email)` | E-mail formátum validáció |
| `validate_phone_input(phone)` | Telefonszám formátum (7-15 számjegy, +, -, szóköz engedélyezett) |
| `validate_positive_int(value, field_name)` | Pozitív egész szám ellenőrzés |
| `validate_file_upload(file, max_size, extensions)` | Fájl méret, kiterjesztés, MIME type ellenőrzés |

---

## HTTPS és production biztonság

Production módban (`DEBUG = False`):

- `SECURE_SSL_REDIRECT = True` — HTTP → HTTPS átirányítás
- `SECURE_HSTS_SECONDS = 31536000` — 1 éves HSTS
- `SECURE_HSTS_INCLUDE_SUBDOMAINS = True`
- `SECURE_HSTS_PRELOAD = True`

---

## Naplózás

Biztonsági események a `security.log` fájlba kerülnek:

- CSRF hibák
- Jegy törlések
- Film CRUD műveletek
- Felhasználó módosítások
- Pénztári eladások
- Brute-force blokkolások
