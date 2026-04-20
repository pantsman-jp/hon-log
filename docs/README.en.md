# hon-log

[![Release-Build](https://github.com/pantsman-jp/hon-log/actions/workflows/release.yml/badge.svg)](https://github.com/pantsman-jp/hon-log/actions/workflows/release.yml)
[![GitHub release](https://img.shields.io/github/v/release/pantsman-jp/hon-log)](https://img.shields.io/github/v/release/pantsman-jp/hon-log/latest)
[![License](https://img.shields.io/github/license/pantsman-jp/hon-log)](https://github.com/pantsman-jp/hon-log/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/python-3.12-blue)](https://www.python.org)
[![GitHub Downloads](https://img.shields.io/github/downloads/pantsman-jp/hon-log/latest/total)](https://github.com/pantsman-jp/hon-log/releases/latest)

## 日本語の README は[こちら](https://github.com/pantsman-jp/hon-log/blob/main/README.md)

## [Latest Release](https://github.com/pantsman-jp/hon-log/releases/latest)

## Overview

**hon-log** is a desktop application that transforms your [Kyushu Institute of Technology (Kyutech) Library loan history (CSV)](https://www.lib.kyutech.ac.jp/library/ja/node/2061) into your own visual reading management catalog.

Beyond just displaying history, it automatically fetches book covers, allows star ratings and tagging, and consolidates multiple loan records for the same book into a single entry.

**Note: An internet connection is required for fetching book covers and checking for updates.**

## Key Features

### 1. Smart Collection Management
- **Consolidated View**: Multiple loans of the same book are grouped into one entry in the main list. You can view the full history of loan dates in the detail view.
- **Metadata Extraction**: Automatically extracts ISBNs from OPAC URLs and fetches book covers from the National Diet Library (NDL) API.
- **Persistent Data**: Imported data and reviews are stored in a local SQLite database, allowing offline browsing.

### 2. Comprehensive Rating & Tagging
- **Star Ratings**: Integrated 5-star rating system for your books.
- **Custom Tags**: Classify books using any keywords (e.g., "Technical," "Favorites").
- **Review Logs**: Save reading logs, personal notes, and reviews for each book.

### 3. Intuitive UI/UX
- **Filter & Sort**: Instantly filter by "Reviewed/Unreviewed" or "Specific Tags," and sort by "Rating," "Date," or "Title."
- **Auto Update Checker**: Notifies you of the latest releases via GitHub API on startup.
- **DB Maintenance**: Easily reset your data using the "Clear All" button.

### 4. Clean Data Management
- **Portable Design**: App settings and images are isolated in the **home directory (`~/.hon-log/`)**, keeping the application directory clean.

## System Requirements

- **OS**: Windows 10 / 11 (Recommended)
- **Python**: 3.12 or higher

### Building the Executable (Windows)

To build the app yourself, use the following commands:

```shell
pip install -r requirements.txt
pyinstaller src/main.py --onefile --noconfirm --name hon-log --icon="assets/img/favicon.ico" --add-data "assets;assets" --noconsole
```

## How to Use

1. **Launch**: Run `hon-log.exe`.
2. **Import**: Click the "Import / Update" button and select the CSV file downloaded from the library.
3. **Manage**: Click on a book cover to open the details, enter your rating, tags, or review, and click "Save Changes."
4. **Organize**: Use the combo boxes at the top to quickly find the books you're looking for.

## Data Storage Location

To backup or migrate your data, copy the following folder:

- **Windows**: `C:\Users\<Username>\.hon-log\`

| File/Folder | Description |
| ---: | :--- |
| `loans.db` | SQLite database containing all history, reviews, ratings, and tags. |
| `img/` | Cached book cover images (`{isbn}.jpeg`). |

## CSV Specifications

Compatible with the standard export format of Kyutech Library (UTF-8 with BOM recommended).

- Required Columns: `Title`, `Loan Date`, `Volume`, `Author`, `Publisher`, `Published At`, `Material ID`, `URL`

## Licenses & Credits

- **Icon**: Generated via [favicon.io](https://favicon.io/favicon-generator/)
- **Illustration**: Materials from [Irasutoya](https://www.irasutoya.com/)
- **Database**: SQLite3

---
Copyright (c) 2026 [@pantsman](https://github.com/pantsman-jp)
