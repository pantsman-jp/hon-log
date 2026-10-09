# Honlog

[![Release-Build](https://github.com/pantsman-jp/hon-log/actions/workflows/release.yml/badge.svg)](https://github.com/pantsman-jp/hon-log/actions/workflows/release.yml)
[![GitHub release](https://img.shields.io/github/v/release/pantsman-jp/hon-log)](https://img.shields.io/github/v/release/pantsman-jp/hon-log/latest)
[![License](https://img.shields.io/github/license/pantsman-jp/hon-log)](https://github.com/pantsman-jp/hon-log/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/python-3.12-blue)](https://www.python.org)
[![GitHub Downloads](https://img.shields.io/github/downloads/pantsman-jp/hon-log/latest/total)](https://github.com/pantsman-jp/hon-log/releases/latest)

[日本語 README](https://github.com/pantsman-jp/hon-log/blob/main/README.md)

## Overview

**Honlog** is a desktop application for viewing and organizing personal reading records from CSV files exported from the [Kyushu Institute of Technology Library](https://www.lib.kyutech.ac.jp/library/ja/node/2061). It imports loan history and consolidates multiple loans of the same item into a single entry.

An internet connection is required to retrieve book covers and check for updates at startup. Imported records are stored locally, allowing you to browse, search, and edit them offline.

## Features

* Import loan history from CSV files (duplicate entries with the same loan date are skipped)
* Consolidate records by item ID and display all loan dates
* Extract ISBNs from OPAC pages and retrieve book covers using the National Diet Library (NDL) and Google Books
* Record ratings (five-point scale), tags, and reviews
* Search by title, author, and tag; filter by review availability and tags; sort by date, rating, and title
* View statistics on the number of books borrowed by author and by month
* Receive notifications about new versions via GitHub Releases

## Download and Launch

Download the appropriate file for your operating system from the [latest release](https://github.com/pantsman-jp/hon-log/releases/latest).

* **Windows**: Download and run `hon-log.exe`.
* **macOS**: Extract `hon-log-macos.zip`, move `hon-log.app` to the Applications folder or another location, and launch it.

The macOS version is currently neither signed nor notarized by Apple. Gatekeeper may display a warning on the first launch. If this happens, control-click the app in Finder and select **Open**.

## Development Environment

### Requirements

* Python 3.12 or later
* [uv](https://docs.astral.sh/uv/)

Dependencies are managed using `pyproject.toml` and `uv.lock`. To set up and launch the application, run:

```shell
uv sync
uv run python -m src.main
```

## Building

Release executables are built by GitHub Actions when a tag matching the `v*.*.*` pattern is pushed. The Windows version is distributed as a standalone `.exe`, while the macOS version is distributed as a ZIP archive containing the `.app` bundle.

To build locally, run the following commands on the respective operating systems.

### Windows

```shell
uv run pyinstaller src/main.py --onefile --noconfirm --name hon-log --icon="assets/img/favicon.ico" --add-data "assets;assets" --noconsole
```

### macOS

```shell
uv run pyinstaller src/main.py --onedir --noconfirm --name hon-log --icon="assets/img/icon.icns" --add-data "assets:assets" --windowed --osx-bundle-identifier jp.pantsman.hon-log
ditto -c -k --sequesterRsrc --keepParent dist/hon-log.app dist/hon-log-macos.zip
```

## Usage

1. Select **Add New / Update** and choose the CSV file downloaded from the library.
2. Click a book cover in the list to open its details.
3. Enter a rating, tags, and a review on the details screen, then select **Save Changes**.
4. Use the search bar, filters, and sorting options at the top to find records.
5. Select **Statistics** to view the number of books borrowed by author and by month.

If the CSV file cannot be imported, an error message will be displayed.

## CSV Format

The application is designed for standard loan history CSV files from the Kyushu Institute of Technology Library, encoded in UTF-8, including files with a UTF-8 BOM.

The `資料ID` (Item ID) column is required. The following columns help create more complete records.

| Column                          | Purpose                                                       |
| ------------------------------- | ------------------------------------------------------------- |
| `タイトル` (Title)                  | Book title displayed in the list and details                  |
| `著者` (Author)                   | Used for searching and statistics                             |
| `出版社` (Publisher)               | Displayed in the details                                      |
| `貸出日` (Loan Date)               | Used for sorting, loan history, and monthly statistics        |
| `資料ID` (Item ID)                | Required; identifies items and detects duplicates             |
| `URL`                           | Used to open the OPAC page and retrieve ISBNs and book covers |
| `巻情報` (Volume Information)      | Displayed in the details                                      |
| `年月情報` (Year/Month Information) | Displayed in the details                                      |

## Data Storage

Application data is stored in `~/.hon-log/` within the user's home directory on all supported operating systems. To back up your data or transfer it to another device, copy this folder.

| File / Directory | Contents                                                            |
| ---------------- | ------------------------------------------------------------------- |
| `loans.db`       | SQLite database containing loan history, reviews, ratings, and tags |
| `img/`           | Cache for retrieved book covers                                     |

## License and Credits

* Icon: [favicon.io](https://favicon.io/favicon-generator/)
* Images: [Irasutoya](https://www.irasutoya.com/)
* Database: SQLite

---

Copyright (c) 2026 [@pantsman](https://github.com/pantsman)
