_local_wait_for_db:
	docker compose -f docker-compose-local.yml exec -T db bash -c 'until pg_isready -U postgres; do sleep 3; done'

_local_migrate: _local_wait_for_db
	alembic upgrade heads

local_up:
	docker compose -f docker-compose-local.yml up -d
	make _local_migrate

local_down:
	docker compose -f docker-compose-local.yml down --remove-orphans



_prod_wait_for_db:
	docker compose -f docker-compose.yml exec -T db bash -c 'until pg_isready -U postgres; do sleep 3; done'

_prod_migrate: _prod_wait_for_db
	alembic upgrade heads

prod_up:
	docker compose -f docker-compose.yml up -d
	make _prod_migrate

prod_rebuild:
	docker compose -f docker-compose.yml up --build -d
	make _prod_migrate

prod_down:
	docker compose -f docker-compose.yml down --remove-orphans
