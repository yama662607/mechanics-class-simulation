# AGENTS.md

> AI コーディングエージェント (Claude Code, Codex, Cursor, Copilot, Gemini CLI 等) 向けの規約。
> 本ファイルは [agents.md](https://agents.md) 仕様に準拠します。Claude Code は `CLAUDE.md`、Gemini CLI は `GEMINI.md` から本ファイルを参照します。

## Project overview

Quarto Book ベースの教科書 / 講義ノートサイト。HTML を GitHub Pages、PDF をオプションで生成。本文は `quarto/textbook/textbook.qmd` を信頼できる唯一の情報源 (single source of truth) とし、章ごとのコンテンツは `_*.qmd` パーシャルに分割して `{{< include >}}` で統合する。

## Setup commands

```bash
just check-env   # ツール (uv / just / quarto / npm) 確認
just setup       # uv sync + npm install
just docs        # http://localhost:4312 でプレビュー
```

## ⚠️ PDF 取り込みの必須ワークフロー

qmd を書き起こす前に、**`extract-pdf` を実行 → 出力された画像を必ず Read で確認** してください。

```bash
# 1 コマンドで画像化 + text/OCR/LaTeX 抽出が走る
just extract-pdf <pdf_path> <start_page> <end_page>
# 内部で render-pdf が先に呼ばれて quarto/assets/raw/<stem>_pages/page_NN.png を生成、
# その上で text(or OCR) + pix2text(LaTeX) がページごとに併走する (auto モード)。

# モード未確定なら先に診断
just diagnose-pdf <pdf_path>

# 例外的にテキストのみで足りるとき (画像不要 = qmd 化しないとき) のみ:
uv run python tools/extract_pdf.py <pdf_path> --mode simple --start <s> --end <e>
```

**抽出 → qmd の必須手順:**
1. `just extract-pdf <pdf> <s> <e>` を実行
2. 標準エラーに出る画像ディレクトリ (`quarto/assets/raw/<stem>_pages/`) の **PNG を Read tool で 1 ページずつ開いて視認**
3. 抽出された text + LaTeX を画像と突き合わせ、OCR 誤読・式番号・図表配置を補正
4. その上で qmd を書き起こす

**画像レビューを飛ばすことは禁止** (テキストと LaTeX だけでは図表配置・式番号・OCR 誤読を必ず取りこぼす)。
ファイル分離 (render_pdf.py / extract_pdf.py) と auto モードでの `--image-dir` 必須化はこのレビューを強制するためにある。
`extract-pdf` の出力冒頭にも視認リマインダが出る — 無視せず必ず PNG を開くこと。

## 対話シミュレーション (Quarto Live + Pyodide)

ブラウザだけで動く Python シミュレーションは [Quarto Live](https://r-wasm.github.io/quarto-live/) を使う。サーバー Python は不要。動作するサンプルは `quarto/textbook/_03_interactive_demo.qmd` を参照。

サンプル: `quarto/textbook/_03_interactive_demo.qmd` (matplotlib + FuncAnimation),
`quarto/textbook/_04_plotly_demo.qmd` (Plotly 静的 + アニメーション)。

**新規ページの作り方:**
1. qmd の YAML に `filters: [r-wasm/live]` を含める (親 `textbook.qmd` に書けば配下のパーシャルにも効く)
2. **追加 Python パッケージ** (Pyodide にプリインストール済以外、例: plotly, nbformat) は親 qmd の YAML `pyodide.packages` に列挙する。**セル内 `await micropip.install(...)` は禁止** (autorun 並列実行時に Pyodide の固定名 env を上書きし合って display 出力先が混線する)
3. `{ojs}` ブロックでスライダー (`Inputs.range(...)`) を定義、`tex` でラベルに LaTeX 数式
4. `{pyodide}` ブロックに `#| autorun: true` と `#| input: ["a", "b", ...]` を付け、スライダー値を Python 変数として受け取る
5. **日本語フォント (matplotlib)**: 描画セルの先頭に `_03_interactive_demo.qmd` の font-load ブロックをコピー — `pyfetch` で `assets/fonts/NotoSansJP-Regular.ttf` を取得して `font_manager.fontManager.addfont` で登録。**font setup を別セルにすると順序が保証されない** ので、**描画セルに inline する** こと。Plotly は OS フォントを使うため不要
6. `pyfetch` の URL は **`../../../assets/fonts/...` で固定** (qmd の階層に合わせて変えない — pyfetch は worker スクリプト基準で解決するため)

詳しい手順・dead-end・トラブルシュートは [docs/quarto-live.md](docs/quarto-live.md) を参照。

**警告抑制**: `warnings.simplefilter("ignore")` を font ロードと同じセルで呼ぶ。font 登録前後の `Glyph missing from current font` 警告を抑える。

**禁止事項:**
- ❌ `{pyodide}` セル内で `await micropip.install(...)` を呼ぶ (上記 race の原因)
- ❌ `{pyodide}` セルで `import shiny` / `import streamlit` (Pyodide では動かない、Quarto Live は素の numpy/matplotlib 中心)
- ❌ font setup を別セルに分ける (実行順序が保証されず描画セルが先に走るとエラー)
- ❌ `pyodide.resources` (qmd YAML) — Quarto Live の filter モードでは効かないので使わない
- ❌ Plotly figure に `fig.show()` を呼ぶ (Pyodide で renderer 検出に失敗。`fig` 最終式 1 行で OK)

## Code style

- **Quarto/qmd**:
  - 本文は `_*.qmd` (アンダースコア接頭辞 = レンダリング対象から除外) に分割し、`textbook.qmd` から `{{< include >}}`
  - パーシャルファイルに **YAML フロントマターを書かない** (親ファイルに集約)
  - `:::` (fenced div) の **閉じる前に空行必須** (`just fix` で自動修正可)
  - 数式: インライン `$...$`、ディスプレイ `$$...$$ {#eq-label}`、参照は `@eq-label`
  - 図表: Mermaid (`{mermaid}` ブロック)、PNG/JPG は `quarto/assets/images/`
  - **qmd の追記は小さく刻む**: 一度に大量の節 / 数式 / 図表を流し込まない。1 節ずつ (または 1 つの論理単位ずつ) 書いて `just check` または `just docs` のプレビューで確認 → 問題なければ次へ進む。理由: (1) OCR / 推論由来の誤りは少量ずつでないと見落とす、(2) Mermaid / LaTeX / fenced div の構文ミスは早期に発見すれば局所的に直せるが、巨大 diff の中では原因切り分けが困難、(3) `{{< include >}}` の追加 / 図表パス / 式番号は 1 つずつ視認確認するのが一番確実。「ファイル全体を一気に書き起こす」モードは使わない
- **Python** (`tools/` 配下): ruff format / lint, mypy, line-length 100
- **PDF リンク** (見出し横): `## タイトル [p.12](../assets/pdf/textbook.pdf#page=12) {#sec-anchor}`
  - ページ番号と物理ページのオフセットは PDF ごとに `just diagnose-pdf` で確認

## Testing

```bash
just check       # 品質ゲート (fmt + lint + typecheck + validate-docs + render-check + pytest)
just fix         # 自動修正 (fmt + lint + validate-docs --fix)
just validate-docs   # ドキュメント整合性検証 (Quarto / Mermaid / LaTeX)
just test        # pytest のみ
```

ドキュメント編集後は **必ず `just check` を実行**。エラーがあれば `just fix` → `just check` の順で。

## Commit & PR

- ブランチ: `feature/<topic>` または `fix/<topic>`
- コミットメッセージ: 日本語可、変更の **why** を 1 行目に
- PR は `main` 向けに、CI (3 OS × Python 3.12 + Quarto render-check) がグリーンになるまで merge しない

## Security & forbidden actions

- ❌ `pip install` を提案しない → `uv add <pkg>` または `uv sync --extra <name>` を使う
- ❌ `_*.qmd` に YAML ヘッダーを追加しない
- ❌ `quarto/textbook/chapter1.qmd` のような新規ルート qmd を作らない (パーシャルに分ける)
- ❌ `:::` の閉じる前の空行を省略しない
- ❌ Justfile に Unix 専用コマンド (`lsof`, `pkill`, `xargs`, `export PATH=`) を追加しない → 必ず `tools/*.py` 経由で cross-platform 化
- ❌ `quarto/assets/raw/`, `quarto/assets/private/`, `research/inbox/*/` 配下のファイルを commit しない (gitignore 済)

## Deployment

`main` ブランチへの push で `.github/workflows/publish.yml` が走り、`gh-pages` ブランチに自動デプロイ → GitHub Pages で公開。

教科書本文で optional 機能を使う場合は `publish.yml` の `uv sync` 行に `--extra <name>` を追記する (デフォルトは base のみで軽量化):

| 用途 | 追加すべき extra |
| --- | --- |
| Qiskit blocks | `--extra quantum` |
| Shinylive 対話 | `--extra shiny` |
| Jupyter compute / numpy / matplotlib | `--extra notebook` |
| 画像 PDF の OCR | `--extra ocr` |
| 数式 (LaTeX) 抽出 | `--extra math` |

## Tooling reference (Justfile)

| コマンド | 用途 |
| --- | --- |
| `just check-env` | ツール (uv / just / quarto / npm) 存在確認 |
| `just setup` | base 依存インストール (`uv sync` + `npm install`) |
| `just setup-all` | base + 全 extras (重い、~数 GB) |
| `just check` | 品質ゲート (fmt-check + lint + typecheck + validate-docs + render-check + test) |
| `just check-full` | `check` + 実 HTML レンダリング |
| `just fix` | 自動修正 (fmt + lint-fix + validate-docs --fix) |
| `just test [args]` | pytest |
| `just clean` | ビルド成果物削除 (cross-platform) |
| `just docs` | プレビューサーバー起動 (port 4312) |
| `just fix-docs` | プレビュー復旧 (Win/Mac/Linux 対応) |
| `just render-site` | HTML 実レンダリング |
| `just render-book-pdf` | PDF 実レンダリング |
| `just render-check` | 構文チェック (compute 実行なし) |
| `just validate-docs` | ドキュメント整合性検証 (Quarto/Mermaid/LaTeX) |
| `just validate-docs-fix` | 自動修正 |
| `just validate-docs-no-cache` | キャッシュを使わず再検証 |
| `just clear-validation-cache` | バリデーションキャッシュ削除 |
| `just diagnose-pdf <pdf>` | PDF 構造診断 (どの mode を選ぶか判断) |
| `just render-pdf <pdf> <s> <e>` | PDF ページ画像化 (画像のみ欲しい時に単独使用可) |
| `just extract-pdf <pdf> <s> <e>` | render-pdf を先に実行 → text/OCR + LaTeX を併走 (auto モード必須) |
| `just app <path>` | Streamlit アプリ起動 (任意) |
