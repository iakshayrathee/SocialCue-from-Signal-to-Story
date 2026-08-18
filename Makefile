# SocialCue — dev & run helpers.
# Windows users without `make`: the equivalent commands are in the README.

.PHONY: help install frontend backend build dev-backend dev-frontend eval docker up down clean

help:
	@echo "SocialCue"
	@echo "  make install       Install backend (venv) + frontend deps"
	@echo "  make build         Build frontend into backend/static (single-service)"
	@echo "  make backend       Run FastAPI (serves built frontend) on :8000"
	@echo "  make dev-frontend  Run Vite dev server on :5173 (proxies /api -> :8000)"
	@echo "  make eval          Run the golden-case eval suite"
	@echo "  make up            docker compose up --build (one command, MOCK_MODE)"
	@echo "  make down          docker compose down"

install:
	python -m venv .venv
	./.venv/bin/pip install --upgrade pip
	./.venv/bin/pip install -r backend/requirements.txt
	cd frontend && npm install

frontend:
	cd frontend && npm run build

build: frontend
	rm -rf backend/static && mkdir -p backend/static
	cp -r frontend/dist/* backend/static/

backend:
	cd backend && MOCK_MODE=true ../.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000

dev-backend:
	cd backend && MOCK_MODE=true ../.venv/bin/uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

eval:
	cd backend && MOCK_MODE=true ../.venv/bin/python -m evals.run

up:
	docker compose up --build

down:
	docker compose down

clean:
	rm -rf .venv frontend/node_modules frontend/dist backend/static
