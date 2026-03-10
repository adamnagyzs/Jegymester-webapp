# Jegymester — Cinema Ticketing System

Online mozi jegyértékesítő és vetítéskezelő rendszer Django alapokon.

---

## Követelmények

| Szoftver | Verzió |
|----------|--------|
| Python   | 3.10+  |
| MySQL    | 8.0+   |
| Git      | bármely |

---

## Gyors telepítés (automatikus)

```bash
git clone <repo-url>
cd Rendszerfejlesztés
python setup.py
```

A `setup.py` interaktívan végigvezet a teljes telepítésen. Ha nem akarsz kérdésekre válaszolni:

```bash
python setup.py --auto
```

---

## Manuális telepítés

### 1. Virtuális környezet létrehozása

```bash
python -m venv .venv
```

Aktiválás:

| Platform | Parancs |
|----------|---------|
| Windows (PowerShell) | `.venv\Scripts\Activate.ps1` |
| Windows (CMD) | `.venv\Scripts\activate.bat` |
| Linux / macOS | `source .venv/bin/activate` |

### 2. Függőségek telepítése

```bash
pip install -r requirements.txt
```

### 3. Környezeti változók beállítása

Másold a `.env.example` fájlt `.env` néven, és töltsd ki a valós értékekkel:

```bash
cp .env.example .env
```

A `.env` fájl tartalma:

```env
# Django
DJANGO_SECRET_KEY=<titkos-kulcs>
DJANGO_DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Adatbázis (MySQL)
DB_ENGINE=django.db.backends.mysql
DB_NAME=Jegymester
DB_USER=<felhasználónév>
DB_PASSWORD=<jelszó>
DB_HOST=<host>
DB_PORT=3306

# E-mail (Gmail SMTP)
EMAIL_HOST_USER=<gmail-cím>
EMAIL_HOST_PASSWORD=<gmail-app-password>
```

> **Megjegyzés:** Gmail küldéshez [App Password](https://myaccount.google.com/apppasswords) szükséges, nem a sima jelszó.

### 4. Adatbázis migrációk

```bash
python manage.py migrate
```

### 5. Minta adatok betöltése

```bash
python setup_data.py
```

Ez létrehozza a tesztfelhasználókat, moziterm eket, filmeket és vetítéseket.

### 6. Statikus fájlok gyűjtése

```bash
python manage.py collectstatic --noinput
```

### 7. Szerver indítása

```bash
python manage.py runserver
```

Ezután a böngészőben: **http://127.0.0.1:8000**

---

## Alapértelmezett felhasználók

| Szerepkör | Felhasználónév | Jelszó |
|-----------|---------------|--------|
| Admin | `admin` | `admin123` |
| Pénztáros | `penztar` | `penztar123` |
| Ügyfél | `felhasznalo` | `user123` |

---

## Projekt struktúra

```
├── cinema_project/     # Django projekt beállítások
│   ├── settings.py     # Fő konfigurációs fájl
│   ├── urls.py         # Gyökér URL-ek
│   └── wsgi.py / asgi.py
│
├── accounts/           # Felhasználókezelés (regisztráció, belépés, szerepkörök)
│   ├── models.py       # Custom User model (Customer/Cashier/Admin)
│   ├── adapter.py      # Allauth adapter (egyedi üzenetek)
│   └── signals.py      # Üdvözlő e-mail regisztrációkor
│
├── core/               # Fő alkalmazás (filmek, vetítések, jegyek)
│   ├── models.py       # Movie, CinemaHall, Screening, Ticket
│   ├── views.py        # Összes nézet (vásárlás, admin, pénztár)
│   ├── urls.py         # Alkalmazás URL-ek
│   ├── validators.py   # Egyedi validátorok
│   └── middleware.py    # Biztonsági middleware-ek
│
├── templates/          # HTML sablonok
│   ├── base.html       # Alaplap (navbar, CSS, JS)
│   ├── account/        # Regisztráció, belépés, jelszókezelés
│   └── core/           # Filmek, vetítések, jegyvásárlás, admin
│
├── static/css/         # CSS fájlok
├── media/posters/      # Film poszterek
│
├── setup.py            # Automatikus telepítő script
├── setup_data.py       # Minta adatok betöltése
├── download_posters.py # Film poszterek letöltése
├── requirements.txt    # Python függőségek
├── .env.example        # Környezeti változók sablon
└── manage.py           # Django CLI
```

---

## Funkciók

- **Filmek böngészése** — korhatár, műfaj, leírás, poszter
- **Vetítések listázása** — szűrés film és dátum szerint
- **Online jegyvásárlás** — vizuális ülésválasztó (max 10 hely egyszerre)
- **E-mail visszaigazolás** — jegyvásárláskor és regisztrációkor
- **Jegy keresés** — jegyazonosító alapján
- **Pénztáros felület** — jegyeladás, jegyellenőrzés
- **Admin felület** — filmek és vetítések kezelése (CRUD)
- **Szerepkör-alapú hozzáférés** — Ügyfél / Pénztáros / Admin

---

## Technológiák

| Komponens | Technológia |
|-----------|-------------|
| Backend | Django 6.0 |
| Adatbázis | MySQL (Aiven Cloud) |
| Autentikáció | django-allauth |
| Frontend | Bootstrap 5, Bootstrap Icons |
| E-mail | Gmail SMTP (TLS) |
| Statikus fájlok | WhiteNoise |
| Konfiguráció | python-decouple (.env) |

---

## Hasznos parancsok

```bash

python manage.py createsuperuser


python manage.py migrate


python setup_data.py


python download_posters.py


python manage.py shell
```
