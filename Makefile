.PHONY: install lint spellcheck format test build ci clean

install:
	uv sync --group dev

lint:
	uv run ruff check .
	uv run ruff format --check .

spellcheck:
	uv run typos

format:
	uv run ruff check --fix .
	uv run ruff format .

test:
	uv run pytest

build:
	uv build

# Single entrypoint for CI: same steps you can run locally with `make ci`
ci: install lint spellcheck test build

clean:
	rm -rf dist build .pytest_cache .ruff_cache
