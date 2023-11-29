# :computer: Website demo with Flask + Bootstrap 5

Forum website demo

## :floppy_disk: Installation

Create virtual enviroment:

```bash
python -m venv env
```

Activate enviroment:

- Windows:

```bash
. env/scripts/activate
```

- Mac/Linux:

```bash
. env/bin/activate
```

Upgrade pip:

```bash
python -m pip install --upgrade pip
```

Install requirements:

```bash
pip install -r requirements-dev.txt
```

## :wrench: Config

Create `.env` file. Check the example `.env.example`

:lock: How to create a secret key:

```bash
openssl rand -base64 64
```

:construction: Before first run:

Run `docker-compose` :whale: to start the database server

```bash
docker compose -f "compose.yaml" up -d --build adminer db
```

and init the database with alembic:

```bash
alembic upgrade head
```

## :runner: Run

```bash
flask run --debug
```

## :pushpin: Features

- [x] flask
- [x] blueprints
- [x] bootstrap 5
- [X] postgres database
- [X] alembic
- [X] docker compose
- [X] 2FA
- [X] Dark theme
