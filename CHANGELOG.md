# CHANGELOG

## v0.2.0 (2026-04-07)
### Added
- CSV import functionality for loan history
- SQLite database integration (`loans.db`)
- ISBN extraction from OPAC HTML
- Thumbnail image download from NDL Search
- Image storage in `img/` directory
- Fallback image support (`img/no-image.png`)
- Review (user comment) field support
- PySide6 GUI for displaying book thumbnails
- Grid layout (5 columns) for book display
- Tooltip on hover (title, author, publisher, loan date)
- Click interaction for editing reviews
- Update button to import additional CSV data

### Changed
- Database schema updated to include:
  - `isbn`
  - `image_path`
  - `review`
- CSV import now preserves existing data
- Duplicate prevention using `(material_id, loan_date)` constraint
- Image handling unified via `thumbnail.py`
- ISBN retrieval separated into `isbn.py`

## v0.1.0 (2026-04-07)
- start project
