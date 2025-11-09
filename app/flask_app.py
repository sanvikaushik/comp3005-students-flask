# Notes:
# - We rely on PostgreSQL constraints (e.g., UNIQUE(email)) to enforce data integrity.
# - We catch psycopg2 exceptions and translate them into user-facing messages.
# - All SQL uses parameterized placeholders (%s) to prevent SQL injection.

from flask import Flask, render_template, request, redirect, url_for, flash
import psycopg2                  # DB driver
from db import get_conn          # returns a psycopg2 connection
import re                        # for simple email format validation

app = Flask(__name__)
app.secret_key = "change-me"     # required for flash() message queue

# --------------------------- utility: validation + messaging ---------------------------

def email_ok(s: str) -> bool:
    """
    Lightweight email format check.
    This is only a UI-level check for obvious errors.
    The *real* enforcement of uniqueness happens in the DB via UNIQUE(email).
    """
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", (s or "").strip()))

def ok(msg: str):   flash(f"(+) {msg}", "success")
def err(msg: str):  flash(f"(!) {msg}", "danger")

# --------------------------- READ (R in CRUD) ---------------------------

def fetch_all():
    """
    SELECT all rows for display.
    Uses a read-only query inside a managed connection+cursor block.
    Psycopg2 connection context manager:
      - commits on normal exit (not strictly needed for SELECT)
      - rolls back if an exception bubbles up
    """
    with get_conn() as c, c.cursor() as cur:
        cur.execute("""
            SELECT student_id, first_name, last_name, email, enrollment_date
            FROM students
            ORDER BY student_id;
        """)
        return cur.fetchall()

@app.get("/")
def index():
    """
    Renders the main page with the current snapshot of the table.
    This is the "Read" part of CRUD surfaced in the UI.
    """
    return render_template("index.html", students=fetch_all())

# --------------------------- CREATE (C in CRUD) ---------------------------

@app.post("/add")
def add():
    """
    INSERT a new student.
    Flow:
      1) Collect and sanitize inputs
      2) Do basic UI-level validation (required fields, email format)
      3) Attempt INSERT using parameterized SQL
      4) Handle DBMS-level errors, especially UNIQUE(email) violations
    Curriculum points:
      - Input validation at the app layer prevents obvious bad data
      - Data integrity is ultimately enforced by DB constraints
      - UNIQUE violation in PostgreSQL → SQLSTATE '23505'
    """
    first = (request.form.get("first_name") or "").strip()
    last  = (request.form.get("last_name") or "").strip()
    email = (request.form.get("email") or "").strip().lower()
    date  = (request.form.get("enrollment_date") or "").strip() or None  # allow NULL

    # App-layer validation for required fields and basic email shape.
    # These checks improve UX, but are NOT a replacement for DB constraints.
    if not first:
        err("first_name required")
        return redirect(url_for("index"))
    if not last:
        err("last_name required")
        return redirect(url_for("index"))
    if not email:
        err("email required")
        return redirect(url_for("index"))
    if not email_ok(email):
        err(f'email invalid — got “{email}” → use name@domain.tld')
        return redirect(url_for("index"))

    try:
        # Transaction scope:
        # - The `with get_conn()` context wraps a transaction.
        # - On success: commit; on exception: automatic rollback.
        with get_conn() as c, c.cursor() as cur:
            cur.execute("""
                INSERT INTO students(first_name, last_name, email, enrollment_date)
                VALUES (%s, %s, %s, %s);
            """, (first, last, email, date))

        # If we reach here, INSERT succeeded and was committed.
        ok("student added")

    except psycopg2.Error as e:
        # Map DBMS errors to user-friendly messages.
        # PostgreSQL SQLSTATE codes:
        #   - 23505: unique_violation (e.g., UNIQUE(email))
        #   - 23514: check_violation (if you add CHECK constraints)
        #   - 23503: foreign_key_violation (not used here but common in CRUD)
        if e.pgcode == "23505":
            # This is the canonical way to prevent duplicates:
            # let the UNIQUE(email) constraint *reject* conflicting values.
            err(f'email already exists — “{email}” → choose a unique email')
        else:
            # Generic fallback: surface the DB error type for debugging in coursework
            err(f"db error (add): {e}")
    return redirect(url_for("index"))

# --------------------------- UPDATE (U in CRUD) ---------------------------

@app.post("/update_email")
def update_email():
    """
    UPDATE a student's email by student_id.
    Two layers of protection against duplicate emails:
      (1) App-level format validation (email_ok),
      (2) DB-level UNIQUE(email) constraint (authoritative).
    Behavior:
      - If student_id does not exist, no rows updated → rowcount == 0
      - If new email collides with existing row's email, DB raises 23505
    """
    sid   = (request.form.get("student_id") or "").strip()
    email = (request.form.get("new_email") or "").strip().lower()

    # Validate student_id is a positive integer before touching the DB.
    if not sid.isdigit():
        err(f'student_id must be a positive integer — got “{sid}”')
        return redirect(url_for("index"))
    # Validate email syntax; prevents obvious mistakes but does not guarantee deliverability.
    if not email_ok(email):
        err(f'email invalid — got “{email}” → use name@domain.tld')
        return redirect(url_for("index"))

    try:
        with get_conn() as c, c.cursor() as cur:
            # Parameterized UPDATE: the WHERE clause scopes the change to a single id.
            cur.execute(
                "UPDATE students SET email=%s WHERE student_id=%s;",
                (email, int(sid))
            )

            # rowcount tells us whether an UPDATE actually occurred.
            # If 0, the id didn't exist → we report that explicitly.
            if cur.rowcount == 0:
                err(f'no student with id {sid} → pick an id from the table')
            else:
                ok("email updated")

    except psycopg2.Error as e:
        if e.pgcode == "23505":
            # Attempted to set email to a value that already exists on another row.
            # The DB's UNIQUE(email) constraint blocks this to preserve key semantics.
            err(f'that email is already in use — “{email}”')
        else:
            err(f"db error (update): {e}")
    return redirect(url_for("index"))

# --------------------------- DELETE (D in CRUD) ---------------------------

@app.post("/delete")
def delete():
    """
    DELETE a student by student_id.
    Behavior:
      - If id exists → one row deleted → rowcount == 1
      - If id does not exist → 0 rows deleted → we inform the user
    Curriculum note:
      - If there were FOREIGN KEYs referencing students.student_id and they were NOT
        set to ON DELETE CASCADE, PostgreSQL would raise 23503 (foreign_key_violation).
        In that case you must either:
          a) delete/modify dependent rows first, or
          b) define ON DELETE CASCADE if the data model allows it.
    """
    sid = (request.form.get("student_id") or "").strip()
    if not sid.isdigit():
        err(f'student_id must be a positive integer — got “{sid}”')
        return redirect(url_for("index"))

    # This simple delete does not need a try/except unless you expect FK errors, etc.
    with get_conn() as c, c.cursor() as cur:
        cur.execute("DELETE FROM students WHERE student_id=%s;", (int(sid),))
        if cur.rowcount:
            ok("student deleted")
        else:
            err(f'no student with id {sid} → pick an id from the table')
    return redirect(url_for("index"))

# --------------------------- dev server ---------------------------

if __name__ == "__main__":
    # debug=True enables Flask reloader and shows stack traces during development
    app.run(port=5000, debug=True)
