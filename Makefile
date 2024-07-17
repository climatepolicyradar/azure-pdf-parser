.PHONY: test

install:
	poetry install

test:
	poetry run python -m pytest \
    --nbmake \
    --nbmake-find-import-errors \
    --nbmake-timeout=20 \
    -vvv
