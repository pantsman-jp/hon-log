# ほんろぐ

[![Release-Build](https://github.com/pantsman-jp/hon-log/actions/workflows/release.yml/badge.svg)](https://github.com/pantsman-jp/hon-log/actions/workflows/release.yml)
[![GitHub release](https://img.shields.io/github/v/release/pantsman-jp/hon-log)](https://github.com/pantsman-jp/hon-log/releases/latest)
[![License](https://img.shields.io/github/license/pantsman-jp/hon-log)](https://github.com/pantsman-jp/hon-log/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org)
[![GitHub Downloads (all assets, latest release)](https://img.shields.io/github/downloads/pantsman-jp/hon-log/latest/total)](https://github.com/pantsman-jp/hon-log/releases/latest)

## [English](https://github.com/pantsman-jp/hon-log/blob/main/docs/README.en.md)

## 最新リリースは[こちら](https://github.com/pantsman-jp/hon-log/releases/latest)。

## 概要

本アプリは、[九州工業大学図書館の貸出履歴（CSV）](https://www.lib.kyutech.ac.jp/library/ja/node/2061)をもとに以下を行うデスクトップアプリケーションです。

- 貸出履歴のデータベース化（SQLite）
- ISBNの自動取得
- 書影画像の取得・保存
- 書影一覧のグリッド表示（PySide6）
- 感想（レビュー）の保存・編集

**アプリの使用にはインターネット接続が必要です。**

## 主な機能

### 1. CSV -> DB変換

- CSV を読み込み、SQLite データベースへ登録
- 重複データは登録されない（`material_id` + `loan_date` で判定）

### 2. ISBN 取得

- OPAC の URL から ISBN を自動抽出

### 3. 書影取得

- 国立国会図書館（NDL）の書影 API を利用
- 取得した画像はローカルにキャッシュし、オフライン時でも表示可能

### 4. クリーンなデータ管理

- **ホームディレクトリ（`~/.hon-log/`）** にデータベースと書影を保存
- アプリ実行ファイルのあるディレクトリを汚しません

## 動作環境

`Python 3.12`

### 必要パッケージ

```shell
pip install -r requirements.txt
```

### 実行ファイル化 (Windows)

```shell
pyinstaller src/main.py --onefile --noconfirm --name hon-log --icon="assets/img/favicon.ico" --add-data "assets;assets" --noconsole
```

## 使用方法

### 1. 起動

```shell
python -m src.main
```

またはビルドした `hon-log.exe` を実行します。

- 初回起動時: UIが表示されます。「新規追加・更新」ボタンからCSVを選択してください。
- 2回目以降: 以前取り込んだデータが自動的に表示されます。

### 2. 更新

- 「新規追加・更新」ボタンをクリックし、新しい CSV を選択します。
- 新規データのみが追加され、既存のデータや感想（レビュー）は保持されます。

## データの保存場所

アプリの設定やデータは以下の場所に保存されます。バックアップを取る際はこのフォルダをコピーしてください。

- Windows: `C:\Users\Username\.hon-log\`

| ファイル/フォルダ | 内容 |
| ---: | :--- |
| `loans.db` | 貸出履歴データおよび感想 |
| `img/` | ダウンロードされた書影画像（`{isbn}.jpeg`） |

## CSV仕様

以下の列を含む必要があります（九工大図書館の標準エクスポート形式に対応）：

- タイトル、貸出日、巻情報、著者、出版社、年月情報、資料ID、URL

## ライセンス・関連

- アプリのアイコンは [favicon.io](https://favicon.io/favicon-generator/) で作成しました
- 画像は[いらすとや](https://www.irasutoya.com/)のものを使用しています

---
Copyright (c) 2026 [@pantsman](https://github.com/pantsman-jp)
