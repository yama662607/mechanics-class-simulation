# Quarto Live (Pyodide) レシピ

ブラウザ内で動く Python ([Quarto Live](https://r-wasm.github.io/quarto-live/)) を
matplotlib / Plotly / 日本語フォントと組合せて使うときの **動作確認済の手順** と、
ハマりやすい落とし穴。

動作するサンプル:
- `quarto/textbook/_03_interactive_demo.qmd` (matplotlib + FuncAnimation)
- `quarto/textbook/_04_plotly_demo.qmd` (Plotly 静的 + アニメーション)

## 追加 Python パッケージは YAML の `pyodide.packages` で宣言する

Pyodide にプリインストール済 (numpy, matplotlib, pandas, sympy 等) **以外** の
パッケージを使うときは、**親 qmd の YAML** で列挙する。

```yaml
---
title: "本編"
filters:
  - r-wasm/live
pyodide:
  packages:
    - plotly
    - nbformat
    - jsonschema
---
```

セル内で `await micropip.install(...)` を呼ぶのは **避けること** (理由は次節)。
この YAML 経路なら Quarto Live が Pyodide 起動時にシリアルインストールを完了
させるので、各 `{pyodide}` セルは `import xxx` を直接書ける ⇒ Jupyter / VSCode に
コピペしても `pip install` 済前提で同じコードが動く。

### なぜセル内 `await micropip.install(...)` がダメか

Quarto Live は各 `{pyodide}` セルを独立した OJS observable にし、OJS は **並列に**
評価する。Pyodide ワーカは固定名 `"result"` の Python 環境を使い回す
(`live-runtime.js` の `PyodideEvaluator.process` / `envManager.create("result", "prep")`)。
セル1 が `await micropip.install` で yield した間に、OJS がセル2 の `process()` を
発火 → セル2 の `envManager.create("result", "prep")` がセル1 の env を上書き →
セル1 の `display()` 出力がセル2 の枠に出る、または消える。

これは **r-wasm/quarto-live の未報告バグ** (固定名 env が原因)。手動で個別に
Run Code を押せば順次実行されて再現しないが、`autorun: true` のページロード時に
発症する。`pyodide.packages` 経路を使えばセル本体に `await` が一切残らないので
race の発生源そのものが消え、回避できる。

## 動作する組合せ

1. **拡張**: `quarto/_extensions/r-wasm/live/` を git で同梱 (`r-wasm/quarto-live`)
2. **フォント**: Noto Sans JP の **static Regular** TTF (5.3 MB) を `quarto/assets/fonts/NotoSansJP-Regular.ttf` に配置
   - DL URL: `https://fonts.gstatic.com/s/notosansjp/v56/-F6jfjtqLzI2JPCgQBnw7HFyzSD-AsregP8VFBEj75s.ttf`
   - 検証: `file quarto/assets/fonts/NotoSansJP-Regular.ttf` → `TrueType Font data, 19 tables, 1st "BASE"` が正解
3. **`_quarto.yml`**: `project.resources` に `assets/fonts/**/*` を追加してビルド時に `_book/` へコピーさせる
4. **qmd の YAML**: `filters: [r-wasm/live]`。Book project では `engine: markdown` も併記して jupyter 依存を回避。include 構造の場合は **親 qmd 側** に書く
5. **OJS スライダー**: `viewof x = Inputs.range([...], {label: tex\`...\`, value: ...})`
6. **Pyodide ブロック**: `#| autorun: true` + `#| input: ["x", "y", ...]` で reactive
7. **フォントロードのイディオム** (描画セルに **inline**):

```python
#| autorun: true
#| input: ["a", "b"]
import os
import warnings
import matplotlib
from matplotlib import font_manager
from pyodide.http import pyfetch

warnings.simplefilter("ignore")  # font 登録前後の Glyph missing 警告を抑制

if not os.path.exists("/tmp/NotoSansJP.ttf"):
    # ⚠️ pyfetch は **worker スクリプト** (/site_libs/quarto-contrib/...) を base に解決する。
    # ページ URL 基準ではない。`../../../` で 3 段戻ればルートに到達する
    # (extra `..` はルートで吸収されるので qmd の階層に関係なく安全)。
    resp = await pyfetch("../../../assets/fonts/NotoSansJP-Regular.ttf")
    with open("/tmp/NotoSansJP.ttf", "wb") as f:
        f.write(await resp.bytes())
font_manager.fontManager.addfont("/tmp/NotoSansJP.ttf")  # キャッシュ済でも毎回呼ぶ
matplotlib.rcParams["font.family"] = "Noto Sans JP"
matplotlib.rcParams["axes.unicode_minus"] = False

# --- ここから描画 ---
import numpy as np
import matplotlib.pyplot as plt
# ...
```

## 検証済 dead-end (やってはいけないこと)

| Don't | Why |
| --- | --- |
| `pyfetch("../assets/fonts/...")` のように `..` を qmd の階層に合わせて減らす | pyfetch は **worker base** に対して解決するのでページ階層は無関係。`../../../` で固定 |
| Font setup を `edit: false, autorun: true` の **別セルに分ける** | 描画セルとの実行順序が保証されず、最初のフレームで Glyph missing 警告が大量発生 |
| qmd YAML の `pyodide.resources` で font 指定 | Quarto Live の filter モードでは効かない (network タブで fetch されない) |
| `ojs_define(font_ready=True)` で OJS dependency を作って描画セルが待つ | 最初のロード時 OJS が未定義エラー (`font_ready is not defined`) を出して止まる |
| Variable font (`NotoSansJP[wght].ttf`、9.6 MB) を使う | Pyodide の matplotlib FreeType が parse できず `In TTFont: unknown file format` |
| `{pyodide}` セル内で `import shiny` / `import streamlit` | Pyodide では動かない。Quarto Live は素の numpy / matplotlib 中心 |
| OJS の `while + Promises.delay` ループでスライダーを高速更新して `{pyodide}` を毎フレーム再実行 | matplotlib 再描画 (>100ms / frame) が間隔に追いつかず描画が固まる。さらに Quarto Live 専用なので Jupyter / VSCode にコピーすると動かない |
| `{pyodide}` セル内で `await micropip.install(...)` を呼ぶ (autorun 複数セル時) | OJS が並列実行し、Pyodide の固定名 env `"result"` が上書きされる。display 出力が別セル枠に出るか消える。**`pyodide.packages` YAML を使うこと** |
| Plotly figure に対し `fig.show()` を呼ぶ | Pyodide で renderer 検出に失敗する。最終式に `fig` を置けば IPython の `_repr_mimebundle_` 経由で描画される |
| Plotly 図を `HTML(fig.to_html(include_plotlyjs="cdn", full_html=False))` で埋め込む | innerHTML 経由で挿入される `<script>` タグはブラウザが実行しないので空 div になる。`fig` 最終式 + `pyodide.packages: [plotly, nbformat, jsonschema]` のほうが確実 |

## アニメーション

選択肢は 2 つ。標準的な Python のやり方なのでどちらも Jupyter / VSCode にコピーで動く。

### matplotlib + FuncAnimation
`matplotlib.animation.FuncAnimation` + `IPython.display.HTML(ani.to_jshtml())`。
フレームを Python 側で全部計算 → JS プレイヤーとして埋め込まれる:

- 再生 / 一時停止 / コマ送り / フレームスライダーが標準で付く
- 毎フレームの Pyodide 再実行が不要
- 出力は単一 PNG ベクター列なので印刷向き

サンプル: `_03_interactive_demo.qmd`。

### Plotly + animation_frame / frames
`px.line(df, animation_frame="frame", ...)` だけで再生 UI が自動生成される。
3D サーフェスや hover ツールチップは Plotly の方が得意。`pyodide.packages` で
`plotly nbformat jsonschema` の宣言が必要。

サンプル: `_04_plotly_demo.qmd`。

### 使い分け

| | matplotlib | Plotly |
| --- | --- | --- |
| コード量 | やや多い | 少ない |
| 日本語 | `font_manager.addfont` 必須 | OS フォント (追加設定不要) |
| インタラクション | コマ送り / 再生 / 停止 | + hover / pan / zoom |
| 印刷用ベクター | 強い | 弱い |
| 3D / 地理 / dashboard | 弱い | 強い |

紙に載せる図は matplotlib、ウェブで触らせる図は Plotly。

## 失敗時の典型症状と切り分け

- **`In FT2Font: Can not load face (unknown file format; error code 0x2)`**
  → 多くの場合 `pyfetch` が 404 を引いて HTML を TTF として読み込んでいる。
  preview のログで `(404: Not Found)` を grep し、`../../../` でルート相対になっているか確認
- **タイトルや軸ラベルが豆腐 (□)**
  → font が登録されていない。`addfont` を毎回呼んでいるか、`font.family` が `"Noto Sans JP"` か確認
- **編集しても変化しない**
  → include されるパーシャル (`_*.qmd`) は親 qmd を `touch` しないと preview が再レンダーしない場合がある。
  完全リセットは下記キャッシュクリア

## キャッシュトラブル時

```bash
rm -rf quarto/_book quarto/.quarto ~/Library/Caches/quarto
```
ブラウザは hard reload (Cmd+Shift+R)。
