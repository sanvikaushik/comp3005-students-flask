from flask import Flask, render_template, flash
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

if __name__ == "__main__":
    app.run(port=5000, debug=True)
