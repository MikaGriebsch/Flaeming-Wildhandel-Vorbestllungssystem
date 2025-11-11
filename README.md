# fwh-orders

## Fläming Wildhandel – Vorbestellungen

Diese Codebasis ist für das Vorbestell-System des Fläming Wildhandel optimiert. Wichtige Eckpunkte:

- Benutzerkonten basieren auf E-Mail-Adressen, die über django-allauth mit Double-Opt-In bestätigt werden müssen.
- Angebote begrenzen die Gesamtmenge sowie optional die Menge pro Nutzer, Überschreiten wird transaktional verhindert.
- Bestellungen sind verbindlich; Stornierungen durch Kund:innen sind nicht vorgesehen.
- Exportfunktionen (CSV, Excel, PDF) stehen über den normalen Django-Admin bereit und behalten die feste Spaltenreihenfolge bei.
- Erinnerungs-Mails (2 Tage vor Abholung sowie zum Start) werden über ein Cron-Command versendet und im E-Mail-Log protokolliert.

### Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r <(poetry export -f requirements.txt --without-hashes)
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Umgebungsvariablen

- `.env.example` kopieren und als `.env` ablegen.
- Wichtige Keys: `SECRET_KEY`, SMTP-Zugangsdaten, `DEFAULT_FROM_EMAIL`, `DEBUG`, `ALLOWED_HOSTS`.

### Cron & Erinnerungen

- Erinnerungen werden per `python manage.py crontab add` eingeplant.
- Der Cronjob führt täglich um 08:00 Uhr `python manage.py send_offer_reminders` aus.
- `python manage.py crontab show` listet aktive Jobs, `python manage.py crontab remove` entfernt sie wieder.

### Smoke-Test (Kurzfassung)

1. Registrieren und E-Mail bestätigen.
2. Als Admin ein Angebot anlegen (Limit + Zeitfenster).
3. Angebot im Frontend aufrufen, verbindlich bestellen.
4. Bestätigungs-Mail prüfen.
5. Im Admin die Exporte (CSV/Excel/PDF) anstoßen.
6. Cron-Command `send_offer_reminders` einmal manuell ausführen, um Log-Einträge zu sehen.

#### Django

This project serves as a base template for new Django projects using
[Poetry](https://github.com/sdispater/poetry) for dependency management. It comes preconfigured
with a robust set of third-party packages to help you start quickly and maintain best practices.

**Included Packages:**

```toml
[packages]
django = "*"
django-axes = "*"
django-compressor = "*"
django-extensions = "*"
django-kronos = "*"
django-post-office = "*"
django-secrets = "*"
django-tasks = "*"
djangorestframework = "*"
huepy = "*"
pendulum = "*"
Pillow = "*"
pypugjs = "*"
python = "*"
requests = "*"
sentry-sdk = "*"
whitenoise = "*"

[dev-packages]
django-browser-reload = "*"
django-debug-toolbar = "*"
fabric = "*"
icecream = "*"
ipdb = "*"
pre-commit = "*"
ruff = "*"
```

Furthermore, this template includes a Hello World example utilizing PUG templates, SASS styles, and
VueJS. The example even features [Chuck Norris facts](https://api.chucknorris.io) to provide a fun,
interactive experience during development.

#### Frontend

The frontend setup is minimal and designed to add reactivity to your pages without the overhead
of a full single-page application. It includes:

- [VueJS](https://vuejs.org/v2/guide/) – the core JavaScript framework.
- [Sentry](https://docs.sentry.io/quickstart/) – error reporting for the frontend.
- [Axios](https://github.com/axios/axios) – for AJAX calls.
- [Vuetify](https://vuetifyjs.com/en/) – a Material Design component framework for VueJS.
- [Material Design Icons](https://pictogrammers.com/library/mdi/) – iconography for your UI.

For more complex frontends, consider building a dedicated VueJS application (using `vue ui`) in
conjunction with Django REST Framework. But for smaller projects, this template provides a
lightweight solution that allows you to add interactivity without the need to deal with ~900
node dependencies.

#### Settings Hierarchy

This template features a simplified yet flexible settings hierarchy inspired by best practices
(e.g., *Two Scoops of Django*). The goal is to keep configuration clear and maintainable while
allowing easy customization for different environments or developers:

1. **Base Settings:**
All common configurations are located in a central file (`settings/common.py`). This file contains
settings shared by all environments.

2. **Environment-Specific Overrides:**
Create separate files for environment-specific settings (e.g., `settings/dev.py`,
`settings/prod.py`). Each of these files imports everything from `base.py` and then applies
overrides specific to that environment.

3. **Personalized Settings:**
Developers can maintain their own settings (e.g., `settings/alice.py`, `settings/bob.py`) based
on the default environment file. Simply set the environment variable `DJANGO_SETTINGS_MODULE`
to point to your custom settings (e.g., `export DJANGO_SETTINGS_MODULE=settings.alice`).

4. **Secret Management:**
With [django-secrets](https://github.com/jezdez/django-secrets), your sensitive configuration
(like API keys and passwords) is managed separately, ensuring that secrets remain secure and
deployment is streamlined (e.g., in CI/CD pipelines).

This flat yet modular approach minimizes complexity while allowing each project or developer to
tailor the settings as needed without interfering with the shared base configuration.

#### Clean Code

A pre-configured pre-commit hook is included to enforce code quality. Install it with:

```bash
pre-commit install
```

#### Static Files

The `wsgi.py` file has been updated to integrate
[Whitenoise](http://whitenoise.evans.io/en/stable/), so serving static files is handled
directly by Django without the need for an external server (unless desired).

#### fabfile

A ready-to-use `fabfile` is provided to simplify common deployment tasks:

- **fab deploy:** Pushes content, deploys static files and restarts the wsgi process.
- **fab migrate:** Additionally updates packages and applies database migrations,.

Enjoy building your project with this template—it’s designed to accelerate development while
keeping configurations clean and manageable.

## Installation

Ensure you have the required tools installed:

```bash
pip install django poetry  # if not already installed
```

For automatic virtual environment management, install [direnv](https://direnv.net/):

```bash
brew install direnv
```

To create a new project from this template:

```bash
django-admin startproject \
--template=https://github.com/kakulukia/django-default-project/zipball/master \
<new_project_name>
```

Then, navigate into your project:

```bash
cd <new_project_name>
direnv allow
poetry install
git init
pre-commit install
```

**Note:** This template uses Poetry for dependency management for now. Im planning to switch to
uv once this ticket is resolved: https://github.com/astral-sh/uv/issues/6794

After initial setup, customize your settings by copying one of the default environment files:

```bash
cp settings/mika.py settings/your_name.py
```

And set your environment variable to use your custom settings by default:

```bash
export DJANGO_SETTINGS_MODULE=settings.your_name
```

## 1st Time Deployment

**Required Components:**

- A recent Ubuntu (or similar) server distribution.
- **Nginx:**
    ```bash
    sudo apt install nginx
    ```
- **Node.js (latest LTS):**
    ```bash
    curl -fsSL https://fnm.vercel.app/install | bash

    fnm install --lts  # or the latest LTS version - used for pm2 and sass
    ```
- **pm2 (process manager for Node.js):**
    ```bash
    npm install -g pm2 sass
    ```
- Set up your project directory (e.g., under `/opt/www/<project_name>`):
    ```bash
    sudo mkdir -p /opt/www/<project_name>
    sudo chown -R $USER:$USER /opt/www/<project_name>
    cd /opt/www/<project_name>
    ```
- **Pyenv:** Install [pyenv](https://github.com/pyenv/pyenv) for Python version management:
    ```bash
    curl https://pyenv.run | bash
    ```
- **Build Requirements for Python:**
    ```bash
    sudo apt install -y make build-essential libssl-dev zlib1g-dev libbz2-dev \
    libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev \
    xz-utils tk-dev libffi-dev liblzma-dev python-openssl
    ```
- Install the required Python version and set it globally, then install Poetry:
    ```bash
    pyenv install 3.12.7
    pyenv global 3.12.7
    pip install -U pip setuptools poetry
    ```
- **Direnv Setup:**
    ```bash
    sudo apt install direnv
    ```
- Adjust the supplied Nginx configuration to your needs, link it to `sites-enabled`, and
restart Nginx:
    ```bash
    sudo ln -s /opt/www/<project>/settings/<your_config> /etc/nginx/sites-enabled/
    sudo systemctl restart nginx
    ```
- Run the local development server to initialize local secrets (e.g., `SECRET_KEY`, `OPEN_AI_API_KEY`):
    ```bash
    python manage.py runserver
    ```
- Test the uWSGI configuration:
    ```bash
    uwsgi settings/deployment/project.yml
    ```
- If everything works, start the pm2 job and set it to launch on startup:
    ```bash
    cd settings/deployment
    pm2 start project.sh
    pm2 save
    pm2 startup
    cd -
    ```
- Prepare Django static files:
    ```bash
    python manage.py compress -e pug,html --force
    python manage.py collectstatic --noinput
    ```

Your project should now be up and running. For deploying updates, you can use the provided fabfile.

- Optionally, deploy an SSL certificate via Certbot:
    ```bash
    sudo apt install certbot python3-certbot-nginx
    sudo certbot --nginx
    ```
