# seznamovak-be

Backend for Seznamovák UTB, the freshers' camp of Univerzita Tomáše Bati in Zlín (site: seznamovak.utb.cz). Students book a place in one of two camp batches (turnusy) through a public form. When a batch is full they become substitutes and move up automatically when someone cancels. The service sends the confirmation, substitute, cancel and payment e-mails. Staff manage reservations in the Django admin: mark payments, cancel, check the numbers and export a PDF list per batch.

It is a Django rewrite of the old Laravel backend, with the same public API paths and JSON. The `seznamovak-fe` frontend calls this API on its own origin, `https://seznamovak.utb.cz/api`.

## Stack

- Python 3.12, Django 5.1 (below 6), Django REST Framework
- Auth: `djangorestframework-simplejwt` (JWT in httpOnly cookies), token blacklist for logout
- `django-cors-headers`, `dj-database-url`, `httpx` (Brevo newsletter call)
- `reportlab` (PDF list), `qrcode` + `pillow` (payment QR codes, photo validation)
- PostgreSQL 16 (driver `psycopg`)
- `gunicorn` (3 workers) + WhiteNoise for static files
- Docker Compose, dependencies managed with `uv` (`ruff` and `mypy` as dev tools)

## Project structure

```
seznamovak-be/
├── docker-compose.yml      db (Postgres) + web (Django)
├── Makefile                shortcuts for docker compose
├── .env.example            all settings
└── api/
    ├── Dockerfile
    ├── pyproject.toml, uv.lock
    ├── manage.py
    ├── config/             settings.py, urls.py, wsgi.py
    ├── common/             exceptions (error mapping), API-language middleware, BaseRepository
    └── apps/
        ├── user/           staff account model, login/refresh/logout/me, cookie JWT auth
        ├── faculties/      Faculty model and reference data
        └── reservations/   Batch, Reservation, BillingInformation; public API, e-mails, QR, PDF, stats, Brevo, seed_data
```

Inside an app the layers are: controller (DRF `ViewSet`, only HTTP) → service (business rules, transactions) → repository (the only place that uses `Model.objects`) → model. Request and response shapes are serializers in `dtos.py`. Services are plain classes wired together in `services/__init__.py`. The Django admin calls the same services.

## Requirements

- Docker with Compose v2
- `make` (optional; on Windows use Git Bash)
- `uv` (only for `make lint`)

## Run locally

```bash
cp .env.example .env
```

Change these lines in `.env`:

```
DJANGO_DEBUG=true
DJANGO_ALLOWED_HOSTS=*
DJANGO_USE_HTTPS=false
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

- `DJANGO_ALLOWED_HOSTS` must include `localhost`, otherwise Django rejects the request.
- `DJANGO_USE_HTTPS=false` is needed because the session, CSRF and login cookies are marked `Secure` otherwise and the browser drops them on plain http.
- The console e-mail backend prints e-mails to the web container log (`make logs`).
- Without `DJANGO_DEBUG=true` the app needs a real `DJANGO_SECRET_KEY` (it refuses to start with the default dev key).

Start and create an admin user:

```bash
make up                 # same as: docker compose up -d --build
make superuser          # same as: docker compose exec web python manage.py createsuperuser
```

- API: http://localhost:8002/api/reservations (port is `WEB_PORT`)
- Admin: http://localhost:8002/admin/

On every start the web container runs, in this order (compose `command`):

1. `collectstatic --noinput` (static files for WhiteNoise)
2. `migrate`
3. `seed_data`
4. `gunicorn config.wsgi` on port 8000 with 3 workers

`seed_data` creates the reference data only if it is missing, so it is safe to run repeatedly:

- 6 faculties with fixed ids: FT, FAME, FMK, FAI, FHS, FLKŘ (the public form posts these ids)
- 2 batches, 100 places each: batch 1 on 17-20 Aug 2026, batch 2 on 24-27 Aug 2026; registration opens 20 Jul 2026 15:00 and closes 24 Aug 2026 15:00 (Europe/Prague)

Existing batches are not changed by `seed_data`. Edit dates, capacity and the registration window in the admin. The dates above are hard-coded for 2026, so for another year change them in the admin (or in `api/apps/reservations/services/batches.py` before the first start).

## Make commands

| Command | What it does |
| --- | --- |
| `make up` | `docker compose up -d --build` (build and start in the background) |
| `make down` | Stop and remove the containers (volumes stay) |
| `make ps` | Show container status |
| `make logs` | Follow the web container log |
| `make psql` | Open `psql` in the db container |
| `make shell` | Django shell in the web container |
| `make migrate` | Run migrations |
| `make seed` | Run `seed_data` |
| `make superuser` | Create an admin user |
| `make lint` | `ruff check` and `mypy` (runs on the host with `uv`, in `api/`) |

## Configuration

All settings come from `.env` (read by compose and passed to the web container).

### Django

| Variable | Default in `.env.example` | What it does |
| --- | --- | --- |
| `DJANGO_DEBUG` | `false` | `true` turns on debug mode and allows the built-in dev secret key |
| `DJANGO_SECRET_KEY` | `change-me-to-a-long-random-string` | Django secret key. Required when debug is off. Use a long random value |
| `DJANGO_ALLOWED_HOSTS` | `seznamovak.utb.cz` | Comma-separated allowed `Host` values |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `https://seznamovak.utb.cz` | Comma-separated origins trusted for CSRF (needed for the admin behind HTTPS) |
| `DJANGO_USE_HTTPS` | `true` | Marks session, CSRF and JWT cookies `Secure`. Set `false` for plain http locally |

### Database and port

| Variable | Default in `.env.example` | What it does |
| --- | --- | --- |
| `POSTGRES_DB` | `seznamovak` | Database name |
| `POSTGRES_USER` | `seznamovak` | Database user |
| `POSTGRES_PASSWORD` | `change-me` | Database password. Change it in production |
| `WEB_PORT` | `8002` | Host port mapped to the web container (container port 8000) |

Compose builds `DATABASE_URL` from the `POSTGRES_*` values.

### E-mail

| Variable | Default in `.env.example` | What it does |
| --- | --- | --- |
| `EMAIL_BACKEND` | `django.core.mail.backends.smtp.EmailBackend` | Use the console backend locally |
| `EMAIL_HOST` | `smtp.example.com` | SMTP server |
| `EMAIL_PORT` | `587` | SMTP port |
| `EMAIL_HOST_USER` | empty | SMTP login |
| `EMAIL_HOST_PASSWORD` | empty | SMTP password |
| `EMAIL_USE_TLS` | `true` | Use STARTTLS |
| `DEFAULT_FROM_EMAIL` | `Seznamovák UTB <seznamovak@sutb.cz>` | Sender of all e-mails |
| `SEZNAMOVAK_PUBLIC_URL` | `https://seznamovak.utb.cz` | Host used to build the cancel link in the e-mails (`<url>/api/reservations/cancel/<token>`) |

### Newsletter

| Variable | Default in `.env.example` | What it does |
| --- | --- | --- |
| `BREVO_API_KEY` | empty | Brevo API key. Students who tick the newsletter consent are added to the Brevo list only when this is set |
| `BREVO_LIST_ID` | `3` | Id of the Brevo list |

### Camp edition, prices and payment

Used in the e-mails, the payment QR codes and `GET /api/reservations`. The deposit is paid by bank transfer, the balance in cash on arrival.

| Variable | Default in `.env.example` | What it does |
| --- | --- | --- |
| `SEZNAMOVAK_YEAR` | `2026` | Camp year (e-mail subjects and texts, QR message) |
| `SEZNAMOVAK_EDITION` | `devátý` | Edition name shown in the e-mails |
| `SEZNAMOVAK_PRICE_TOTAL_CZK` | `3399` | Total price in CZK |
| `SEZNAMOVAK_PRICE_TOTAL_EUR` | `145` | Total price in EUR |
| `SEZNAMOVAK_DEPOSIT_CZK` | `2399` | Deposit in CZK (amount in the CZK QR code) |
| `SEZNAMOVAK_DEPOSIT_EUR` | `102` | Deposit in EUR (amount in the EUR QR code) |
| `SEZNAMOVAK_BALANCE_CZK` | `1000` | Balance paid in cash |
| `SEZNAMOVAK_PAYMENT_DEADLINE_DAYS` | `5` | Working days to pay the deposit, shown in the e-mails |
| `SEZNAMOVAK_ACCOUNT_CZK` | `2301459738/2010` | Czech account number shown in the e-mails |
| `SEZNAMOVAK_IBAN_CZK` | `CZ3720100000002301459738` | IBAN in the CZK QR code |
| `SEZNAMOVAK_ACCOUNT_EUR` | `2501459740/2010` | EUR account number shown in the e-mails |
| `SEZNAMOVAK_IBAN_EUR` | `CZ7120100000002501459740` | IBAN in the EUR QR code (and shown in the e-mails) |
| `SEZNAMOVAK_VARIABLE_SYMBOL` | `2026767` | Variable symbol in the e-mails and QR codes |

## API

Public paths have no trailing slash; the auth paths do. Errors are JSON, usually `{"detail": "..."}` (with `code` for some auth errors); validation errors are returned as `{"field": ["message"]}`. `/api/` answers in English, the admin is Czech. CORS is open for all origins on `/api/`.

| Method | Path | Auth | What it does |
| --- | --- | --- | --- |
| GET | `/api/reservations` | none | Faculties, free places per batch, batches (dates, substitutes, registration window) and prices |
| POST | `/api/reservations` | none | Create a reservation (multipart, with photo). Returns the reservation; it is a substitute when the batch is full |
| GET | `/api/reservations/cancel/{token}` | none | Cancel link from the e-mail. Returns plain text `Rezervace {id} zrušena. Více informací v emailu.` |
| POST | `/api/auth/login/` | none | Log in with `username` and `password`. Returns the user and sets the cookies |
| POST | `/api/auth/refresh/` | refresh cookie | Issue a new access cookie (204) |
| POST | `/api/auth/logout/` | refresh cookie | Blacklist the refresh token and delete the cookies (204) |
| GET | `/api/auth/me/` | access cookie | Current user (`id`, `username`, `email`, `first_name`, `last_name`) |
| GET | `/media/{path}` | staff session | Uploaded photos (log in at `/admin/` first) |

Notes:

- `POST /api/reservations` fields: `name`, `surname`, `email`, `faculty_id`, `year` (1-5), `batch` (batch number), `gdpr_consent` (must be true), `image` (JPEG or PNG, max 8 MB), optional `nickname`, `disability`, `roommate`, `newsletter_consent`. The billing address is sent as the multipart keys `billing_information[city]`, `billing_information[street]`, `billing_information[postal_code]`, `billing_information[country]`, `billing_information[phone]` (all required). A text value of `---` for an optional field is stored as empty.
- Registering outside the batch's registration window returns 409.
- Cookies: `access_token` (15 minutes, path `/`) and `refresh_token` (1 day, path `/api/auth/`), both httpOnly, SameSite Lax. Cookie-authenticated requests are CSRF-checked.
- Rate limits: login 20/min, public reservation endpoints 300/min.

## Django admin

Open `/admin/` and log in with a superuser (`make superuser`). The admin is in Czech.

- Reservations (`Rezervace`): list with photo link, name, nickname, e-mail, phone, faculty, batch, state (Nezaplaceno / Zaplaceno / Náhradník), filters by batch, paid, substitute and faculty, and search by name, e-mail and phone. Reservations are read-only: no add, no edit.
  - Actions: `Označit jako zaplacené` (marks paid and sends the payment e-mail; refused for substitutes and already paid ones) and `Zrušit rezervaci` (cancels, sends the cancel e-mail, deletes the photo and promotes the oldest substitute of the batch). The bulk delete action is removed. Deleting a single reservation does the same as cancelling it.
  - Summary above the list: total, paid and unpaid reservations, free places and substitutes per batch, count per faculty.
  - Buttons `Export PDF – N. turnus`: a landscape A4 PDF `turnusN.pdf` with every reservation of the batch (substitutes included): name, nickname, e-mail, year, faculty, disability, roommate, phone, paid, and the address.
- Batches (`Turnusy`): number, capacity, dates and the registration window.
- Faculties (`Fakulty`): name and abbreviation.
- Users: staff accounts (standard Django user admin).

## Deploy

For a Linux server with Docker and Compose v2.

1. Copy this folder to the server (git clone or `scp`) and go into it.
2. Create the config and edit it:

   ```bash
   cp .env.example .env
   ```

   Set at least: `DJANGO_SECRET_KEY` (long random string), `DJANGO_DEBUG=false`, `DJANGO_ALLOWED_HOSTS` and `DJANGO_CSRF_TRUSTED_ORIGINS` (your domain, the second one with `https://`), `DJANGO_USE_HTTPS=true`, `POSTGRES_PASSWORD`, `WEB_PORT`, the SMTP values (`EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL`), `SEZNAMOVAK_PUBLIC_URL`, the `SEZNAMOVAK_*` price and payment values for the current year, and `BREVO_API_KEY` if you want the newsletter.
3. Start it and create an admin user:

   ```bash
   docker compose up -d --build
   docker compose exec web python manage.py createsuperuser
   ```

   The Postgres port is not published; only the web container is reachable, on `WEB_PORT`. Both containers have `restart: unless-stopped`.
4. Put a reverse proxy with HTTPS in front of `WEB_PORT`. Caddy example (`/etc/caddy/Caddyfile`); Caddy gets the certificate automatically and sends `X-Forwarded-Proto`, which Django needs:

   ```
   seznamovak.utb.cz {
       request_body {
           max_size 20MB
       }
       reverse_proxy localhost:8002
   }
   ```

   Use your `WEB_PORT` instead of `8002`. Then run `sudo systemctl reload caddy`.

### Update

```bash
git pull
docker compose up -d --build
```

Migrations and static files run automatically on start.

### Logs

```bash
docker compose logs -f web
docker compose logs -f db
```

### Backup and restore

Data lives in two named volumes: `pgdata` (database) and `media` (uploaded student photos, `/app/media` in the web container).

```bash
# database backup
docker compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' > backup.sql

# photos backup
docker compose exec -T web tar czf - -C /app media > media.tar.gz
```

Restore into a running stack. Stop the web container first so nothing writes during the restore:

```bash
docker compose stop web

# recreate the database, then load the dump
docker compose exec -T db sh -c 'dropdb -U "$POSTGRES_USER" "$POSTGRES_DB" && createdb -U "$POSTGRES_USER" "$POSTGRES_DB"'
docker compose exec -T db sh -c 'psql -U "$POSTGRES_USER" "$POSTGRES_DB"' < backup.sql

docker compose start web

# photos
docker compose exec -T web tar xzf - -C /app < media.tar.gz
```
