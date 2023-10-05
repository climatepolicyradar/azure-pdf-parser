.PHONY: test

install:
	poetry install

test:
	poetry run python -m pytest -vvv
