"""
BGCGW Student Attendance & Mark Register
Bharathidasan Government College for Women

Flask + MySQL application.

Setup:
    1. pip install flask mysql-connector-python
    2. In MySQL Workbench, run:  database/schema.sql
    3. Update DB_HOST / DB_USER / DB_PASSWORD / DB_NAME below if needed
    4. python app.py  →  open http://127.0.0.1:5000
"""

import calendar
import os
import json
from urllib.parse import unquote
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP

import mysql.connector
from flask import (Flask, jsonify, redirect, render_template,
                   request, send_from_directory, session, url_for)
from flask.wrappers import Request as FlaskRequest
from werkzeug.utils import secure_filename

# ─────────────────────────────────────────────────────────────────────────────
#  APP SETUP
# ─────────────────────────────────────────────────────────────────────────────

class LenientJSONRequest(FlaskRequest):
    def on_json_loading_failed(self, e):
        return None

app = Flask(__name__)
app.request_class = LenientJSONRequest
app.secret_key = "bgcgw-super-secret-key-2024"
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.jinja_env.auto_reload = True
app.jinja_env.cache = {}

UPLOADS_DIR  = os.path.join(app.root_path, "static", "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

APP_NAME     = "BGCGW Student Attendance & Mark Register"
COLLEGE_NAME = "Bharathidasan Government College for Women"

# ─── MySQL connection settings — edit these to match your MySQL Workbench ────
import os

DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", "19430"))
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
# ─────────────────────────────────────────────────────────────────────────────

print("DB_HOST:", DB_HOST)
print("DB_PORT:", DB_PORT)
print("DB_NAME:", DB_NAME)

def get_db():
    """Open and return a MySQL connection with dictionary cursor support."""
    return mysql.connector.connect(
        host=DB_HOST,
        port=int(DB_PORT),
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        autocommit=False,
    )

def qry(conn, sql, params=(), many=False, one=False, commit=False):
    """
    Thin helper: run a query and return rows as dicts.
      qry(conn, sql, params)           → None  (INSERT/UPDATE/DELETE)
      qry(conn, sql, params, one=True) → dict | None
      qry(conn, sql, params, many=True)→ list[dict]
    """
    cur = conn.cursor(dictionary=True)
    cur.execute(sql, params)
    result = None
    if one:
        result = cur.fetchone()
    elif many:
        result = cur.fetchall()
    if commit:
        conn.commit()
    cur.close()
    return result


# ─────────────────────────────────────────────────────────────────────────────
#  SCHEMA COMPAT HELPERS
# ─────────────────────────────────────────────────────────────────────────────

_STUDENT_BIODATA_PK_COL = None

def student_biodata_pk_col(conn):
    """
    The project has seen two variants in the wild:
      - student_biodata.id (AUTO_INCREMENT PK)
      - student_biodata.student_id (PK)
    Detect which one exists and cache it.
    """
    global _STUDENT_BIODATA_PK_COL
    if _STUDENT_BIODATA_PK_COL:
        return _STUDENT_BIODATA_PK_COL
    cur = conn.cursor()
    try:
        cur.execute("SHOW COLUMNS FROM student_biodata LIKE 'id'")
        if cur.fetchone():
            _STUDENT_BIODATA_PK_COL = "id"
            return _STUDENT_BIODATA_PK_COL
        cur.execute("SHOW COLUMNS FROM student_biodata LIKE 'student_id'")
        if cur.fetchone():
            _STUDENT_BIODATA_PK_COL = "student_id"
            return _STUDENT_BIODATA_PK_COL
        # Fallback (will error loudly if neither exists)
        _STUDENT_BIODATA_PK_COL = "id"
        return _STUDENT_BIODATA_PK_COL
    finally:
        cur.close()


def _json_safe_row(row):
    """Convert a MySQL dict row to JSON-friendly values."""
    if not row:
        return None
    out = {}
    for k, v in row.items():
        if isinstance(v, (datetime, date)):
            out[k] = v.isoformat()
        elif isinstance(v, Decimal):
            out[k] = str(v)
        elif isinstance(v, (bytes, bytearray)):
            out[k] = v.decode("utf-8", errors="replace")
        else:
            out[k] = v
    return out


def _lookup_student_biodata(conn, query=None, biodata_pk=None):
    """
    Resolve a student row from roll_no or biodata primary key.
    If biodata_pk is provided, it wins. Otherwise `query` is roll_no first, then PK.
    """
    pk = student_biodata_pk_col(conn)
    if biodata_pk is not None and str(biodata_pk).strip() != "":
        return qry(
            conn,
            f"SELECT * FROM student_biodata WHERE {pk}=%s LIMIT 1",
            (biodata_pk,),
            one=True,
        )
    if not query or not str(query).strip():
        return None
    q = str(query).strip()
    row = qry(conn, "SELECT * FROM student_biodata WHERE roll_no=%s LIMIT 1", (q,), one=True)
    if row:
        return row
    return qry(conn, f"SELECT * FROM student_biodata WHERE {pk}=%s LIMIT 1", (q,), one=True)


def _delete_student_cascade(conn, biodata_pk, roll_no):
    """
    Delete dependent rows then student_biodata. Uses roll_no for marks, semester_result,
    and attendance (same convention as the rest of the app).
    """
    pk = student_biodata_pk_col(conn)
    roll_key = str(roll_no).strip()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM marks WHERE student_id=%s", (roll_key,))
        cur.execute("DELETE FROM semester_result WHERE student_id=%s", (roll_key,))
        cur.execute("DELETE FROM attendance WHERE roll_number=%s", (roll_key,))
        cur.execute(f"DELETE FROM student_biodata WHERE {pk}=%s", (biodata_pk,))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()

# ─────────────────────────────────────────────────────────────────────────────
#  MATH HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _r2(x):
    return Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _grade(pct):
    p = Decimal(str(pct))
    if p >= 96: return "O"
    if p >= 86: return "A+"
    if p >= 76: return "A"
    if p >= 66: return "B+"
    if p >= 56: return "B"
    if p >= 46: return "C"
    if p >= 40: return "P"
    return "F"


def _att_mark(pct):
    p = Decimal(str(pct))
    if p >= 95: return 5
    if p >= 90: return 4
    if p >= 85: return 3
    if p >= 80: return 2
    if p >= 75: return 1
    return 0


# ─────────────────────────────────────────────────────────────────────────────
#  LANDING PAGE
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


# ─────────────────────────────────────────────────────────────────────────────
#  LOGIN  (HOD / Teacher / CR)
#
#  HOW IT WORKS:
#   - First time you type an email+password for a role → stores it in DB,
#     sets the session, redirects straight to /dashboard.
#   - Next login → checks stored password; correct = dashboard, wrong = error.
#   - The error message is shown on the login page if anything goes wrong,
#     INCLUDING if MySQL is not reachable (so you know exactly what failed).
# ─────────────────────────────────────────────────────────────────────────────

_ROLE_LOGIN = {
    "HOD":     "hod_login",
    "Teacher": "teacher_login",
    "CR":      "cr_login",
}


def _do_login(role, template):
    error = None

    if request.method == "POST":
        email    = (request.form.get("email") or "").strip()
        password = (request.form.get("password") or "").strip()

        if not email or not password:
            error = "Please enter your email and password."
        else:
            conn = None
            try:
                conn = get_db()

                # ── Ensure the table exists (safe to run every request) ──
                cur = conn.cursor()
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS login_credentials (
                        id         INT AUTO_INCREMENT PRIMARY KEY,
                        email      VARCHAR(150) NOT NULL,
                        password   VARCHAR(255) NOT NULL,
                        role       VARCHAR(50)  NOT NULL,
                        created_at TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE KEY uq_email_role (email, role)
                    )
                """)
                conn.commit()
                cur.close()

                # ── Check if user exists ──
                row = qry(conn,
                    "SELECT id, password FROM login_credentials "
                    "WHERE email=%s AND role=%s LIMIT 1",
                    (email, role), one=True)

                if row is None:
                    # First-time registration: save credentials, log in
                    qry(conn,
                        "INSERT INTO login_credentials (email, password, role) "
                        "VALUES (%s, %s, %s)",
                        (email, password, role), commit=True)
                    session["user_email"] = email
                    session["user_role"]  = role
                    return redirect(url_for("dashboard"))

                elif row["password"] == password:
                    # Correct password
                    session["user_email"] = email
                    session["user_role"]  = role
                    return redirect(url_for("dashboard"))

                else:
                    error = "Incorrect password. Please try again."

            except mysql.connector.Error as exc:
                # Show the MySQL error clearly so you can diagnose it
                error = (
                    f"Cannot connect to MySQL: {exc.msg} "
                    f"(Error {exc.errno}). "
                    "Check that MySQL is running and DB_PASSWORD in app.py is correct."
                )
                print(f"[MySQL ERROR] {exc}")

            except Exception as exc:
                error = f"Unexpected error: {exc}"
                print(f"[LOGIN ERROR] {exc}")

            finally:
                if conn and conn.is_connected():
                    conn.close()

    return render_template(template, error=error)


@app.route("/hod_login",     methods=["GET", "POST"])
def hod_login():     return _do_login("HOD",     "hod_login.html")

@app.route("/teacher_login", methods=["GET", "POST"])
def teacher_login(): return _do_login("Teacher", "teacher_login.html")

@app.route("/cr_login",      methods=["GET", "POST"])
def cr_login():      return _do_login("CR",      "cr_login.html")


# ─────────────────────────────────────────────────────────────────────────────
#  DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html",
        user_email=session.get("user_email", ""),
        user_role=session.get("user_role", ""))


# ─────────────────────────────────────────────────────────────────────────────
#  LOGOUT — goes back to the correct role login page
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/logout")
def logout():
    role = session.get("user_role", "")
    session.clear()
    return redirect(url_for(_ROLE_LOGIN.get(role, "index")))


# ─────────────────────────────────────────────────────────────────────────────
#  MODULE PAGES
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/application_form")
def application_form():
    return render_template("application_form.html")


@app.route("/attendance_register")
def attendance_register():
    return render_template("attendance_register.html",
        app_name=APP_NAME, college_name=COLLEGE_NAME)


@app.route("/mark_register")
def mark_register():
    return render_template("mark_register.html",
        app_name=APP_NAME, college_name=COLLEGE_NAME)


@app.route("/mark_result_dashboard")
def mark_result_dashboard():
    semester_id = request.args.get("semester_id", type=int)
    conn = None
    try:
        conn = get_db()
        cur  = conn.cursor(dictionary=True)

        if semester_id:
            cur.execute("SELECT * FROM semester_result WHERE semester_id=%s", (semester_id,))
        else:
            cur.execute("SELECT * FROM semester_result")
        results = cur.fetchall() or []

        avg_marks = 0.0
        if semester_id:
            cur.execute("SELECT AVG(total_marks) AS a FROM marks WHERE semester_id=%s", (semester_id,))
            r = cur.fetchone()
            avg_marks = float(r["a"] or 0) if r else 0.0

        grade_counts = {}
        for r in results:
            g = r.get("grade") or "NA"
            grade_counts[g] = grade_counts.get(g, 0) + 1

        subj_labels, subj_avgs = [], []
        if semester_id:
            cur.execute("""
                SELECT COALESCE(s.subject_name, m.subject_id) AS sn,
                       AVG(m.total_marks) AS av
                FROM marks m
                LEFT JOIN subject s ON s.subject_id = m.subject_id
                WHERE m.semester_id=%s
                GROUP BY m.subject_id, sn ORDER BY sn
            """, (semester_id,))
            for row in cur.fetchall() or []:
                subj_labels.append(row["sn"])
                subj_avgs.append(float(row["av"] or 0))

        cur.execute("""SELECT semester_id, AVG(sgpa) AS av
                       FROM semester_result GROUP BY semester_id ORDER BY semester_id""")
        sgpa_rows   = cur.fetchall() or []
        sgpa_labels = [int(r["semester_id"]) for r in sgpa_rows]
        sgpa_avgs   = [float(r["av"] or 0) for r in sgpa_rows]

        perf = {"First Class with Distinction": 0, "First Class": 0,
                "Second Class": 0, "Pass": 0, "Fail/NA": 0}
        for r in results:
            cg = float(r.get("cgpa") or 0)
            if   cg >= 9:   perf["First Class with Distinction"] += 1
            elif cg >= 7:   perf["First Class"] += 1
            elif cg >= 5.5: perf["Second Class"] += 1
            elif cg >= 4:   perf["Pass"] += 1
            else:           perf["Fail/NA"] += 1

        cur.close()
        return render_template("mark_result_dashboard.html",
            app_name=APP_NAME, college_name=COLLEGE_NAME,
            semester_id=semester_id, avg_marks=avg_marks,
            grade_counts=grade_counts,
            subj_labels=subj_labels, subj_avgs=subj_avgs,
            sgpa_labels=sgpa_labels, sgpa_avgs=sgpa_avgs, perf=perf)
    except Exception as exc:
        return render_template("mark_result_dashboard.html",
            app_name=APP_NAME, college_name=COLLEGE_NAME,
            semester_id=semester_id, avg_marks=0,
            grade_counts={}, subj_labels=[], subj_avgs=[],
            sgpa_labels=[], sgpa_avgs=[], perf={}, error=str(exc))
    finally:
        if conn and conn.is_connected(): conn.close()


@app.route("/mark_student_report")
def mark_student_report():
    return render_template("mark_student_report.html",
        app_name=APP_NAME, college_name=COLLEGE_NAME)


@app.route("/delete_student", methods=["GET"])
def delete_student():
    conn = None
    students_for_dropdown = []
    try:
        conn = get_db()
        pk = student_biodata_pk_col(conn)
        rows = qry(
            conn,
            f"SELECT {pk} AS biodata_pk, roll_no, full_name "
            "FROM student_biodata ORDER BY roll_no ASC",
            many=True,
        ) or []
        for r in rows:
            rid = r.get("biodata_pk")
            rno = r.get("roll_no")
            name = (r.get("full_name") or "").strip() or "-"
            students_for_dropdown.append(
                {
                    "biodata_pk": rid,
                    "roll_no": rno,
                    "full_name": name,
                    "label": f"{name} | Roll No: {rno} | ID: {rid}",
                }
            )
    except Exception as exc:
        print(f"[delete_student page] {exc}")
    finally:
        if conn and conn.is_connected():
            conn.close()

    return render_template(
        "delete_student.html",
        app_name=APP_NAME,
        college_name=COLLEGE_NAME,
        user_email=session.get("user_email", ""),
        user_role=session.get("user_role", ""),
        students_for_dropdown=students_for_dropdown,
    )


@app.route("/delete_student/search", methods=["POST"])
def delete_student_search():
    data = request.get_json(silent=True) or {}
    query = (data.get("query") or "").strip()
    biodata_pk = data.get("biodata_pk")
    if biodata_pk is not None:
        biodata_pk = str(biodata_pk).strip()
        if biodata_pk == "":
            biodata_pk = None

    if not query and not biodata_pk:
        return jsonify({"success": False, "error": "Enter roll number, student ID, or pick from the list."}), 400

    conn = None
    try:
        conn = get_db()
        row = _lookup_student_biodata(conn, query=query or None, biodata_pk=biodata_pk)
        if not row:
            return jsonify({"success": False, "error": "Student not found."}), 404
        pk = student_biodata_pk_col(conn)
        biodata_id = row.get(pk)
        roll_no = row.get("roll_no")
        if roll_no is None or str(roll_no).strip() == "":
            return jsonify(
                {"success": False, "error": "Student record is missing a roll number; cannot delete safely."}
            ), 400
        payload = _json_safe_row(row)
        return jsonify(
            {
                "success": True,
                "student": payload,
                "biodata_pk": biodata_id,
                "roll_no": roll_no,
            }
        )
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500
    finally:
        if conn and conn.is_connected():
            conn.close()


@app.route("/delete_student/confirm_delete", methods=["POST"])
def delete_student_confirm_delete():
    data = request.get_json(silent=True) or {}
    biodata_pk = data.get("biodata_pk")
    roll_no = data.get("roll_no")
    if biodata_pk is None or roll_no is None or str(roll_no).strip() == "":
        return jsonify({"success": False, "error": "Missing student identifiers."}), 400

    conn = None
    try:
        conn = get_db()
        pk = student_biodata_pk_col(conn)
        row = qry(
            conn,
            f"SELECT {pk} AS _pk, roll_no FROM student_biodata WHERE {pk}=%s LIMIT 1",
            (biodata_pk,),
            one=True,
        )
        if not row:
            return jsonify({"success": False, "error": "Student not found."}), 404
        if str(row.get("roll_no")) != str(roll_no):
            return jsonify({"success": False, "error": "Record mismatch; please search again."}), 400

        _delete_student_cascade(conn, biodata_pk, roll_no)
        return jsonify({"success": True, "message": "Student record deleted successfully"})
    except Exception as exc:
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
        return jsonify({"success": False, "error": str(exc)}), 500
    finally:
        if conn and conn.is_connected():
            conn.close()


# ─────────────────────────────────────────────────────────────────────────────
#  REPORT MODULE
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/report_search", methods=["GET"])
def report_search():
    return render_template("report_search.html",
        app_name=APP_NAME, college_name=COLLEGE_NAME)


@app.route("/report/search", methods=["GET", "POST"])
def report_search_post():
    # Support both:
    # - GET /report/search?roll_no=...&student_id=...
    # - POST form submits (application/x-www-form-urlencoded)
    # Avoid request.get_json() to prevent 415 on non-JSON content-types.
    roll_no = (request.values.get("roll_no") or "").strip()
    student_id = (request.values.get("student_id") or "").strip()
    if not roll_no and not student_id:
        return render_template(
            "report_search.html",
            error="Roll number or Student ID required.",
            app_name=APP_NAME,
            college_name=COLLEGE_NAME,
        )
    conn = None
    try:
        conn = get_db()
        pk = student_biodata_pk_col(conn)
        # Allow search by either roll number (used in marks tables) or student_id (biodata PK)
        if student_id and not roll_no:
            row = qry(conn,
                      f"SELECT {pk} AS biodata_id, roll_no FROM student_biodata WHERE {pk}=%s LIMIT 1",
                      (student_id,), one=True)
            if not row:
                return render_template(
                    "report_search.html",
                    error="Student not found.",
                    app_name=APP_NAME,
                    college_name=COLLEGE_NAME,
                )
            biodata_id = row["biodata_id"]
            roll_no = str(row.get("roll_no") or "").strip()
            if not roll_no:
                return render_template(
                    "report_search.html",
                    error="Student found but roll number is missing.",
                    app_name=APP_NAME,
                    college_name=COLLEGE_NAME,
                )
        else:
            row = qry(conn,
                      f"SELECT {pk} AS biodata_id FROM student_biodata WHERE roll_no=%s LIMIT 1",
                      (roll_no,), one=True)
            if not row:
                return render_template(
                    "report_search.html",
                    error="Student not found.",
                    app_name=APP_NAME,
                    college_name=COLLEGE_NAME,
                )
            biodata_id = row["biodata_id"]

        sem = qry(
            conn,
            "SELECT semester_id FROM marks WHERE student_id=%s ORDER BY semester_id DESC LIMIT 1",
            (roll_no,),
            one=True,
        )
        target_sem = sem["semester_id"] if sem else 1
        redirect_url = (f"/report?student_biodata_id={biodata_id}"
                        f"&roll_no={roll_no}&target_semester_id={target_sem}")
        return redirect(redirect_url)
    except Exception as exc:
        return render_template("report_search.html", error=str(exc),
            app_name=APP_NAME, college_name=COLLEGE_NAME)
    finally:
        if conn and conn.is_connected(): conn.close()


@app.route("/report", methods=["GET"])
def report_page():
    student_biodata_id = request.args.get("student_biodata_id")
    roll_no            = request.args.get("roll_no", "")
    target_semester_id = request.args.get("target_semester_id", type=int, default=1)
    conn = None
    try:
        conn = get_db()
        pk = student_biodata_pk_col(conn)
        student = qry(conn,
            f"SELECT * FROM student_biodata WHERE {pk}=%s LIMIT 1" if student_biodata_id
            else "SELECT * FROM student_biodata WHERE roll_no=%s LIMIT 1",
            (student_biodata_id if student_biodata_id else roll_no,), one=True)
        if not student:
            return render_template("report_search.html",
                error="Student not found.",
                app_name=APP_NAME, college_name=COLLEGE_NAME)

        # If the DB has junk/non-filename values in `photo`, don't render a broken <img>.
        # Only treat it as a photo when the file exists in static/uploads.
        raw_photo = (student.get("photo") or "").strip()
        if raw_photo:
            p = unquote(raw_photo).replace("\\", "/")
            fname = os.path.basename(p)
            if fname and os.path.exists(os.path.join(UPLOADS_DIR, fname)):
                student["photo"] = fname
            else:
                student["photo"] = ""

        rn = str(student.get("roll_no", ""))
        biodata_pk_value = student.get(pk)
        marks_rows = qry(conn, """
            SELECT m.subject_id,
                   COALESCE(s.subject_name, m.subject_id) AS subject_name,
                   m.marks_obtained_internal AS internal,
                   m.marks_obtained_external AS external,
                   m.total_marks             AS total
            FROM marks m
            LEFT JOIN subject s ON s.subject_id = m.subject_id
            WHERE m.student_id=%s AND m.semester_id=%s
        """, (rn, target_semester_id), many=True)

        result = qry(conn,
            "SELECT percentage,grade,sgpa,cgpa,attendance_mark "
            "FROM semester_result WHERE student_id=%s AND semester_id=%s LIMIT 1",
            (rn, target_semester_id), one=True) or {}

        all_results = qry(conn,
            "SELECT semester_id,percentage,sgpa,cgpa,grade "
            "FROM semester_result WHERE student_id=%s ORDER BY semester_id",
            (rn,), many=True)

        att = qry(conn, """
            SELECT COALESCE(SUM(total_present),0) AS tp,
                   COALESCE(SUM(total_absent),0)  AS ta,
                   COALESCE(SUM(total_late),0)    AS tl
            FROM attendance WHERE roll_number=%s AND semester_number=%s
        """, (rn, target_semester_id), one=True) or {"tp": 0, "ta": 0, "tl": 0}

        total_hours = (att["tp"] or 0) + (att["ta"] or 0) + (att["tl"] or 0)
        att_pct = (float(_r2(Decimal(att["tp"]) / Decimal(total_hours) * 100))
                   if total_hours > 0 else 0.0)

        return render_template("report.html",
            student=student, marks_rows=marks_rows or [], result=result,
            all_results=all_results or [],
            attendance_percentage=att_pct,
            att_pct=att_pct, att_hours=att,
            biodata_pk_value=biodata_pk_value,
            biodata_pk_col=pk,
            target_semester_id=target_semester_id,
            app_name=APP_NAME, college_name=COLLEGE_NAME)

    except Exception as exc:
        return render_template("report_search.html", error=str(exc),
            app_name=APP_NAME, college_name=COLLEGE_NAME)
    finally:
        if conn and conn.is_connected(): conn.close()


@app.route("/update_report", methods=["POST"])
def update_report():
    conn = None
    try:
        # New flow: report.js sends FormData with a JSON string under "payload"
        if request.form.get("payload"):
            payload = json.loads(request.form.get("payload") or "{}")
            sid = str(payload.get("student_biodata_id") or "").strip()
            roll_no = str(payload.get("original_roll_no") or "").strip()
            target_semester_id = int(payload.get("target_semester_id") or 0)
            student_fields = payload.get("student_fields") or {}
            marks = payload.get("marks") or []
            attendance_percentage = payload.get("attendance_percentage")

            if not sid:
                return jsonify({"success": False, "error": "Missing student_biodata_id."}), 400
            if not roll_no:
                return jsonify({"success": False, "error": "Missing roll number."}), 400
            if not target_semester_id:
                return jsonify({"success": False, "error": "Missing target semester."}), 400

            conn = get_db()
            cur = conn.cursor(dictionary=True)

            # Optional photo update
            photo_filename = None
            pf = request.files.get("photo")
            if pf and pf.filename:
                photo_filename = secure_filename(pf.filename)
                pf.save(os.path.join(UPLOADS_DIR, photo_filename))

            # Update biodata fields
            allowed_fields = {
                "full_name", "dob", "class_sec", "blood_group", "primary_phone", "alt_phone",
                "res_address", "bus_address", "mother_name", "mother_occ", "father_name", "father_occ",
                "school_name", "category", "group_studied", "hsc_marks", "scholarship", "add_qual",
                "extra_curric", "ncc_sports", "achievements", "hobbies", "hostel", "exam_reg", "roll_no",
            }
            set_parts, values = [], []
            for k, v in (student_fields or {}).items():
                if k in allowed_fields:
                    set_parts.append(f"{k}=%s")
                    values.append(v)
            if photo_filename:
                set_parts.append("photo=%s")
                values.append(photo_filename)
            if set_parts:
                cur.execute(
                    f"UPDATE student_biodata SET {', '.join(set_parts)} WHERE {student_biodata_pk_col(conn)}=%s",
                    values + [sid],
                )

            # Upsert marks for the selected semester
            saved_marks = 0
            for m in marks:
                subject_id = str(m.get("subject_id") or "").strip()
                if not subject_id:
                    continue
                internal = int(m.get("internal_marks") or 0)
                external = int(m.get("external_marks") or 0)
                total = internal + external

                cur.execute(
                    "SELECT marks_id FROM marks WHERE student_id=%s AND subject_id=%s AND semester_id=%s LIMIT 1",
                    (roll_no, subject_id, target_semester_id),
                )
                ex = cur.fetchone()
                if ex:
                    cur.execute(
                        "UPDATE marks SET marks_obtained_internal=%s, marks_obtained_external=%s, total_marks=%s "
                        "WHERE marks_id=%s",
                        (internal, external, total, ex["marks_id"]),
                    )
                else:
                    cur.execute(
                        "INSERT INTO marks (student_id, subject_id, semester_id, total_marks, marks_obtained_external, "
                        "marks_obtained_internal, cumulative_marks) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                        (roll_no, subject_id, target_semester_id, total, external, internal, total),
                    )
                saved_marks += 1

            # Store attendance percentage into semester_result.attendance_mark (optional)
            try:
                if attendance_percentage is not None:
                    att_mark = float(attendance_percentage)
                    cur.execute(
                        "SELECT result_id FROM semester_result WHERE student_id=%s AND semester_id=%s LIMIT 1",
                        (roll_no, target_semester_id),
                    )
                    exr = cur.fetchone()
                    if exr:
                        cur.execute(
                            "UPDATE semester_result SET attendance_mark=%s WHERE result_id=%s",
                            (att_mark, exr["result_id"]),
                        )
                    else:
                        cur.execute(
                            "INSERT INTO semester_result (student_id, semester_id, attendance_mark) VALUES (%s,%s,%s)",
                            (roll_no, target_semester_id, att_mark),
                        )
            except Exception:
                # Don't fail the whole update if attendance mark can't be stored
                pass

            conn.commit()
            cur.close()
            return jsonify({"success": True, "message": f"Updated. Saved {saved_marks} marks rows."})

        # Legacy fallback (non-JS clients)
        sid     = request.form.get("student_biodata_id")
        roll_no = request.form.get("roll_no", "").strip()
        if not sid:
            return jsonify({"status": "error", "message": "Missing student_biodata_id"}), 400

        photo_filename = None
        pf = request.files.get("photo")
        if pf and pf.filename:
            photo_filename = secure_filename(pf.filename)
            pf.save(os.path.join(UPLOADS_DIR, photo_filename))

        fields = ["full_name","dob","class_sec","blood_group",
                  "primary_phone","alt_phone","res_address",
                  "mother_name","father_name"]
        set_parts, values = [], []
        for fld in fields:
            val = request.form.get(fld)
            if val is not None:
                set_parts.append(f"{fld}=%s"); values.append(val)
        if photo_filename:
            set_parts.append("photo=%s"); values.append(photo_filename)

        if set_parts:
            conn = get_db()
            cur  = conn.cursor()
            cur.execute(f"UPDATE student_biodata SET {', '.join(set_parts)} WHERE {student_biodata_pk_col(conn)}=%s",
                        values + [sid])
            conn.commit()
            cur.close()

        return redirect(f"/report?student_biodata_id={sid}&roll_no={roll_no}")
    except Exception as exc:
        # Keep JSON shape expected by report.js when possible
        if request.form.get("payload"):
            return jsonify({"success": False, "error": str(exc)}), 500
        return jsonify({"status": "error", "message": str(exc)}), 500
    finally:
        if conn and conn.is_connected(): conn.close()


# ─────────────────────────────────────────────────────────────────────────────
#  STUDENT PHOTO
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/student_photo/<path:filename>")
def student_photo(filename):
    # Normalize DB-stored values like:
    # - "uploads/foo.jpg"
    # - "C:\...\static\uploads\foo.jpg"
    # - "foo bar.jpg"
    fname = unquote(filename or "")
    fname = fname.replace("\\", "/")
    fname = os.path.basename(fname)
    if not fname:
        return "", 404
    if os.path.exists(os.path.join(UPLOADS_DIR, fname)):
        return send_from_directory(UPLOADS_DIR, fname)
    return "", 404


# ─────────────────────────────────────────────────────────────────────────────
#  APPLICATION FORM SUBMIT
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/submit", methods=["POST"])
def submit():
    conn = None
    try:
        def fv(n): return request.form.get(n) or None

        photo_filename = None
        pf = request.files.get("photo")
        if pf and pf.filename:
            photo_filename = secure_filename(pf.filename)
            pf.save(os.path.join(UPLOADS_DIR, photo_filename))

        conn = get_db()
        cur  = conn.cursor()
        cur.execute("""
            INSERT INTO student_biodata (
                full_name, dob, roll_no, exam_reg, class_sec,
                mother_name, father_name, mother_occ, father_occ,
                res_address, bus_address, primary_phone, alt_phone,
                school_name, category, group_studied, hsc_marks,
                scholarship, extra_curric, add_qual,
                ncc_sports, achievements, hobbies, blood_group, hostel, photo
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            fv("full_name"), fv("dob"), fv("roll_no"), fv("exam_reg"), fv("class_sec") or "",
            fv("mother_name") or "", fv("father_name") or "", fv("mother_occ"), fv("father_occ"),
            fv("res_address"), fv("bus_address") or "",
            fv("primary_phone"), fv("alt_phone"),
            fv("school_name"), fv("category"), fv("group_studied"), fv("hsc_marks"),
            fv("scholarship"), fv("extra_curric"), fv("add_qual"),
            fv("ncc_sports"), fv("achievements"), fv("hobbies"), fv("blood_group"),
            1 if request.form.get("hostel") == "Yes" else 0,
            photo_filename or "",
        ))
        conn.commit()
        cur.close()
        return jsonify({"status": "success"}), 200
    except Exception as exc:
        print(f"[SUBMIT ERROR] {exc}")
        return jsonify({"status": "error", "message": str(exc)}), 500
    finally:
        if conn and conn.is_connected(): conn.close()


# ─────────────────────────────────────────────────────────────────────────────
#  HOUR-WISE ATTENDANCE API
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/attendance/load", methods=["POST"])
def load_attendance():
    data = request.get_json() or {}
    month = int(data.get("month", 1))
    year  = int(data.get("year", datetime.now().year))
    sem   = int(data.get("semester_number", data.get("semester_id", 1)))
    conn  = None
    try:
        conn  = get_db()
        rows  = qry(conn,
            "SELECT roll_no, full_name FROM student_biodata ORDER BY roll_no ASC",
            many=True)
        students = [{"roll_number": r["roll_no"], "student_name": r["full_name"]}
                    for r in (rows or [])]
        if not students:
            return jsonify({"success": True, "students": [], "attendance": {},
                "month": month, "year": year, "semester_number": sem,
                "message": "No students found. Add students via Application Form first."})

        month_name = calendar.month_name[month]
        att_rows = qry(conn, """
            SELECT roll_number, date, h1, h2, h3, h4, h5, h6
            FROM attendance
            WHERE year=%s AND month=%s AND semester_number=%s
        """, (year, month_name, sem), many=True) or []

        att_map = {}
        for r in att_rows:
            d = r["date"]
            if hasattr(d, "isoformat"): d = d.isoformat()[:10]
            att_map[f"{r['roll_number']}|{d}"] = {
                f"h{i}": r.get(f"h{i}") or "A" for i in range(1, 7)}

        return jsonify({"success": True, "students": students, "attendance": att_map,
            "month": month, "year": year, "semester_number": sem})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500
    finally:
        if conn and conn.is_connected(): conn.close()


@app.route("/api/attendance/save", methods=["POST"])
def save_attendance():
    data        = request.get_json() or {}
    date_str    = data.get("date", "")
    month_name  = data.get("month", "")
    year        = int(data.get("year", 0) or 0)
    sem         = int(data.get("semester_number", 0) or 0)
    records     = data.get("records", []) or []

    if not date_str or not month_name or not year or not sem:
        return jsonify({"success": False,
            "error": "Missing: date, month, year, semester_number"}), 400
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return jsonify({"success": False, "error": "Date must be YYYY-MM-DD"}), 400

    conn = None
    try:
        conn = get_db()
        cur  = conn.cursor(dictionary=True)
        saved = 0
        for rec in records:
            rn = rec.get("roll_number")
            sn = rec.get("student_name", "")
            if rn is None: continue
            h  = {f"h{i}": rec.get(f"h{i}", "A") for i in range(1, 7)}
            tp = sum(1 for v in h.values() if v == "P")
            ta = sum(1 for v in h.values() if v == "A")
            tl = sum(1 for v in h.values() if v == "L")

            cur.execute("""SELECT attendance_id FROM attendance
                WHERE roll_number=%s AND date=%s AND semester_number=%s LIMIT 1""",
                (rn, date_str, sem))
            ex = cur.fetchone()

            if ex:
                cur.execute("""UPDATE attendance SET
                    student_name=%s, h1=%s,h2=%s,h3=%s,h4=%s,h5=%s,h6=%s,
                    total_present=%s,total_absent=%s,total_late=%s,month=%s,year=%s
                    WHERE attendance_id=%s""",
                    (sn, h["h1"],h["h2"],h["h3"],h["h4"],h["h5"],h["h6"],
                     tp, ta, tl, month_name, year, ex["attendance_id"]))
            else:
                cur.execute("""INSERT INTO attendance
                    (roll_number,student_name,h1,h2,h3,h4,h5,h6,
                     total_present,total_absent,total_late,date,month,year,semester_number)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (rn, sn, h["h1"],h["h2"],h["h3"],h["h4"],h["h5"],h["h6"],
                     tp, ta, tl, date_str, month_name, year, sem))
            saved += 1

        conn.commit()
        cur.close()
        return jsonify({"success": True, "saved": saved})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500
    finally:
        if conn and conn.is_connected(): conn.close()


# ─────────────────────────────────────────────────────────────────────────────
#  MARK REGISTRATION API
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api_student_lookup/<student_id>")
def api_student_lookup(student_id):
    conn = None
    try:
        conn = get_db()
        row  = qry(conn, "SELECT full_name FROM student_biodata WHERE roll_no=%s LIMIT 1",
                   (student_id,), one=True)
        if not row:
            return jsonify({"success": False, "error": "Student not found."}), 404
        return jsonify({"success": True, "student_id": student_id,
                        "student_name": row["full_name"]})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500
    finally:
        if conn and conn.is_connected(): conn.close()


@app.route("/api_student_results/<student_id>")
def api_student_results(student_id):
    conn = None
    try:
        conn = get_db()
        rows = qry(conn,
            "SELECT semester_id,percentage,grade,sgpa,cgpa,attendance_mark "
            "FROM semester_result WHERE student_id=%s ORDER BY semester_id",
            (student_id,), many=True) or []
        # Convert Decimal → str for JSON serialisation
        clean = []
        for r in rows:
            clean.append({k: (str(v) if isinstance(v, Decimal) else v)
                          for k, v in r.items()})
        return jsonify({"success": True, "results": clean})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500
    finally:
        if conn and conn.is_connected(): conn.close()


@app.route("/save_marks", methods=["POST"])
def save_marks():
    data        = request.get_json() or {}
    student_id  = (data.get("student_id") or "").strip()
    semester_id = int(data.get("semester_id") or 0)
    subjects    = data.get("subjects") or []

    if not student_id or not semester_id or not subjects:
        return jsonify({"success": False,
            "error": "student_id, semester_id and subjects required."}), 400

    conn = None
    try:
        conn = get_db()
        cur  = conn.cursor(dictionary=True)

        cur.execute("SELECT full_name FROM student_biodata WHERE roll_no=%s LIMIT 1",
                    (student_id,))
        if not cur.fetchone():
            return jsonify({"success": False, "error": "Student not found."}), 400

        # Auto-create semester row
        cur.execute("SELECT semester_id FROM semester WHERE semester_id=%s LIMIT 1",
                    (semester_id,))
        if not cur.fetchone():
            cur.execute("INSERT IGNORE INTO semester (semester_id,semester_no,academic_year) "
                        "VALUES (%s,%s,%s)", (semester_id, semester_id, "N/A"))

        cur.execute("DELETE FROM marks WHERE student_id=%s AND semester_id=%s",
                    (student_id, semester_id))

        saved_rows = 0
        for s in subjects:
            sid   = (s.get("subject_id") or "").strip()
            sname = (s.get("subject_name") or "").strip()
            if not sid or not sname: continue
            internal = int(s.get("internal_marks") or 0)
            external = int(s.get("external_marks") or 0)
            total    = internal + external

            cur.execute("SELECT subject_id FROM subject WHERE subject_id=%s LIMIT 1", (sid,))
            if cur.fetchone():
                cur.execute("UPDATE subject SET subject_name=%s,semester_id=%s "
                            "WHERE subject_id=%s", (sname, semester_id, sid))
            else:
                cur.execute("INSERT INTO subject (subject_id,subject_name,semester_id) "
                            "VALUES (%s,%s,%s)", (sid, sname, semester_id))

            cur.execute("""INSERT INTO marks
                (student_id,subject_id,semester_id,
                 marks_obtained_external,marks_obtained_internal,
                 cumulative_marks,total_marks)
                VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                (student_id, sid, semester_id, external, internal, total, total))
            saved_rows += 1

        if saved_rows == 0:
            conn.rollback()
            return jsonify({"success": False, "error": "No valid subjects to save."}), 400

        cur.execute("SELECT COALESCE(SUM(total_marks),0) AS s FROM marks "
                    "WHERE student_id=%s AND semester_id=%s", (student_id, semester_id))
        total_sum = int((cur.fetchone() or {}).get("s") or 0)

        cur.execute("""SELECT COALESCE(SUM(total_present),0) AS tp,
                              COALESCE(SUM(total_absent),0)  AS ta,
                              COALESCE(SUM(total_late),0)    AS tl
                       FROM attendance WHERE roll_number=%s AND semester_number=%s""",
                    (student_id, semester_id))
        att = cur.fetchone() or {"tp": 0, "ta": 0, "tl": 0}
        total_hours = (att["tp"] or 0) + (att["ta"] or 0) + (att["tl"] or 0)
        att_pct  = (_r2(Decimal(att["tp"]) / Decimal(total_hours) * 100)
                    if total_hours > 0 else Decimal("0.00"))
        att_mark = _att_mark(att_pct)

        pct   = _r2(Decimal(total_sum) / Decimal(saved_rows))
        sgpa  = _r2(Decimal(total_sum) / Decimal("486") * 10)
        grade = _grade(pct)

        cur.execute("SELECT semester_id,sgpa FROM semester_result "
                    "WHERE student_id=%s AND semester_id BETWEEN 1 AND 6", (student_id,))
        sgpa_map = {int(r["semester_id"]): Decimal(str(r["sgpa"]))
                    for r in (cur.fetchall() or [])}
        sgpa_map[semester_id] = sgpa
        upto = min(semester_id, 6)
        used = [sgpa_map[i] for i in range(1, upto + 1) if i in sgpa_map]
        cgpa = _r2(sum(used) / len(used)) if used else Decimal("0.00")

        cur.execute("SELECT result_id FROM semester_result "
                    "WHERE student_id=%s AND semester_id=%s LIMIT 1",
                    (student_id, semester_id))
        ex = cur.fetchone()
        if ex:
            cur.execute("""UPDATE semester_result
                SET percentage=%s,grade=%s,sgpa=%s,cgpa=%s,attendance_mark=%s
                WHERE result_id=%s""",
                (str(pct), grade, str(sgpa), str(cgpa), att_mark, ex["result_id"]))
        else:
            cur.execute("""INSERT INTO semester_result
                (student_id,semester_id,percentage,grade,sgpa,cgpa,attendance_mark)
                VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                (student_id, semester_id, str(pct), grade, str(sgpa), str(cgpa), att_mark))

        conn.commit()
        cur.close()
        return jsonify({"success": True, "saved_rows": saved_rows,
            "percentage": str(pct), "sgpa": str(sgpa), "cgpa": str(cgpa),
            "grade": grade, "attendance_mark": att_mark})

    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500
    finally:
        if conn and conn.is_connected(): conn.close()


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", 5000))

    print("\n" + "="*60)
    print(f"  {APP_NAME}")
    print(f"  MySQL: {DB_HOST} / {DB_NAME}")
    print(f"  Running on port {port}")
    print("="*60 + "\n")

    app.run(debug=True, host="0.0.0.0", port=port)