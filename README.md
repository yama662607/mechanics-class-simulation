# Quarto Textbook Template

[![Quality Checks](https://github.com/yama662607/quarto-textbook-template/actions/workflows/check.yml/badge.svg)](https://github.com/yama662607/quarto-textbook-template/actions/workflows/check.yml)
[![Quarto Publish](https://github.com/yama662607/quarto-textbook-template/actions/workflows/publish.yml/badge.svg)](https://github.com/yama662607/quarto-textbook-template/actions/workflows/publish.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Made with Quarto](https://img.shields.io/badge/Made%20with-Quarto-39729E)](https://quarto.org)

教科書・授業ノート・写真や PDF など各種素材から **Quarto** ドキュメントを構築し、**GitHub Pages** に公開するためのテンプレートリポジトリです。

> [!TIP]
> このリポジトリは GitHub の "**Use this template**" ボタンから新規プロジェクトとして即コピーできます。

## 主な特徴

- **Quarto Book** ベース (HTML / PDF 両対応)
- **対話シミュレーション**: [Quarto Live](https://r-wasm.github.io/quarto-live/) + Pyodide で **ブラウザ完結** の Python (numpy/matplotlib) を実行。サーバー不要、生徒が Notebook にコピペしてそのまま動かせる素のコード。日本語フォントの組み込み済 (`assets/fonts/NotoSansJP-Regular.ttf`)
- **PDF 取り込み (画像化 + 文字抽出)** — `render_pdf.py` (画像) と `extract_pdf.py` (text / OCR / LaTeX 数式) の併用が前提
- **Mermaid / KaTeX** によるダイアグラム & 数式
- **Justfile** による統一コマンドインターフェース (Win/Mac/Linux)
- **GitHub Actions** で push 時に自動公開、3 OS マトリクスで品質チェック
- **品質ゲート**: ruff + mypy + pytest + Quarto/Mermaid/LaTeX 整合性検証 + `quarto render --no-execute` 構文チェック
- **AI エージェント対応** (`AGENTS.md` 準拠 + `CLAUDE.md` / `GEMINI.md` 同梱)

## How to use this template

### 1. テンプレートからリポジトリ作成

**GitHub Web UI から (推奨)**: リポジトリページ右上の "**Use this template**" → "**Create a new repository**" → 自分の Organization / アカウントを選び、リポジトリ名を入力 → "Create repository"。完了後、ローカルに clone:

```bash
git clone https://github.com/<you>/<your-repo>.git
cd <your-repo>
```

**`gh` CLI を使う場合** (要 `gh auth login`):

```bash
gh repo create my-textbook --template yama662607/quarto-textbook-template --public --clone
cd my-textbook
```

### 2. セットアップ — 4 つの選び方

#### A. 何も入っていない端末を使う・お任せで動かしたい (推奨)

OS に応じて 1 行:

```bash
# macOS / Linux
./scripts/bootstrap.sh

# Windows (PowerShell)
.\scripts\bootstrap.ps1
```

ツール (just / uv / quarto / node) を OS のパッケージマネージャ (brew / apt / dnf / winget / scoop / 公式 curl installer) で入れた後、`uv sync` と `npm install` まで自動実行します。Python 3 だけ事前に必要 (大半の OS に同梱)。`--dry-run` で実際には実行せず内容を確認できます。

#### B. mise / asdf を使っている

`mise.toml` と `.tool-versions` を同梱しているので 1 発:

```bash
mise install              # または: asdf install
uv sync && npm install
```

#### C. ブラウザだけで試したい (GitHub Codespaces / VS Code Dev Containers)

`.devcontainer/devcontainer.json` 同梱。リポジトリページの **`<> Code` → `Codespaces` → `Create codespace on main`** を押すだけで、5 分後にブラウザで `just docs` が動かせる状態になります。VS Code 派なら "Dev Containers: Reopen in Container" でも可。Docker が必要。

#### D. 自分でツールを選んで入れたい

| ツール | macOS | Linux | Windows |
| --- | --- | --- | --- |
| **Python 3.12+** | `brew install python@3.12` | apt/dnf | [python.org](https://www.python.org/) |
| **uv** | `brew install uv` | `curl -LsSf https://astral.sh/uv/install.sh \| sh` | `powershell -c "irm https://astral.sh/uv/install.ps1 \| iex"` |
| **just** | `brew install just` | [just.systems](https://just.systems/man/en/packages.html) | `winget install Casey.Just` または `scoop install just` |
| **Quarto** | `brew install --cask quarto` | [.deb / .rpm](https://quarto.org/docs/get-started/) | [installer](https://quarto.org/docs/get-started/) |
| **Node.js 20+** | `brew install node` | nvm/apt | [nodejs.org](https://nodejs.org/) |

その後:

```bash
just setup    # uv sync + npm install
just docs     # http://localhost:4312
```

### 3. プレースホルダ書き換え

clone 後、以下のプレースホルダを置換してください:

| ファイル | 書き換える箇所 |
| --- | --- |
| `pyproject.toml` | `name`, `description`, `authors` |
| `package.json` | `name`, `description` |
| `quarto/_quarto.yml` | `book.title`, `book.author`, `book.repo-url`, `book.repo-branch`, `page-footer` |
| `quarto/index.qmd` | タイトル・サブタイトル・著者・本文 |
| `quarto/textbook/textbook.qmd` 等 | サンプル本文を自分の章構成に置換 |
| `LICENSE` | copyright 年と保有者 |
| `README.md` | このファイル全体 (バッジ URL の `yama662607/quarto-textbook-template` も) |
| `.github/CODEOWNERS` | `* @yama662607` をあなたの GitHub アカウント / チームに |
| `.devcontainer/devcontainer.json` | `name` ("Quarto Textbook Template" → 派生プロジェクト名) |
| `SECURITY.md` | リポジトリ URL (`yama662607/quarto-textbook-template`) |
| `CHANGELOG.md` | 0.1.0 エントリのコピーライト年や、自分のリリース履歴 |

### 4. GitHub Pages の有効化

1. GitHub リポジトリの Settings → Pages → Source を **`gh-pages` branch** に設定
2. `git push origin main` すると `.github/workflows/publish.yml` が走り、自動で公開

教科書本文で optional 機能 (Qiskit / Shinylive / Jupyter compute / OCR / LaTeX) を使う場合は `publish.yml` の `uv sync` 行に `--extra <name>` を追記してください (デフォルトは base のみで軽量化)。

## ディレクトリ構成

```
.
├── quarto/                  # Quarto ソース
│   ├── _quarto.yml         # サイト設定 (output-dir: _book)
│   ├── index.qmd           # トップページ
│   ├── textbook/           # 本編 (textbook.qmd + _NN_*.qmd で章分割)
│   ├── templates/          # CSS / sidebar JS / qmd テンプレ
│   ├── preamble.tex        # PDF 出力用 LaTeX プリアンブル
│   ├── _freeze/            # compute block 結果キャッシュ (commit する)
│   └── assets/             # 画像・PDF など
│       ├── images/         # 公開図版
│       ├── pdf/            # 公開 PDF
│       ├── raw/            # 個人保管 (gitignore)
│       └── private/        # 機密素材 (gitignore)
├── research/               # 素材インテイク・下書き
│   ├── inbox/             # 取り込み待ち素材 (gitignore)
│   ├── notes/             # 個人メモ
│   ├── drafts/            # 公開前下書き
│   └── guidelines/        # 編集ガイドライン
├── tools/                  # 開発支援スクリプト (Python)
│   ├── README.md          # 各ツールの用途
│   ├── check_env.py       # 環境チェック
│   ├── dev_server.py      # Quarto preview + watcher
│   ├── validate_docs.py   # Quarto/Mermaid/LaTeX 検証
│   ├── render_pdf.py      # PDF → PNG 画像化
│   ├── extract_pdf.py     # PDF 文字抽出 (auto/simple/ocr/latex)
│   ├── clean.py           # ビルド成果物削除
│   └── kill_quarto_process.py # Win/Mac/Linux 対応プロセス停止
├── tests/                  # pytest
├── .github/workflows/      # CI/CD (publish.yml + check.yml)
├── Justfile                # 統一コマンド
├── pyproject.toml          # Python 依存 (PEP 735 dependency-groups)
├── package.json            # Node 依存
├── AGENTS.md               # AI エージェント向け規約 (本体)
├── CLAUDE.md               # Claude Code 用 (@AGENTS.md 参照)
├── GEMINI.md               # Gemini CLI 用 (@AGENTS.md 参照)
└── LICENSE                 # MIT
```

## コマンド一覧 (`just <task>`)

### 標準インターフェース

| コマンド | 用途 |
| --- | --- |
| `just check-env` | 必要ツール (uv, just, quarto, npm) の存在確認 |
| `just setup` | 依存インストール (`uv sync` + `npm install`) |
| `just check` | 品質ゲート (fmt + lint + typecheck + validate-docs + render-check + test) |
| `just check-full` | `check` + 実 HTML レンダリング |
| `just fix` | 自動修正 (fmt + lint + validate-docs --fix) |
| `just test` | pytest 実行 |
| `just clean` | ビルド成果物削除 (cross-platform) |

### Quarto

| コマンド | 用途 |
| --- | --- |
| `just docs` | プレビューサーバー (http://localhost:4312) |
| `just fix-docs` | プレビュー復旧 (Win/Mac/Linux 対応) |
| `just render-site` | HTML 実レンダリング |
| `just render-book-pdf` | PDF 実レンダリング |
| `just render-check` | 構文チェック (compute 実行なし、CI と同等) |
| `just validate-docs` | ドキュメント整合性検証 |
| `just validate-docs-fix` | 自動修正可能なエラーを修正 |

### PDF 取り込み (両方の併用が必須)

> ⚠️ **AGENTS.md の必須ワークフロー**: qmd 作成前に **`render-pdf` と `extract-pdf` の両方を実行**し、画像と文字情報を照合してください。

| コマンド | 用途 |
| --- | --- |
| `just render-pdf <pdf> <start> <end>` | PDF ページを PNG 化 (画像で誤読チェック) |
| `just extract-pdf <pdf> [opts]` | 文字 / OCR / LaTeX 抽出 (`--mode auto` がデフォルト) |
| `just diagnose-pdf <pdf>` | PDF 構造診断 (どの mode を使うか判断) |

詳細は [`tools/README.md`](tools/README.md) と [`AGENTS.md`](AGENTS.md) を参照。

## オプション機能

依存をインストールして有効化:

```bash
uv sync --extra ocr        # 画像 PDF の OCR (easyocr, ~1GB)
uv sync --extra math       # 数式抽出 (pix2text, 大型 ML モデル)
uv sync --extra notebook   # numpy / matplotlib / jupyter
uv sync --extra quantum    # Qiskit
uv sync --extra shiny      # Shinylive 対話シミュレーション
uv sync --extra viz        # plotly / pyvis
uv sync --all-extras       # 全部入り
```

## 編集ワークフロー

1. `research/inbox/YYYY-MM-DD_topic/` に元素材 (写真・スキャン PDF・講義スライド等) を置く
2. `just diagnose-pdf <pdf>` で PDF 構造を確認、適切な mode を選定
3. **`just render-pdf` と `just extract-pdf` を併用** して画像と文字情報を取得
4. 両方を照合しながら `quarto/textbook/_NN_*.qmd` に書き起こす
5. `just docs` でプレビュー、`just check` で品質確認
6. `git push` で GitHub Pages に自動公開

## AI エージェントとの協働

[`AGENTS.md`](AGENTS.md) に編集規約を記載 ([agents.md spec](https://agents.md) 準拠)。

- **Claude Code**: `CLAUDE.md` が `@AGENTS.md` を import
- **Gemini CLI**: `GEMINI.md` が `@AGENTS.md` を import
- **Codex / Cursor / Copilot 等**: `AGENTS.md` を直接参照

## クレジット

このテンプレートは以下のプロジェクトの知見を統合して作成されました:

- [yama662607/Quantum-information](https://github.com/yama662607/Quantum-information) — ベース構成、validate_docs、pix2text 数式抽出
- [yukicomadaqq/peskin](https://github.com/yukicomadaqq/peskin) — easyocr による画像 PDF 対応、PDF 診断
- mechanics-class-simulation — Shinylive 統合、シンプル PDF 抽出
- Field-Theory — 標準ディレクトリ構成

## サードパーティ素材のクレジット

- [Quarto Live](https://github.com/r-wasm/quarto-live) — ブラウザ内 Python 実行 (Apache 2.0 / `quarto/_extensions/r-wasm/live/`)
- [Noto Sans JP](https://github.com/notofonts/noto-cjk) — Pyodide matplotlib 用日本語フォント (SIL OFL 1.1 / `quarto/assets/fonts/NotoSansJP-Regular.ttf`)

## ライセンス

[MIT](LICENSE)
