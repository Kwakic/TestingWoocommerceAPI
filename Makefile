# Makefile = orchestrates project execution
# It should control:
  # - docker
  # - setup
  # -tests

.PHONY: up setup test run down

up:
	docker compose -f docker-compose.wp.yml up -d

setup:
	bash scripts/setup.sh

test:
	pytest -v

run: up setup test

down:
	docker compose -f docker-compose.wp.yml down
