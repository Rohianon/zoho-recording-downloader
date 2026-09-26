.DEFAULT_GOAL := help
.PHONY: help install test list list-all dry-run download scopes token clean-parts

# Optional regex override, e.g. make download PATTERN='pandas'
PATTERN ?=
pattern_arg = $(if $(PATTERN),--pattern '$(PATTERN)')

help: ## Show available commands
	@grep -hE '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	uv sync

test: ## Run the test suite
	uv run pytest -q

list: ## List recordings matching TITLE_PATTERN (or PATTERN=...)
	uv run main.py list $(pattern_arg)

list-all: ## List every recording in the Zoho org
	uv run main.py list --all

dry-run: ## Show what download would fetch
	uv run main.py download --dry-run $(pattern_arg)

download: ## Download matching recordings not yet on disk
	uv run main.py download $(pattern_arg)

scopes: ## Print the OAuth scopes for the Zoho Self Client
	uv run scripts/get_refresh_token.py || true

token: ## Exchange a grant code for a refresh token: make token CODE=1000.xxx
	@test -n "$(CODE)" || (echo "usage: make token CODE=<grant-code>" && exit 1)
	uv run scripts/get_refresh_token.py $(CODE)

clean-parts: ## Delete partial downloads (*.part) in data/recordings/
	find data/recordings -name '*.part' -delete 2>/dev/null || true
