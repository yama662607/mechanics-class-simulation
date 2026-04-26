# tools/

Cross-platform Python helpers invoked from the Justfile.

## PDF 取り込みの意思決定 — どの mode を使うか

```
                    ┌──────────────────────────┐
                    │ just diagnose-pdf <pdf>  │
                    └────────────┬─────────────┘
                                 ▼
       ┌─────────────────────────┴──────────────────────────┐
       │                                                    │
   テキスト層あり                                    テキスト層なし
       │                                                    │
       ▼                                                    ▼
┌──────────────┐                              ┌──────────────────────┐
│ --mode auto  │ ← 数式が無ければ最速           │ uv sync --extra ocr  │
│  または       │                              │ --mode ocr           │
│ --mode simple│                              └──────────────────────┘
└──────────────┘
       │
       │ 数式 (LaTeX) も欲しい
       ▼
┌──────────────────────────┐
│ uv sync --extra math      │
│ --mode latex              │ ← 事前に render-pdf で画像化が必要
│ + --image-dir <dir>       │
└──────────────────────────┘
```

**両 tool 必須併用**: `render-pdf` で画像も用意し、文字情報と画像を照合してから qmd 化 (詳細は AGENTS.md)。

## Core (always available)

| ファイル | 用途 |
| --- | --- |
| `check_env.py` | uv / just / quarto / npm の存在 & バージョン確認 |
| `clean.py` | ビルド成果物削除 (cross-platform, shutil/glob ベース) |
| `dev_server.py` | Quarto preview + watcher 起動 (port 4312) |
| `validate_docs.py` | Quarto / Mermaid / LaTeX 整合性検証 + キャッシュ |
| `kill_quarto_process.py` | Quarto preview プロセスを停止 (Win/Mac/Linux 対応) |

## PDF ingestion (use BOTH together)

> AGENTS.md の必須ワークフロー: qmd 作成前に **render-pdf と extract-pdf の両方を実行** し、画像と文字情報を照合する。

| ファイル | 用途 | 必要な追加依存 |
| --- | --- | --- |
| `render_pdf.py` | PDF ページを PNG 化 (画像確認用) | (デフォルト) |
| `extract_pdf.py` | 文字 / OCR / LaTeX 数式抽出を 1 つに統合 | mode 別 (下記) |

### `extract_pdf.py` の mode

| `--mode` | 説明 | 追加依存 |
| --- | --- | --- |
| `auto` (デフォルト) | テキスト層あれば simple、無ければ OCR にフォールバック | OCR 時のみ `--extra ocr` |
| `simple` | pymupdf のみ — 高速・テキスト埋込済 PDF 用 | (デフォルト) |
| `ocr` | easyocr — スキャン PDF / 画像 PDF 用 | `uv sync --extra ocr` |
| `latex` | pix2text — テキスト + LaTeX 数式抽出 | `uv sync --extra math` (要 render-pdf 先行) |

`--diagnose` フラグで構造のみ表示 (どの mode を使うべきか判断材料)。

## utils/

| ファイル | 用途 |
| --- | --- |
| `find_quarto.py` | quarto バイナリ探索 |
| `quarto_watcher.py` | パーシャル `_*.qmd` 変更検知 → 親 qmd を touch |
| `pdf_processing.py` | pymupdf による text/image 抽出共通関数 |
| `latex_extraction.py` | pix2text 呼び出し (lazy import) |
| `mermaid_parser.js` | Mermaid 図式パーサ (validate_docs から呼出) |
