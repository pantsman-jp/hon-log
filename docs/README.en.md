# Hon-Log

[日本語](https://github.com/pantsman-jp/hon-log/blob/main/README.md)

The latest release is [here](https://github.com/pantsman-jp/hon-log/releases/latest).

## Overview

This desktop application uses the [Kyushu Institute of Technology Library Loan History (CSV)](https://www.lib.kyutech.ac.jp/library/ja/node/2061) to perform the following tasks:

- Convert loan history to a database (SQLite)
- Automatically retrieve ISBNs
- Retrieve and save book cover images
- Display a grid view of book covers (PySide6)
- Saving and editing reviews

**An internet connection is required to use this app.**

## Main Features

### 1. CSV to DB Conversion

- Reads CSV files and registers them in an SQLite database
- Duplicate data is not registered (determined by `material_id` + `loan_date`)

### 2. ISBN Retrieval

- Automatically extracts ISBNs from OPAC URLs

### 3. Book Cover Retrieval

- Uses the National Diet Library (NDL) book cover API
- Retrieved images are cached locally and can be viewed even offline

### 4. Clean Data Management

- Saves the database and book covers to the **home directory (`~/.hon-log/`)**
- Does not clutter the directory containing the app executable

## System Requirements

`Python 3.12`

### Required Packages

```shell
pip install -r requirements.txt
```

### Creating an Executable (Windows)

```shell
pyinstaller src/main.py --onefile --noconfirm --name hon-log --icon=“assets/img/favicon.ico” --add-data “assets/img;assets/img” --noconsole
```

## Usage

### 1. Launching

```shell
python -m src.main
```

Or run the built `hon-log.exe` file.

- First launch: The UI will appear. Select a CSV file using the “Add New/Update” button.
- Subsequent launches: Previously imported data will be displayed automatically.

### 2. Update

- Click the “Add New/Update” button and select a new CSV file.
- Only new data will be added; existing data and reviews will be retained.

## Data Storage Location

App settings and data are stored in the following location. Please copy this folder when creating a backup.

- Windows: `C:\Users\Username\.hon-log\`

| File/Folder | Contents |
| ---: | :--- |
| `loans.db` | Loan history data and reviews |
| `img/` | Downloaded book cover images (`{isbn}.jpeg`) |

## CSV Specifications

The file must include the following columns (compatible with Kyushu Institute of Technology Library’s standard export format):

- Title, Loan Date, Volume Information, Author, Publisher, Year/Month Information, Material ID, URL

## License & Related Information

- The app icon was created using [favicon.io](https://favicon.io/favicon-generator/).
- Images are sourced from [Irasutoya](https://www.irasutoya.com/).

---
Copyright (c) 2026 [@pantsman](https://github.com/pantsman-jp)
