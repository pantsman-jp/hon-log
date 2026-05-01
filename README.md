# ほんろぐ

[![Release-Build](https://github.com/pantsman-jp/hon-log/actions/workflows/release.yml/badge.svg)](https://github.com/pantsman-jp/hon-log/actions/workflows/release.yml)
[![GitHub release](https://img.shields.io/github/v/release/pantsman-jp/hon-log)](https://img.shields.io/github/v/release/pantsman-jp/hon-log/latest)
[![License](https://img.shields.io/github/license/pantsman-jp/hon-log)](https://github.com/pantsman-jp/hon-log/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/python-3.12-blue)](https://www.python.org)
[![GitHub Downloads](https://img.shields.io/github/downloads/pantsman-jp/hon-log/latest/total)](https://github.com/pantsman-jp/hon-log/releases/latest)

## English README is available [here](https://github.com/pantsman-jp/hon-log/blob/main/docs/README.en.md).

## 最新リリースは[こちら](https://github.com/pantsman-jp/hon-log/releases/latest)。

## 概要

**ほんろぐ** は、[九州工業大学図書館の貸出履歴（CSV）](https://www.lib.kyutech.ac.jp/library/ja/node/2061)を、あなただけのビジュアルな読書管理カタログへと変えるデスクトップアプリケーションです。

単なる履歴の表示にとどまらず、書影の自動取得、星評価、タグ付け、そして複数回の貸出記録を集約して管理することが可能です。

**※ アプリの使用（書影取得・アップデート確認）にはインターネット接続が必要です。**

## 主な機能

### 1. スマートな蔵書管理
- **重複の統合**: 同じ本を複数回借りた場合、一覧には1冊として表示。詳細画面ですべての貸出日を確認できます。
- **メタデータ取得**: OPACのURLからISBNを自動抽出し、国立国会図書館（NDL）から書影を自動取得します。
- **データ永続化**: 取り込んだデータや感想は SQLite データベースに保存され、オフラインでも閲覧可能です。

### 2. 充実の管理・評価システム
- **星評価**: 5段階のレーティング機能を搭載。
- **タグ付け**: 任意のキーワード（例：技術書、お気に入り）で書籍を分類できます。
- **感想ログ**: 本ごとの読書記録やメモを自由に保存できます。

### 3. 直感的なUI/UX
- **絞り込み・並び替え**: 「感想の有無」「特定のタグ」での抽出や、「評価順」「日付順」でのソートが即座に行えます。
- **統計機能**: メイン画面の「統計」ボタンから、著者別貸出頻度グラフや月別貸出冊数推移グラフを表示できます。
- **自動アップデート確認**: 起動時に GitHub API を介して最新バージョンの有無を通知します。
- **データベースメンテナンス**: 「全削除」ボタンにより、データの初期化も簡単に行えます。

### 4. クリーンなデータ管理
- **ポータブルな設計**: アプリの設定や画像は **ホームディレクトリ（`~/.hon-log/`）** に隔離して保存されます。アプリ本体のあるディレクトリを汚しません。

## 動作環境

- **OS**: Windows 10 / 11 (推奨)
- **Python**: 3.12 以上

### 実行ファイル化 (Windows)

開発者自身でビルドする場合は、以下のコマンドを使用してください。

```shell
pip install -r requirements.txt
pyinstaller src/main.py --onefile --noconfirm --name hon-log --icon="assets/img/favicon.ico" --add-data "assets;assets" --noconsole
```

## 使用方法

1. **起動**: `hon-log.exe` を実行します。
2. **インポート**: 「新規追加 / 更新」ボタンから、図書館からダウンロードした CSV を選択します。
3. **管理**: 書影をクリックして詳細画面を開き、評価や感想、タグを入力して「変更を保存」をクリックします。
4. **分析**: 画面上部の「統計」ボタンをクリックすると、貸出傾向分析画面が表示されます。
5. **整理**: 画面上部のコンボボックスを使い、目的の本を素早く見つけ出せます。

## データの保存場所

バックアップや移行の際は、以下のフォルダをコピーしてください。

- **Windows**: `C:\Users\<ユーザー名>\.hon-log\`

| ファイル/フォルダ | 内容 |
| ---: | :--- |
| `loans.db` | 貸出履歴、感想、評価、タグなどの全データ |
| `img/` | ローカルに保存された書影画像（`{isbn}.jpeg`） |

## CSV仕様

九工大図書館の標準エクスポート形式（UTF-8, シグネチャ付き推奨）に対応しています。

- 必須列: `タイトル`, `貸出日`, `巻情報`, `著者`, `出版社`, `年月情報`, `資料ID`, `URL`

## ライセンス・クレジット

- **アイコン**: [favicon.io](https://favicon.io/favicon-generator/) で生成
- **画像**: [いらすとや](https://www.irasutoya.com/) の素材を使用
- **データベース**: SQLite3

---
Copyright (c) 2026 [@pantsman](https://github.com/pantsman-jp)
