MAKEFLAGS += --always-make

# ----------------------------------- installation -----------------------------------------------
install:
	python -m venv venv
	./venv/bin/pip install --upgrade pip
	./venv/bin/pip install -r requirements.txt

# ----------------------------------- client -----------------------------------------------
# client_start:
# 	docker-compose --env-file ./config/git/git.env --env-file ./config/dvc/dvc.env up -d build_dvc  --build
# 	docker-compose --env-file ./config/git/git.env --env-file ./config/dvc/dvc.env up -d dataset_ia_data --build
# 	docker-compose up -d docs

# client_into:
# 	docker-compose exec dataset_ia_data zsh

# client_stop:
# 	docker-compose down dataset_ia_data
# 	docker-compose down build_dvc
# 	docker-compose down docs

# ----------------------------------- server -----------------------------------------------
server_start:
	docker-compose dvc-minio up -d --build

# ----------------------------------- documentation -----------------------------------------------
# docs_build:
# 	cd docs && make html

# docs_container_build:
# 	make docs_build && docker-compose build docs

# docs_container_up:
# 	docker-compose up -d docs

# docs_serve:
# 	cd docs/_build/html && python -m http.server 1200

# docs_clean:
# 	cd docs && make clean


# ----------------------------------- worker -----------------------------------------------

start_worker:
	docker-compose -f docker-compose.worker.yaml up worker -d --build

stop_worker:
	docker-compose -f docker-compose.worker.yaml down worker


# ----------------------------------- api -----------------------------------------------

start_api:
	docker-compose -f docker-compose.worker.yaml up api -d --build
	docker-compose -f docker-compose.worker.yaml up redis -d --build

stop_api:
	docker-compose -f docker-compose.worker.yaml down api
	docker-compose -f docker-compose.worker.yaml down redis

into_worker:
	docker-compose -f docker-compose.worker.yaml exec worker zsh

logs_worker:
	docker-compose -f docker-compose.worker.yaml logs -f worker

nload_worker:
	docker-compose -f docker-compose.worker.yaml exec worker nload