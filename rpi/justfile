set shell := ["bash", "-c"]


help:
    @just --list


lint-js:
    cd frontend && yarn lint
lint-py:
    pylint $(git ls-files '*.py')
lint: lint-js lint-py


fix-js:
    cd frontend && yarn lint:fix
fix-py:
    black $(git ls-files '*.py')
    pylint $(git ls-files '*.py')
fix: fix-js fix-py
