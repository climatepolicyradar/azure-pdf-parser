.PHONY: test

install:
	poetry shell
	poetry install

test:
	poetry run python -m pytest -vvv