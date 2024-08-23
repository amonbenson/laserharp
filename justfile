set shell := ["bash", "-c"]

list:
    @just --list

lint-js:
    cd frontend && yarn lint

lint-py:
    pylint $(git ls-files '*.py')

lint: lint-js lint-py
