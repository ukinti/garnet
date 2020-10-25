prun := poetry run

.PHONY: isort
isort:
	$(prun) isort src/

.PHONY: imports
imports:
	$(prun) lint-imports

.PHONY: black
black:
	$(prun) black src/

.PHONY: flake8
flake8:
	$(prun) flake8 src/

.PHONY: lint
lint: black isort imports flake8
