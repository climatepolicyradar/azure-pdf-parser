.PHONY: install test

install:
	poetry install

test:
	poetry run pytest -vvv
