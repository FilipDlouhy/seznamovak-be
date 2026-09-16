.PHONY: up down ps logs psql shell migrate seed superuser lint

up:
	docker compose up -d --build

down:
	docker compose down

ps:
	docker compose ps

logs:
	docker compose logs -f web

psql:
	docker compose exec db sh -c 'psql -U "$$POSTGRES_USER" "$$POSTGRES_DB"'

shell:
	docker compose exec web python manage.py shell

migrate:
	docker compose exec web python manage.py migrate

seed:
	docker compose exec web python manage.py seed_data

superuser:
	docker compose exec web python manage.py createsuperuser

lint:
	cd api && uv run ruff check . && uv run python -m mypy apps common config
