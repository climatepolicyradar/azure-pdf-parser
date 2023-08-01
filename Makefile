.PHONY: test

install:
	poetry config virtualenvs.create false
	poetry export --with dev > requirements.txt
	pip3 install --no-cache -r requirements.txt

test:
	python -m pytest -vvv