MAKEFLAGS += --always-make



# ----------------------------------- worker -----------------------------------------------

start_worker:
	docker-compose -f docker-compose.worker.yaml up worker -d --build --force-recreate --no-deps --pull always

stop_worker:
	docker-compose -f docker-compose.worker.yaml down worker


# ----------------------------------- api -----------------------------------------------

start_api:
	docker-compose -f docker-compose.worker.yaml up api -d --build
	docker-compose -f docker-compose.worker.yaml up redis -d --build

stop_api:
	docker-compose -f docker-compose.worker.yaml down api
	docker-compose -f docker-compose.worker.yaml down redis