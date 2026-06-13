.PHONY: test test-backend test-frontend install dev docker-build docker-up docker-down lint

install:
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

test: test-backend

test-backend:
	cd backend && python -m pytest tests/ -v

test-frontend:
	cd frontend && npm test

dev-backend:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	cd frontend && npm run dev

docker-build:
	docker compose build

docker-up:
	docker compose up -d

docker-down:
	docker compose down

lint-backend:
	cd backend && python -m ruff check app/ tests/
