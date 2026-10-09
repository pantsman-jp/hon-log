# ほんろぐ

[![Release-Build](https://github.com/pantsman-jp/hon-log/actions/workflows/release.yml/badge.svg)](https://github.com/pantsman-jp/hon-log/actions/workflows/release.yml)
[![GitHub release](https://img.shields.io/github/v/release/pantsman-jp/hon-log)](https://img.shields.io/github/v/release/pantsman-jp/hon-log/latest)
[![License](https://img.shields.io/github/license/pantsman-jp/hon-log)](https://github.com/pantsman-jp/hon-log/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/python-3.12-blue)](https://www.python.org)
[![GitHub Downloads](https://img.shields.io/github/downloads/pantsman-jp/hon-log/latest/total)](https://github.com/pantsman-jp/hon-log/releases/latest)

[English README](README.en.md)

## 概要

**ほんろぐ**は、[九州工業大学附属図書館の貸出履歴](https://www.lib.kyutech.ac.jp/library/ja/node/2061)から出力した CSV を、個人用の読書記録として閲覧・整理するデスクトップアプリです。貸出履歴を取り込み、同じ資料を1冊にまとめて表示します。

書影の取得と起動時の更新確認にはインターネット接続が必要です。取り込み済みの記録はローカルに保存されるため、閲覧・検索・編集はオフラインでも行えます。

## 主な機能

- CSV からの貸出履歴の取り込み（同じ貸出日は重複登録しません）
- 資料 ID ごとの集約表示と、全貸出日の表示
- OPAC ページからの ISBN 抽出と、NDL／Google Books を利用した書影の取得
- 評価（5段階）・タグ・感想の登録
- タイトル・著者・タグによる検索、感想の有無・タグによる絞り込み、日付・評価・タイトル順の並び替え
- 著者別冊数と月別冊数の統計表示
- GitHub Releases を使った新バージョンの通知

## ダウンロードと起動

[最新リリース](https://github.com/pantsman-jp/hon-log/releases/latest)から、ご利用の OS 向けファイルを取得してください。

- **Windows**: `hon-log.exe` をダウンロードして実行します。
- **macOS**: `hon-log-macos.zip` を展開し、`hon-log.app` をアプリケーションフォルダなどへ移して起動します。

macOS 版は現時点では Apple による署名・公証を行っていません。初回起動時に Gatekeeper の警告が表示されることがあります。その場合は、Finder でアプリを control キーを押しながらクリックして「開く」を選択してください。

## 開発環境

### 必要なもの

- Python 3.12 以上
- [uv](https://docs.astral.sh/uv/)

依存関係は `pyproject.toml` と `uv.lock` で管理しています。セットアップと起動は次のとおりです。

```shell
uv sync
uv run python -m src.main
```

## ビルド

リリース用の実行ファイルは、`v*.*.*` 形式のタグを push したときに GitHub Actions が作成します。Windows 版は単体の `.exe`、macOS 版は `.app` を含む ZIP として公開されます。

ローカルでビルドする場合は、各 OS 上で次のコマンドを実行します。

### Windows

```shell
uv run pyinstaller src/main.py --onefile --noconfirm --name hon-log --icon="assets/img/favicon.ico" --add-data "assets;assets" --noconsole
```

### macOS

```shell
uv run pyinstaller src/main.py --onedir --noconfirm --name hon-log --icon="assets/img/icon.icns" --add-data "assets:assets" --windowed --osx-bundle-identifier jp.pantsman.hon-log
ditto -c -k --sequesterRsrc --keepParent dist/hon-log.app dist/hon-log-macos.zip
```

## 使い方

1. 「新規追加 / 更新」を選び、図書館からダウンロードした CSV ファイルを指定します。
2. 一覧の書影をクリックすると詳細画面が開きます。
3. 詳細画面で評価、タグ、感想を入力し、「変更を保存」を選びます。
4. 上部の検索欄・絞り込み・並び替えを使って記録を探します。
5. 「統計」から著者別・月別の貸出冊数を確認します。

CSV の読み込みに失敗した場合は、エラーメッセージが表示されます。

## CSV について

九州工業大学附属図書館の標準的な貸出履歴 CSV（UTF-8、BOM 付きにも対応）を想定しています。`資料ID` は必須です。以下の列があると、より完全な記録を作成できます。

| 列名 | 用途 |
| --- | --- |
| `タイトル` | 一覧と詳細に表示する書名 |
| `著者` | 検索と統計に使用 |
| `出版社` | 詳細に表示 |
| `貸出日` | 一覧の並び替え、貸出履歴、月別統計に使用 |
| `資料ID` | 資料を識別し、重複を判定する必須列 |
| `URL` | OPAC を開く、ISBN・書影を取得するために使用 |
| `巻情報` | 詳細に表示 |
| `年月情報` | 詳細に表示 |

## データの保存場所

アプリのデータは、OS にかかわらずホームディレクトリ内の `~/.hon-log/` に保存します。バックアップまたは別の端末への移行時は、このフォルダをコピーしてください。

| ファイル／フォルダ | 内容 |
| --- | --- |
| `loans.db` | 貸出履歴、感想、評価、タグを保存する SQLite データベース |
| `img/` | 取得した書影のキャッシュ |

## ライセンス・クレジット

- アイコン: [favicon.io](https://favicon.io/favicon-generator/)
- 画像: [いらすとや](https://www.irasutoya.com/)
- データベース: SQLite

---

Copyright (c) 2026 [@pantsman](https://github.com/pantsman)
