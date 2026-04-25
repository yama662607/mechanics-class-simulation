# 物理学基礎論A (力学) シミュレーション学習資料

京都大学「物理学基礎論A」の補足資料として、主に力学のシミュレーションを学習するためのプロジェクトです。

## Structure

```text
mechanics-class-simulation/
├── quarto/
│   ├── index.qmd
│   ├── theory/
│   │   ├── textbook.qmd
│   │   └── topics/
│   ├── assets/
│   │   ├── raw/lectures/
│   │   ├── pdf/lectures/
│   │   └── images/lectures/
│   └── templates/
├── research/
│   └── inbox/               ← 素材ドロップ先
│       ├── YYYY-MM-DD_xxx/  ← 日付+内容でフォルダを作る
│       └── manifest.yml     ← 素材の対応表
├── tools/
├── tests/
├── Justfile
└── README.md
```

## Commands

```bash
just check-env       # 開発環境のチェック
just docs            # 開発サーバー起動
just validate-docs   # ドキュメント検証
just check           # 全品質チェック
just render          # HTML ビルド
just check-full      # 全チェック + ビルド
just extract-pdf <path>         # PDF → テキスト + 画像
just extract-pdf <path> --ocr   # + OCR（要 Tesseract）
```

## 素材の追加手順

1. `research/inbox/YYYY-MM-DD_トピック名/` フォルダを作成
2. 講義資料、板書写真、手書き画像などを入れる
3. PDF は `just extract-pdf` で画像化・テキスト抽出する
4. AI に画像を読ませて qmd の内容を執筆
5. qmd から参照する図は `quarto/assets/images/lectures/` に配置
6. `research/inbox/manifest.yml` に素材の対応を記録

```
research/inbox/YYYY-MM-DD_xxx/   ← 生素材を投入
    ↓ (AI が読み取り・テキスト抽出)
quarto/theory/topics/xxx/        ← qmd に執筆
    ↓ (qmd から参照する画像があれば)
quarto/assets/images/lectures/   ← 整理済み画像を配置
```

## Writing Policy

- 本文は講義回ではなくトピック単位（質点の力学、剛体の力学など）で整理します。
- 未処理の講義素材は `research/inbox/YYYY-MM-DD_トピック名/` に置きます。
- qmd から参照する整理済み素材は `quarto/assets/pdf/lectures/` または `quarto/assets/images/lectures/` に置きます。
- `quarto/theory/topics/_*.qmd` は YAML ヘッダーなしの断片ファイルにします。
- 講義由来の PDF・画像は私用資料として `.gitignore` で除外します。必要なら `.gitkeep` だけを管理します。
- 素材の対応関係は `research/inbox/manifest.yml` に記録します。
