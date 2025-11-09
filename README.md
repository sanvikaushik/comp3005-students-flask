# COMP 3005 Q1 — Students CRUD (PostgreSQL + Flask)

A minimal web app that demonstrates **CRUD** on a `students` table in **PostgreSQL**, with:

- DDL/DML scripts (`db/01_create_table.sql`, `db/02_insert.sql`)
- A small Flask UI for **Create / Read / Update / Delete**
- Safe DB access (**parameterized queries**) and **unique email** enforcement
- Fun demo :-)

> **Video demo:** 
> video shows: running the SQL in pgAdmin, then performing **INSERT / UPDATE / DELETE** in the Flask app and verifying each result in pgAdmin.

---

## 1) Repo Files for Flow

**app/**
- `flask_app.py` — Flask web application (CRUD logic + routes)
- `db.py` — PostgreSQL connection helper (loads environment variables)
- `test_connection.py` — quick script to verify DB connection
- **templates/**
  - `base.html` — shared layout template
  - `index.html` — main UI page (table + forms)

**db/**
- `01_create_table.sql` — DDL script (defines `students` table)
- `02_insert.sql` — initial sample data (John, Jane, Jim)

**root directory**
- `.env.example` — example environment configuration (copy → `.env`)
- `requirements.txt` — Python dependencies
- `README.md` — setup + demo instructions
- `.gitignore` — ignores `__pycache__/` and `.env`


---

## 2) Prerequisites

- **PostgreSQL 14+** and **pgAdmin**
- **Python 3.10+**
- A PostgreSQL user & database you can connect to

---

## 3) Requirements
- Flask==3.0.0
- psycopg2-binary==2.9.9
- python-dotenv==1.0.1
  
---

## 4) Database Setup (pgAdmin or psql)

### Option A — pgAdmin (GUI)

1. Open **pgAdmin**
2. Select or create a database (ex: `comp3005_a3`)
3. Run:

i.
`db/01_create_table.sql`

ii.
`db/02_insert.sql`


### Option B — psql (terminal)

```bash
psql -U postgres -d comp3005_a3 -f db/01_create_table.sql
psql -U postgres -d comp3005_a3 -f db/02_insert.sql
```

The table is now created by `db/01_create_table.sql` and initially populated by `db/02_insert.sql`:

`SELECT * FROM students;`
```
 student_id | first_name | last_name |         email          | enrollment_date
------------+------------+-----------+------------------------+-----------------
          1 | John       | Doe       | john.doe@example.com   | 2023-09-01
          2 | Jane       | Smith     | jane.smith@example.com | 2023-09-01
          3 | Jim        | Beam      | jim.beam@example.com   | 2023-09-02
(3 rows)
```
---

## 5) Environment Configuration

Copy the example env file:

```
cp .env.example .env
```

Edit .env to match your PostgreSQL setup:
```
PGHOST=localhost
PGPORT=5432
PGDATABASE=comp3005_a3
PGUSER=postgres
PGPASSWORD=your_password_here
```
5) Install & Run the App

```
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app/test_connection.py    # optional: verify DB connectivity
python app/flask_app.py          # run the app
```

Open the UI in your browser:
http://127.0.0.1:5000

---

## 6) CRUD Demonstration

| Operation  | Where to Perform It            | Verification                    |
| ---------- | ------------------------------ | ------------------------------- |
| **Read**   | Home page table                | Table updates immediately       |
| **Create** | "Add student" form             | Re-run `SELECT *` in pgAdmin    |
| **Update** | "Update email" form            | Verify updated email in pgAdmin |
| **Delete** | "Delete student" modal confirm | Row disappears in pgAdmin       |

All SQL uses `%s` placeholders → SQL injection safe.  
`UNIQUE(email)` in database prevents duplicates.

---

**Verify in pgAdmin:** Open pgAdmin → Query Tool and run:

```sql
SELECT * FROM students;
```
---

## 7) Troubleshooting

- Wrong password / cannot connect: Check .env

- Duplicate email error: Expected as email must be unique

- IDs keep rising: This is normal for SERIAL; use TRUNCATE … RESTART IDENTITY if needed

