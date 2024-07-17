.PHONY: test

install:
	poetry install

test:
	poetry run pytest \
    --nbmake \
    --nbmake-find-import-errors \
    --nbmake-timeout=20 \
    -vvv
