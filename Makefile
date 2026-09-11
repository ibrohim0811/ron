mig:
	alembic revision --autogenerate -m "initial_migration"
migrate:
	alembic upgrade head

run:
	python main.py