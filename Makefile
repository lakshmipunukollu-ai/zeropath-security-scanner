.PHONY: dev test seed build install clean

install:
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

dev:
	cd backend && uvicorn app.main:app --reload --port 3006 &
	cd frontend && PORT=5006 npm start

test:
	cd backend && python -m pytest tests/ -v --tb=short

seed:
	cd backend && python -m seed

build:
	cd backend && pip install -r requirements.txt
	cd frontend && npm install && npm run build

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null; true
	rm -f backend/test.db
