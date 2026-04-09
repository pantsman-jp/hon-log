# ほんろぐ

## 概要
本アプリは、[九州工業大学図書館の貸出履歴（CSV）](https://www.lib.kyutech.ac.jp/library/ja/node/2061)をもとに以下を行うデスクトップアプリケーションです。

- 貸出履歴のデータベース化（SQLite）
- ISBNの自動取得
- 書影画像の取得・保存
- 書影一覧のグリッド表示（PySide6）
- 感想（レビュー）の保存・編集

## 主な機能

### 1. CSV -> DB変換
- CSV を読み込み、SQLite データベースへ登録
- 重複データは登録されない（material_id + loan_date で判定）

### 2. ISBN 取得
- OPAC のURL から HTML を取得
- ISBN を自動抽出

### 3. 書影取得
- ISBN から書影 URL を生成
- 画像をダウンロードして保存

### 4. GUI表示
- 書影をグリッド表示（5列）
- 下に書名を表示

### 5. インタラクション
- ホバー -> 詳細情報表示
- クリック -> 感想入力・保存

## 動作環境
`Python 3.12`

### 必要パッケージ
```zsh
pip install -r requirements.txt
```

## 使用方法

### 1. 初回起動
```zsh
python -m src.main
```

- CSV 選択ダイアログが表示される
- CSV を選択すると D が作成される

#### 注意
初回起動時は書影取得のため、大変時間がかかります。

### 2. 通常起動（2回目以降）
```zsh
python -m src.main
```

- DB からデータを読み込み表示

### 3. 更新
- 「更新」ボタンをクリック
- 新しい CSV を選択
- 新規データのみ追加される（既存データ保持）

## CSV仕様
以下の列を含む必要があります：  
- タイトル
- 貸出日
- 巻情報
- 著者
- 出版社
- 年月情報
- 資料ID
- URL

### 注意
- ヘッダの空白や BOM は内部で正規化される

## DB仕様
| カラム名 | 説明 |
| --- | --- |
| id | 主キー |
| title | タイトル |
| loan_date | 貸出日 |
| volume | 巻情報 |
| author | 著者 |
| publisher | 出版社 |
| published_at | 出版年月 |
| material_id | 資料ID |
| url | URL |
| isbn | ISBN |
| image_path | 書影パス |
| review | 感想 |

## 書影仕様

### 保存先
```
cache/img/{isbn}.jpg
```

### 書影がない場合
```
cache/img/no-image.png
```

## 注意
- インターネット接続が必要

---
Copyright (c) 2026 [@pantsman](https://github.com/pantsman-jp)
