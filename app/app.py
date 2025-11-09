import psycopg2
from db import get_conn
import re
from datetime import datetime

def msg_ok(text):   print("{*} " + text)
def msg_err(text):  print("{:/} " + text)

def parse_date_or_none(s: str):
    s = (s or "").strip()
    if not s:
        return None
    try:
        datetime.strptime(s, "%Y-%m-%d")
        return s
    except ValueError:
        return None

def looks_like_email(s: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", (s or "").strip()))


def frame_title(title: str) -> str:
    text = f" {title.strip()} "
    width = max(56, len(text) + 2)
    border = "\\" + ("*" * (width - 2)) + "/"
    line   = "\\ " + text.center(width - 4) + " /"
    return f"{border}\n{line}\n{border}"

def draw_table(rows, headers):
    str_rows = [[("" if v is None else str(v)) for v in r] for r in rows]
    str_headers = [str(h) for h in headers]

    zipped = list(zip(str_headers, *str_rows)) if str_rows else [(h,) for h in str_headers]
    widths = [max(len(v) for v in col) for col in zipped]

    def row_line(cells):
        padded = [cells[i].ljust(widths[i]) for i in range(len(widths))]
        return "\\ " + " | ".join(padded) + " /"

    total_width = sum(widths) + (3 * (len(widths) - 1)) + 4
    border = "\\" + ("*" * (total_width - 2)) + "/"

    out = []
    out.append(border)
    out.append(row_line(str_headers))
    out.append(border)
    for r in str_rows:
        out.append(row_line(r))
    out.append(border)

    return "\n".join(out)

def getAllStudents():
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("""
                select student_id, first_name, last_name, email, enrollment_date
                from students
                order by student_id;
            """)
            rows = cur.fetchall()

        print()
        print(frame_title("all students"))
        print()

        if not rows:
            print("\\ no rows \\")
            print()
            return rows

        headers = ["id", "first_name", "last_name", "email", "enrollment_date"]
        print(draw_table(rows, headers))
        print()
        return rows

    except psycopg2.Error as e:
        print(frame_title("database error")); print(e); return []
    except Exception as e:
        print(frame_title("unexpected error")); print(e); return []

def addStudent(first_name, last_name, email, enrollment_date):
    first = (first_name or "").strip()
    last  = (last_name  or "").strip()
    email = (email      or "").strip().lower()
    date  = parse_date_or_none(enrollment_date)

    if not first or not last or not email:
        msg_err("first, last, and email are required.")
        return False
    if not looks_like_email(email):
        msg_err("invalid email format.")
        return False
    if enrollment_date and not date:
        msg_err("enrollment_date must be YYYY-MM-DD (or leave blank).")
        return False

    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("""
                insert into students (first_name, last_name, email, enrollment_date)
                values (%s, %s, %s, %s);
            """, (first, last, email, date))
        msg_ok("student added.")
        return True
    except psycopg2.Error as e:
        if e.pgcode == "23505":
            msg_err("email already exists (must be unique).")
        else:
            msg_err(f"database error (add): {e}")
        return False
    except Exception as e:
        msg_err(f"unexpected error (add): {e}")
        return False

def updateStudentEmail(student_id, new_email):
    sid_raw = (str(student_id) or "").strip()
    if not sid_raw.isdigit():
        msg_err("student id must be a positive integer.")
        return False

    sid = int(sid_raw)
    email = (new_email or "").strip().lower()

    if not looks_like_email(email):
        msg_err("invalid email format.")
        return False

    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("""
                update students
                   set email = %s
                 where student_id = %s;
            """, (email, sid))

            if cur.rowcount == 0:
                msg_err("no student with that id.")
                return False

        msg_ok("email updated.")
        return True

    except psycopg2.Error as e:
        if e.pgcode == "23505":
            msg_err("that email is already in use.")
        else:
            msg_err(f"database error (update): {e}")
        return False
    except Exception as e:
        msg_err(f"unexpected error (update): {e}")
        return False

def deleteStudent(student_id):
    sid_raw = (str(student_id) or "").strip()
    if not sid_raw.isdigit():
        msg_err("student id must be a positive integer.")
        return False

    sid = int(sid_raw)

    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("delete from students where student_id = %s;", (sid,))
            if cur.rowcount == 0:
                msg_err("no student with that id.")
                return False

        msg_ok("student deleted.")
        return True

    except psycopg2.Error as e:
        msg_err(f"database error (delete): {e}")
        return False
    except Exception as e:
        msg_err(f"unexpected error (delete): {e}")
        return False

if __name__ == "__main__":
    while True:
        print()
        print(frame_title("student database menu"))
        print("\\ 1. view all students /")
        print("\\ 2. add student /")
        print("\\ 3. update student email /")
        print("\\ 4. delete student /")
        print("\\ 5. exit /")
        print()

        choice = input("\\ select option: ").strip()

        if choice == "1":
            getAllStudents()

        elif choice == "2":
            print(frame_title("add student"))
            first = input("\\ first name: ").strip()
            last  = input("\\ last name: ").strip()
            email = input("\\ email: ").strip()
            date  = input("\\ enrollment date (YYYY-MM-DD or blank): ").strip()
            addStudent(first, last, email, date)
            getAllStudents()

        elif choice == "3":
            print(frame_title("update student email"))
            sid   = input("\\ student id: ").strip()
            email = input("\\ new email: ").strip()
            updateStudentEmail(sid, email)
            getAllStudents()

        elif choice == "4":
            print(frame_title("delete student"))
            sid = input("\\ student id to delete: ").strip()
            confirm = input(f"\\ type {sid} again to confirm: ").strip()
            if confirm != sid:
                print("{<} delete cancelled.")
            else:
                deleteStudent(sid)
            getAllStudents()

        elif choice == "5":
            print()
            print(frame_title("goodbye"))
            break

        else:
            print("{:/} invalid choice.")
