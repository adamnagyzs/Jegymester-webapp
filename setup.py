"""
==========================================================
  Jegymester - Cinema Project Setup Script
==========================================================
  Automated setup for first-time installation.
  Run this once to get the project fully configured.

  Usage:
    python setup.py           (interactive mode)
    python setup.py --auto    (auto mode, skips prompts)
==========================================================
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
VENV_DIR = BASE_DIR / '.venv'
ENV_FILE = BASE_DIR / '.env'
ENV_EXAMPLE = BASE_DIR / '.env.example'
REQUIREMENTS = BASE_DIR / 'requirements.txt'
IS_WINDOWS = platform.system() == 'Windows'
PYTHON_CMD = sys.executable
AUTO_MODE = '--auto' in sys.argv




def header(text: str):
    """Print a formatted section header."""
    print(f'\n{"=" * 56}')
    print(f'  {text}')
    print(f'{"=" * 56}')


def step(text: str):
    """Print a step indicator."""
    print(f'\n→ {text}')


def success(text: str):
    print(f'  ✓ {text}')


def warn(text: str):
    print(f'  ⚠ {text}')


def error(text: str):
    print(f'  ✗ {text}')


def ask(question: str, default: str = 'y') -> bool:
    """Ask a yes/no question. In auto mode, always returns True."""
    if AUTO_MODE:
        return True
    hint = '[Y/n]' if default == 'y' else '[y/N]'
    answer = input(f'  {question} {hint}: ').strip().lower()
    if not answer:
        return default == 'y'
    return answer in ('y', 'yes', 'igen', 'i')


def run(cmd: list[str], cwd=None, check=True, env=None):
    """Run a subprocess command and return the result."""
    result = subprocess.run(
        cmd,
        cwd=cwd or BASE_DIR,
        capture_output=True,
        text=True,
        env=env,
    )
    if check and result.returncode != 0:
        error(f'Command failed: {" ".join(cmd)}')
        if result.stderr:
            print(f'    {result.stderr.strip()[:500]}')
        return None
    return result


def get_venv_python() -> str:
    """Return the path to the Python executable inside the venv."""
    if IS_WINDOWS:
        return str(VENV_DIR / 'Scripts' / 'python.exe')
    return str(VENV_DIR / 'bin' / 'python')


def get_venv_pip() -> str:
    """Return the path to pip inside the venv."""
    if IS_WINDOWS:
        return str(VENV_DIR / 'Scripts' / 'pip.exe')
    return str(VENV_DIR / 'bin' / 'pip')




def check_python():
    header('1/7 — Python verzió ellenőrzése')
    
    major, minor = sys.version_info[:2]
    version_str = f'{major}.{minor}.{sys.version_info.micro}'
    
    if major < 3 or (major == 3 and minor < 10):
        error(f'Python {version_str} — legalább 3.10 szükséges!')
        sys.exit(1)
    
    success(f'Python {version_str} — OK')
    return True




def setup_venv():
    header('2/7 — Virtuális környezet')
    
    if VENV_DIR.exists() and Path(get_venv_python()).exists():
        success(f'Virtuális környezet már létezik: {VENV_DIR}')
        return True
    
    step('Virtuális környezet létrehozása...')
    result = run([PYTHON_CMD, '-m', 'venv', str(VENV_DIR)])
    if result is None:
        error('Nem sikerült a virtuális környezet létrehozása!')
        sys.exit(1)
    
    success(f'Virtuális környezet létrehozva: {VENV_DIR}')
    return True




def install_dependencies():
    header('3/7 — Függőségek telepítése')
    
    if not REQUIREMENTS.exists():
        error(f'requirements.txt nem található: {REQUIREMENTS}')
        sys.exit(1)
    
    pip = get_venv_pip()
    python = get_venv_python()
    
    
    step('pip frissítése...')
    run([python, '-m', 'pip', 'install', '--upgrade', 'pip'], check=False)
    
    
    step('Csomagok telepítése (requirements.txt)...')
    result = run([pip, 'install', '-r', str(REQUIREMENTS)])
    if result is None:
        error('Függőségek telepítése sikertelen!')
        warn('Próbáld meg manuálisan: pip install -r requirements.txt')
        sys.exit(1)
    
    success('Minden függőség telepítve')
    return True




def setup_env():
    header('4/7 — Környezeti változók (.env)')
    
    if ENV_FILE.exists():
        success('.env fájl már létezik')
        if ask('Felül akarod írni a meglévő .env fájlt?', default='n'):
            _create_env_interactive()
        return True
    
    if AUTO_MODE:
        
        if ENV_EXAMPLE.exists():
            shutil.copy(ENV_EXAMPLE, ENV_FILE)
            success('.env fájl létrehozva .env.example alapján')
            warn('Ne feledd kitölteni a valós értékeket a .env fájlban!')
        else:
            _create_env_with_defaults()
        return True
    
    print()
    print('  A .env fájl tartalmazza az adatbázis és e-mail beállításokat.')
    print('  Most megadhatod az értékeket, vagy később szerkesztheted a fájlt.')
    print()
    
    if ask('Szeretnéd most interaktívan beállítani?'):
        _create_env_interactive()
    elif ENV_EXAMPLE.exists():
        shutil.copy(ENV_EXAMPLE, ENV_FILE)
        success('.env fájl létrehozva .env.example alapján')
        warn('Szerkeszd a .env fájlt a valós adatokkal!')
    else:
        _create_env_with_defaults()
    
    return True


def _create_env_interactive():
    """Interactively ask for .env values."""
    print()
    print('  ── Django beállítások ──')
    secret_key = input('  SECRET_KEY [Enter = automatikus generálás]: ').strip()
    if not secret_key:
        import secrets as _secrets
        secret_key = _secrets.token_urlsafe(50)
    
    debug = input('  DEBUG mód (True/False) [True]: ').strip() or 'True'
    
    print()
    print('  ── Adatbázis beállítások (MySQL) ──')
    db_host = input('  DB_HOST [localhost]: ').strip() or 'localhost'
    db_port = input('  DB_PORT [3306]: ').strip() or '3306'
    db_name = input('  DB_NAME [Jegymester]: ').strip() or 'Jegymester'
    db_user = input('  DB_USER [root]: ').strip() or 'root'
    db_password = input('  DB_PASSWORD: ').strip()
    
    print()
    print('  ── E-mail beállítások (Gmail SMTP) ──')
    email_user = input('  EMAIL_HOST_USER (Gmail cím) []: ').strip()
    email_pass = input('  EMAIL_HOST_PASSWORD (App Password) []: ').strip()
    
    env_content = f"""# ── Django ──
DJANGO_SECRET_KEY={secret_key}
DJANGO_DEBUG={debug}
ALLOWED_HOSTS=localhost,127.0.0.1

# ── Database (MySQL) ──
DB_ENGINE=django.db.backends.mysql
DB_NAME={db_name}
DB_USER={db_user}
DB_PASSWORD={db_password}
DB_HOST={db_host}
DB_PORT={db_port}

# ── Email (Gmail SMTP) ──
EMAIL_HOST_USER={email_user}
EMAIL_HOST_PASSWORD={email_pass}
"""
    ENV_FILE.write_text(env_content, encoding='utf-8')
    success('.env fájl létrehozva az megadott értékekkel')


def _create_env_with_defaults():
    """Create .env with placeholder defaults."""
    env_content = """# ── Django ──
DJANGO_SECRET_KEY=django-insecure-CHANGE-ME-IN-PRODUCTION
DJANGO_DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# ── Database (MySQL) ──
DB_ENGINE=django.db.backends.mysql
DB_NAME=Jegymester
DB_USER=root
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=3306

# ── Email (Gmail SMTP) ──
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
"""
    ENV_FILE.write_text(env_content, encoding='utf-8')
    success('.env fájl létrehozva alapértelmezett értékekkel')
    warn('Szerkeszd a .env fájlt a valós adatokkal!')




def run_migrations():
    header('5/7 — Adatbázis migrációk')
    
    python = get_venv_python()
    manage = str(BASE_DIR / 'manage.py')
    
    step('Migrációk futtatása...')
    result = run([python, manage, 'migrate'])
    if result is None:
        error('Migrációk futtatása sikertelen!')
        warn('Ellenőrizd a .env fájlban az adatbázis beállításokat.')
        return False
    
    
    if result.stdout:
        for line in result.stdout.strip().split('\n'):
            if 'Applying' in line or 'No migrations' in line:
                print(f'    {line.strip()}')
    
    success('Migrációk sikeresen lefutottak')
    return True




def load_initial_data():
    header('6/7 — Kezdeti adatok betöltése')
    
    python = get_venv_python()
    setup_script = BASE_DIR / 'setup_data.py'
    
    if not setup_script.exists():
        warn('setup_data.py nem található, kihagyva')
        return True
    
    if not AUTO_MODE and not ask('Betöltsük a minta adatokat (filmek, termek, vetítések)?'):
        warn('Minta adatok betöltése kihagyva')
        return True
    
    step('Minta adatok betöltése (setup_data.py)...')
    result = run([python, str(setup_script)])
    if result is None:
        error('Adatok betöltése sikertelen!')
        return False
    
    if result.stdout:
        for line in result.stdout.strip().split('\n'):
            print(f'    {line}')
    
    success('Kezdeti adatok betöltve')
    return True




def collect_static():
    header('7/7 — Statikus fájlok')
    
    python = get_venv_python()
    manage = str(BASE_DIR / 'manage.py')
    
    step('Statikus fájlok gyűjtése...')
    result = run([python, manage, 'collectstatic', '--noinput'])
    if result is None:
        warn('Statikus fájlok gyűjtése sikertelen (nem kritikus)')
        return True
    
    success('Statikus fájlok összegyűjtve')
    return True




def print_summary():
    header('TELEPÍTÉS KÉSZ!')
    
    print(f'''
  A projekt sikeresen be lett állítva.

  ── Indítás ────────────────────────────────────────''')
    
    if IS_WINDOWS:
        print(f'''
  1. Virtuális környezet aktiválása:
     .venv\\Scripts\\Activate.ps1

  2. Szerver indítása:
     python manage.py runserver''')
    else:
        print(f'''
  1. Virtuális környezet aktiválása:
     source .venv/bin/activate

  2. Szerver indítása:
     python manage.py runserver''')
    
    print(f'''
  3. Böngészőben:
     http://127.0.0.1:8000

  ── Felhasználók ──────────────────────────────────

  Admin:      admin / admin123
  Pénztáros:  penztar / penztar123
  Ügyfél:     felhasznalo / user123

  ── Hasznos parancsok ─────────────────────────────

  python manage.py createsuperuser   — Új admin felhasználó
  python manage.py migrate           — Migrációk futtatása
  python setup_data.py               — Minta adatok újratöltése
  python download_posters.py         — Film poszterek letöltése

{"=" * 56}
''')




def main():
    print(r'''
       ___                                     _            
      |_  |                                   | |           
        | | ___  __ _ _   _ _ __ ___   ___  ___| |_ ___ _ __ 
        | |/ _ \/ _` | | | | '_ ` _ \ / _ \/ __| __/ _ \ '__|
    /\__/ / (__| (_| | |_| | | | | | |  __/\__ \ ||  __/ |   
    \____/ \___|\__, |\__, |_| |_| |_|\___||___/\__\___|_|   
                 __/ | __/ |                                  
                |___/ |___/                                   
    
    Cinema Ticketing System — Project Setup
    ''')
    
    try:
        check_python()
        setup_venv()
        install_dependencies()
        setup_env()
        run_migrations()
        load_initial_data()
        collect_static()
        print_summary()
    except KeyboardInterrupt:
        print('\n\n  Telepítés megszakítva.')
        sys.exit(1)
    except Exception as e:
        error(f'Váratlan hiba: {e}')
        sys.exit(1)


if __name__ == '__main__':
    main()
