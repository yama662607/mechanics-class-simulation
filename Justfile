# =============================================================================
# Quarto Textbook Template — Justfile
# =============================================================================
# Cross-platform (Windows / macOS / Linux). All shell-out work is delegated to
# Python helpers under tools/ so PowerShell and POSIX shells behave identically.
# =============================================================================

set dotenv-load := true
set windows-shell := ["powershell.exe", "-NoLogo", "-Command"]

pm := "uv"
python := "uv run python"

# デフォルト: 全体の品質チェックを実行
default: check

# =============================================================================
# Standard Interface (AI Agent Protocol)
# =============================================================================

# 環境の整合性チェック (uv / just / quarto / npm)
check-env:
    @{{python}} tools/check_env.py

# 環境構築: 依存関係のインストール (base のみ — extras は明示的に追加)
# 例: just setup-extras ocr math    で OCR と数式抽出も追加でインストール
setup: check-env
    @echo "Setting up environment..."
    {{pm}} sync
    npm install
    @echo "Environment setup complete."

# 全 extras を追加: 重い (easyocr / pix2text / qiskit / shinylive 等を含む)
setup-all:
    @echo "Setting up environment with ALL extras..."
    {{pm}} sync --all-extras
    npm install
    @echo "Environment setup (all extras) complete."

# 全体品質検証 (CI ゲート)
check: fmt-check lint typecheck validate-docs render-check test
    @echo "All quality checks passed."

# 構文チェックのみの軽量レンダリング (compute blocks は実行しない)
render-check:
    @echo "Quarto syntax check (no execute)..."
    quarto render quarto --to html --execute-debug --no-execute

# フル品質検証: HTML 実レンダリングまで含めて確認
check-full: check render-site
    @echo "Full quality checks passed."

# 自動修正
fix: fmt lint-fix validate-docs-fix
    @echo "Auto-fixes applied."

# =============================================================================
# Testing & Verification
# =============================================================================

test *args="":
    @echo "Running unit tests..."
    {{pm}} run pytest {{args}}

# =============================================================================
# Granular Tasks
# =============================================================================

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

# =============================================================================
# Operations & Utilities
# =============================================================================

# ビルド成果物・キャッシュ削除 (Cross-platform)
clean:
    {{python}} tools/clean.py

# =============================================================================
# Quarto Tasks
# =============================================================================

# Quarto プレビュー起動 (port 4312)。
# 前回のプレビューを止め忘れて別ターミナルで再実行しても動くよう、
# 起動前に必ず port 4312 に居座っているプロセスを掃除する。
docs: fix-docs
    @{{python}} tools/dev_server.py

# プレビューが落ちない / ポートが使用中の場合の復旧 (Win/Mac/Linux 対応)。
# `docs` から自動で呼ばれる。手動での復旧用にも単独実行可。
fix-docs:
    @{{python}} tools/kill_quarto_process.py --port 4312

# Quarto HTML 実レンダリング
render-site:
    quarto render quarto --to html

# Quarto PDF 実レンダリング
render-book-pdf:
    quarto render quarto --to pdf

# ドキュメント整合性検証 (Quarto / Mermaid / LaTeX)
validate-docs:
    {{python}} tools/validate_docs.py quarto/

validate-docs-no-cache:
    {{python}} tools/validate_docs.py quarto/ --no-cache

validate-docs-fix:
    {{python}} tools/validate_docs.py quarto/ --fix

clear-validation-cache:
    {{python}} tools/validate_docs.py --clear-cache

# =============================================================================
# PDF Ingestion (USE BOTH render-pdf AND extract-pdf BEFORE WRITING qmd)
# =============================================================================
# AGENTS.md mandates running both tools and cross-checking the rendered images
# against extracted text, so OCR / formula misreads are caught.

# 画像出力先の規約: PDF basename ごとに quarto/assets/raw/<stem>_pages/
_pdf_image_dir := "quarto/assets/raw"

# 教科書 PDF を PNG 画像に変換 (ページごとに画像確認するため)
# 使い方: just render-pdf <pdf_path> <start_page> <end_page>
render-pdf pdf_path start end *args="":
    {{python}} tools/render_pdf.py {{pdf_path}} --start {{start}} --end {{end}} --out-dir "{{_pdf_image_dir}}/{{ file_stem(pdf_path) }}_pages" {{args}}

# PDF から文字情報 (text + OCR + LaTeX 数式) を抽出
# 使い方: just extract-pdf <pdf_path> <start_page> <end_page> [--mode simple|ocr|latex]
# 内部で render-pdf を先に走らせて画像化 → text/OCR + pix2text を全ページに併走 (auto モード)
# AI agent は出力後、必ず quarto/assets/raw/<pdf>_pages/ の PNG を Read で確認すること
extract-pdf pdf_path start end *args="":
    @just render-pdf {{pdf_path}} {{start}} {{end}}
    {{python}} tools/extract_pdf.py {{pdf_path}} --start {{start}} --end {{end}} --image-dir "{{_pdf_image_dir}}/{{ file_stem(pdf_path) }}_pages" {{args}}

# PDF 構造の診断 (どの --mode を選ぶべきか分からない時)
diagnose-pdf pdf_path:
    {{python}} tools/extract_pdf.py {{pdf_path}} --diagnose

# =============================================================================
# Optional: Streamlit / Shiny app launcher
# =============================================================================

# Streamlit アプリ起動: just app <path>
app path:
    {{python}} -m streamlit run {{path}}
