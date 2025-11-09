from flask import Flask, render_template, request, redirect, url_for, flash
import psycopg2
from db import get_conn
import re

app = Flask(__name__)
app.secret_key = "change-me"

def email_ok(s: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", (s or "").strip()))

def ok(msg: str):   flash(f"(+) {msg}", "success")
def err(msg: str):  flash(f"(!) {msg}", "danger")

def fetch_all():
    with get_conn() as c, c.cursor() as cur:
        cur.execute("""
            select student_id, first_name, last_name, email, enrollment_date
            from students
            order by student_id;
        """)
        return cur.fetchall()

@app.get("/")
def index():
    return render_template("index.html", students=fetch_all())

@app.post("/add")
def add():
    first = (request.form.get("first_name") or "").strip()
    last  = (request.form.get("last_name") or "").strip()
    email = (request.form.get("email") or "").strip().lower()
    date  = (request.form.get("enrollment_date") or "").strip() or None

    if not first: err("first_name required"); return redirect(url_for("index"))
    if not last:  err("last_name required");  return redirect(url_for("index"))
    if not email: err("email required");      return redirect(url_for("index"))
    if not email_ok(email):
        err(f'email invalid — got “{email}” → use name@domain.tld')
        return redirect(url_for("index"))

    try:
        with get_conn() as c, c.cursor() as cur:
            cur.execute("""
                insert into students(first_name,last_name,email,enrollment_date)
                values (%s,%s,%s,%s);
            """, (first, last, email, date))
        ok("student added")
    except psycopg2.Error as e:
        if e.pgcode == "23505":
            err(f'email already exists — “{email}” → choose a unique email')
        else:
            err(f"db error (add): {e}")
    return redirect(url_for("index"))

@app.post("/update_email")
def update_email():
    sid   = (request.form.get("student_id") or "").strip()
    email = (request.form.get("new_email") or "").strip().lower()

    if not sid.isdigit():
        err(f'student_id must be a positive integer — got “{sid}”')
        return redirect(url_for("index"))
    if not email_ok(email):
        err(f'email invalid — got “{email}” → use name@domain.tld')
        return redirect(url_for("index"))

    try:
        with get_conn() as c, c.cursor() as cur:
            cur.execute("update students set email=%s where student_id=%s;", (email, int(sid)))
            if cur.rowcount == 0:
                err(f'no student with id {sid} → pick an id from the table')
            else:
                ok("email updated")
    except psycopg2.Error as e:
        if e.pgcode == "23505":
            err(f'that email is already in use — “{email}”')
        else:
            err(f"db error (update): {e}")
    return redirect(url_for("index"))

@app.post("/delete")
def delete():
    sid = (request.form.get("student_id") or "").strip()
    if not sid.isdigit():
        err(f'student_id must be a positive integer — got “{sid}”')
        return redirect(url_for("index"))

    with get_conn() as c, c.cursor() as cur:
        cur.execute("delete from students where student_id=%s;", (int(sid),))
        if cur.rowcount:
            ok("student deleted")
        else:
            err(f'no student with id {sid} → pick an id from the table')
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(port=5000, debug=True)
