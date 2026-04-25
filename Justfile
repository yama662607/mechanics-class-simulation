set dotenv-load := true

pm := "uv"
python := "uv run python"

set windows-shell := ["powershell.exe", "-NoLogo", "-Command"]

default: check

check-env:
    @{{python}} tools/check_env.py

setup: check-env
    {{pm}} sync --all-extras
    npm install

check: fmt-check lint typecheck validate-docs test
    @echo "All quality checks passed."

check-full: check render
    @echo "Full quality checks passed."

fix: fmt lint-fix validate-docs-fix
    @echo "Auto-fixes applied."

test *args="":
    {{pm}} run pytest {{args}}

fmt-check:
    {{pm}} run ruff format --check

fmt:
    {{pm}} run ruff format

lint:
    {{pm}} run ruff check

lint-fix:
    {{pm}} run ruff check --fix

typecheck:
    {{pm}} run mypy tools

clean:
    {{python}} tools/clean.py

render:
    quarto render quarto --to html

render-pdf:
    quarto render quarto --to pdf

docs:
    @{{python}} tools/dev_server.py

fix-docs:
    -lsof -ti:4312 | xargs kill -9 2>/dev/null
    -pkill -f "quarto preview" 2>/dev/null
    @echo "Cleaned lingering Quarto preview processes."

validate-docs:
    {{python}} tools/validate_docs.py quarto/

validate-docs-no-cache:
    {{python}} tools/validate_docs.py quarto/ --no-cache

validate-docs-fix:
    {{python}} tools/validate_docs.py quarto/ --fix

clear-validation-cache:
    {{python}} tools/validate_docs.py --clear-cache

extract-pdf path *args="":
    {{python}} tools/extract_pdf.py {{path}} {{args}}
