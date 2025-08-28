.PHONY: setup dev run

setup:
	python -m venv .venv && . .venv/bin/activate && pip install -U pip && pip install -r requirements.txt

dev:
	. .venv/bin/activate && export $$(grep -v '^#' .env | xargs) && python -m src.main

run:
	. .venv/bin/activate && python -m src.main

