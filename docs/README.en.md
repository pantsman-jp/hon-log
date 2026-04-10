# Hon-Log

[日本語](https://github.com/pantsman-jp/hon-log/blob/main/README.md)

The latest version is available [here](https://github.com/pantsman-jp/hon-log/releases/latest).

## Overview
This desktop application uses the [Kyushu Institute of Technology Library Loan History (CSV)](https://www.lib.kyutech.ac.jp/library/ja/node/2061) to perform the following tasks:

- Convert loan history to a database (SQLite)
- Automatically retrieve ISBNs
- Retrieve and save book cover images
- Grid display of book cover list (PySide6)
- Saving and editing reviews

**An internet connection is required to use the app.**

## Main Features

### 1. CSV to DB Conversion
- Reads CSV files and registers data in an SQLite database
- Duplicate data is not registered (determined by material_id + loan_date)

### 2. ISBN Retrieval
- Retrieves HTML from the OPAC URL
- Automatically extracts ISBNs

### 3. Book Cover Retrieval
- Generates book cover URLs from ISBNs
- Downloads and saves images

### 4. GUI Display
- Displays book covers in a grid (5 columns)
- Displays book titles below

### 5. Interaction
- Hover -> Display detailed information
- Click -> Enter and save review

## System Requirements
`Python 3.12`

### Required Packages
```zsh
pip install -r requirements.txt
```

## Usage

### 1. First Launch
```zsh
python -m src.main
```

- A CSV selection dialog will appear
- Selecting a CSV file will create the database

#### Note
The first launch takes a long time to retrieve book covers.

### 2. Normal Launch (2nd time and beyond)
```zsh
python -m src.main
```

- Data is loaded from the database and displayed

### 3. Update
- Click the “Update” button
- Select a new CSV file
- Only new data is added (existing data is retained)

## CSV Specifications
Must include the following columns:  
- Title
- Checkout Date
- Volume Information
- Author
- Publisher
- Year/Month Information
- Material ID
- URL

### Notes
- Leading spaces and BOMs in headers are normalized internally

## DB Specifications
| Column Name | Description |
| ---: | :--- |
| id | Primary Key |
| title | Title |
| loan_date | Loan Date |
| volume | Volume Information |
| author | Author |
| publisher | Publisher |
| published_at | Publication Date |
| material_id | Material ID |
| url | URL |
| isbn | ISBN |
| image_path | Book Cover Path |
| review | Review |

## Book Cover Specifications

### Storage Location
```
cache/img/{isbn}.jpg
```

### If No Cover Image Is Available
```
cache/img/no-image.png
```

---
Copyright (c) 2026 [@pantsman](https://github.com/pantsman-jp)
