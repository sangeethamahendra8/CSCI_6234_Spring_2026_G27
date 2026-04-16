# Campus Library

A small **Flask** web app for a student library project. Members log in, open a **dashboard**, and use **seven use cases**: browse the catalog, borrow and return copies, extend a loan, place a hold, pay fines, and view their account. Data is stored in **SQLite** (`library_demo.db` on first run).

**Repository:** [github.com/Lalithasree-2599/Library_Management_System](https://github.com/Lalithasree-2599/Library_Management_System)

## Tech stack

- Python 3
- Flask 3.x
- Flask-SQLAlchemy (SQLAlchemy ORM)
- SQLite
- Jinja2 HTML templates

## Use cases and routes

| Use case        | Path |
|-----------------|------|
| Log in          | `/login` |
| Dashboard       | `/dashboard` |
| Browse Books    | `/browse-books` |
| Request Borrow  | `/request-borrow` |
| Return Item     | `/return-item` |
| Extend Loan     | `/extend-loan` |
| Place Hold      | `/place-hold` |
| Pay Fine        | `/pay-fine` |
| View Account    | `/view-account` |

Domain models include **Member**, **Book**, **BookCopy**, **Loan**, **Reservation**, **Fine**, **Payment**, and **Librarian** (seeded for the schema; only members sign in).

## Run locally

1. Clone the repo:
   ```bash
   git clone https://github.com/Lalithasree-2599/Library_Management_System.git
   cd Library_Management_System
   ```

2. Create a virtual environment (recommended), then install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Start the app:
   ```bash
   python app.py
   ```

4. Open **http://127.0.0.1:5000** in your browser (or the port shown in the terminal if `5000` is already in use).

On macOS, **port 5000** is sometimes taken by AirPlay Receiver; either turn that off in **System Settings → General → AirDrop & Handoff**, or run on another port, for example:

```bash
python -c "from app import app; app.run(debug=True, host='127.0.0.1', port=5002)"
```

## Database and sample data

- Tables are created automatically when the app starts (`db.create_all()`).
- If there are **no members** yet, the app seeds books, copies, two demo members, sample loans, a hold, and a sample fine.
- To **start over** with a fresh seed, stop the app, delete `library_demo.db`, and run the app again.
- `library_demo.db` is listed in `.gitignore` and is not committed.



## Project layout

```
├── app.py              # Routes, seed data, account sync
├── models.py           # SQLAlchemy models and helpers
├── requirements.txt
├── templates/          # Jinja HTML pages
├── static/             # CSS, images, JS
└── screenshots/        # Older UI screenshots (may not match current pages)
```

## Screenshots

Images under `screenshots/` may reflect an **earlier** version of the app. The current UI is defined by the templates in `templates/`.

## Contributing

Issues and pull requests are welcome for improvements or bug fixes.
