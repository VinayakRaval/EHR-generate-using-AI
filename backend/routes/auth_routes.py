from flask import Blueprint, render_template, request, redirect, flash, session
from database import connect_db
from utils.audit_logger import log_action

auth_bp = Blueprint("auth", __name__)


# ------------------------------
# LOGIN PAGE (GET)
# ------------------------------
@auth_bp.route("/login", methods=["GET"])
def login_page():
    return render_template("auth/login.html")


# ------------------------------
# LOGIN SUBMIT (POST)
# ------------------------------
@auth_bp.route("/login", methods=["POST"])
def login_post():

    role = request.form.get("role")
    identifier = request.form.get("identifier")
    password = request.form.get("password")

    conn = connect_db()
    cur = conn.cursor(dictionary=True)

    # ------------------------------
    # ADMIN LOGIN (Plain Text)
    # ------------------------------
    if role == "admin":
        cur.execute("SELECT * FROM admins WHERE email=%s", (identifier,))
        admin = cur.fetchone()

        if not admin or admin["password"] != password:
            flash("Invalid admin login", "danger")
            return redirect("/auth/login")

        session["role"] = "admin"
        session["admin"] = admin
        log_action("admin", admin["admin_id"], "Logged in")
        return redirect("/admin/dashboard")

    # ------------------------------
    # DOCTOR LOGIN (Plain Text)
    # ------------------------------
    elif role == "doctor":
        cur.execute("SELECT * FROM doctors WHERE email=%s", (identifier,))
        doctor = cur.fetchone()

        if not doctor or doctor["password"] != password:
            flash("Invalid doctor login", "danger")
            return redirect("/auth/login")

        session["role"] = "doctor"
        session["doctor"] = doctor
        log_action("doctor", doctor["doctor_id"], "Logged in")
        return redirect("/doctor/dashboard")

    # ------------------------------
    # PATIENT LOGIN (Plain Text)
    # ------------------------------
    elif role == "patient":
        cur.execute("SELECT * FROM patients WHERE username=%s", (identifier,))
        patient = cur.fetchone()

        if not patient or patient["password"] != password:
            flash("Invalid patient login", "danger")
            return redirect("/auth/login")

        session["role"] = "patient"
        session["patient"] = patient
        log_action("patient", patient["patient_id"], "Logged in")
        return redirect("/patient/dashboard")

    flash("Invalid role selected", "danger")
    return redirect("/auth/login")


# ------------------------------
# LOGOUT
# ------------------------------
@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect("/auth/login")
