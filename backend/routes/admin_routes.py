from flask import Blueprint, render_template, request, redirect, flash, session, send_file
import os
import json
from database import connect_db
from encryption import hash_password
from utils.audit_logger import log_action

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


# ------------------------------------------------
# Helper: Require Admin Login
# ------------------------------------------------
def require_admin():
    return "admin" in session and session.get("role") == "admin"



# ------------------------------------------------
# ADMIN DASHBOARD
# ------------------------------------------------
@admin_bp.route("/dashboard")
def admin_dashboard():
    if not require_admin():
        return redirect("/auth/login")

    conn = connect_db()
    cur = conn.cursor(dictionary=True)

    # Summary numbers
    cur.execute("SELECT COUNT(*) AS total FROM doctors")
    total_doctors = cur.fetchone()["total"]

    cur.execute("SELECT COUNT(*) AS total FROM patients")
    total_patients = cur.fetchone()["total"]

    cur.execute("SELECT COUNT(*) AS total FROM prescriptions")
    total_prescriptions = cur.fetchone()["total"]

    cur.execute("SELECT COUNT(*) AS total FROM lab_reports")
    total_reports = cur.fetchone()["total"]

    # Recent audit logs
    cur.execute("""
        SELECT role, user_id, action, timestamp, ip_address
        FROM audit_logs
        ORDER BY timestamp DESC
        LIMIT 5
    """)
    recent_logs = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "admin/dashboard.html",
        total_doctors=total_doctors,
        total_patients=total_patients,
        total_prescriptions=total_prescriptions,
        total_reports=total_reports,
        recent_logs=recent_logs
    )


# ------------------------------------------------
# MANAGE DOCTORS (LIST + ADD)
# ------------------------------------------------
@admin_bp.route("/manage-doctors", methods=["GET", "POST"])
def manage_doctors():
    if not require_admin():
        return redirect("/auth/login")

    conn = connect_db()
    cur = conn.cursor(dictionary=True)

    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        specialization = request.form["specialization"]
        phone = request.form.get("phone")

        hashed = hash_password(password)

        cur.execute("""
            INSERT INTO doctors (name, email, password, specialization, phone, created_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
        """, (name, email, hashed, specialization, phone))

        conn.commit()
        log_action("admin", session["admin"]["admin_id"], f"Added doctor: {name}")

        flash("Doctor added successfully", "success")

        cur.close()
        conn.close()
        return redirect("/admin/manage-doctors")

    # GET doctors list
    cur.execute("SELECT * FROM doctors ORDER BY created_at DESC")
    doctors = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("admin/manage-doctors.html", doctors=doctors)


# ------------------------------------------------
# EDIT DOCTOR
# ------------------------------------------------
@admin_bp.route("/manage-doctors/edit", methods=["POST"])
def edit_doctor():
    if not require_admin():
        return redirect("/auth/login")

    conn = connect_db()
    cur = conn.cursor()

    doctor_id = request.form.get("doctor_id")
    name = request.form.get("name")
    email = request.form.get("email")
    specialization = request.form.get("specialization")
    phone = request.form.get("phone")
    password = request.form.get("password")  # optional

    if password:
        hashed = hash_password(password)
        cur.execute("""
            UPDATE doctors
            SET name=%s, email=%s, specialization=%s, phone=%s, password=%s
            WHERE doctor_id=%s
        """, (name, email, specialization, phone, hashed, doctor_id))
    else:
        cur.execute("""
            UPDATE doctors
            SET name=%s, email=%s, specialization=%s, phone=%s
            WHERE doctor_id=%s
        """, (name, email, specialization, phone, doctor_id))

    conn.commit()

    log_action("admin", session["admin"]["admin_id"], f"Edited doctor ID {doctor_id}")
    flash("Doctor updated successfully", "success")

    cur.close()
    conn.close()
    return redirect("/admin/manage-doctors")


# ------------------------------------------------
# DELETE DOCTOR
# ------------------------------------------------
@admin_bp.route("/manage-doctors/delete/<int:doctor_id>")
def delete_doctor(doctor_id):
    if not require_admin():
        return redirect("/auth/login")

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("SELECT name FROM doctors WHERE doctor_id=%s", (doctor_id,))
    row = cur.fetchone()

    if not row:
        flash("Doctor not found!", "danger")
        return redirect("/admin/manage-doctors")

    cur.execute("DELETE FROM doctors WHERE doctor_id=%s", (doctor_id,))
    conn.commit()

    log_action("admin", session["admin"]["admin_id"], f"Deleted doctor ID {doctor_id}")
    flash("Doctor removed successfully", "info")

    cur.close()
    conn.close()
    return redirect("/admin/manage-doctors")


# ------------------------------------------------
# MANAGE PATIENTS (LIST + ADD)
# ------------------------------------------------
@admin_bp.route("/manage-patients", methods=["GET", "POST"])
def manage_patients():
    if not require_admin():
        return redirect("/auth/login")

    conn = connect_db()
    cur = conn.cursor(dictionary=True)

    if request.method == "POST":
        first = request.form["first_name"]
        last = request.form["last_name"]
        doctor_id = request.form.get("doctor_id")
        username = request.form["username"]
        phone = request.form.get("phone")
        dob = request.form.get("dob")

        cur.execute("""
            INSERT INTO patients (doctor_id, first_name, last_name, phone, dob, username, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
        """, (doctor_id, first, last, phone, dob, username))

        conn.commit()

        log_action("admin", session["admin"]["admin_id"], f"Added patient username: {username}")
        flash("Patient added successfully", "success")

        cur.close()
        conn.close()
        return redirect("/admin/manage-patients")

    # GET patient list
    cur.execute("""
        SELECT p.*, d.name AS doctor_name
        FROM patients p
        LEFT JOIN doctors d ON p.doctor_id=d.doctor_id
        ORDER BY p.created_at DESC
    """)
    patients = cur.fetchall()

    # doctor dropdown list
    cur.execute("SELECT doctor_id, name FROM doctors ORDER BY name")
    doctors = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("admin/manage-patients.html", patients=patients, doctors=doctors)


# ------------------------------------------------
# EDIT PATIENT
# ------------------------------------------------
@admin_bp.route("/manage-patients/edit", methods=["POST"])
def edit_patient():
    if not require_admin():
        return redirect("/auth/login")

    conn = connect_db()
    cur = conn.cursor()

    patient_id = request.form.get("patient_id")
    first = request.form.get("first_name")
    last = request.form.get("last_name")
    username = request.form.get("username")
    phone = request.form.get("phone")
    dob = request.form.get("dob")
    doctor_id = request.form.get("doctor_id")

    cur.execute("""
        UPDATE patients
        SET first_name=%s, last_name=%s, username=%s, phone=%s, dob=%s, doctor_id=%s
        WHERE patient_id=%s
    """, (first, last, username, phone, dob, doctor_id, patient_id))

    conn.commit()

    log_action("admin", session["admin"]["admin_id"], f"Edited patient ID {patient_id}")
    flash("Patient updated successfully", "success")

    cur.close()
    conn.close()
    return redirect("/admin/manage-patients")


# ------------------------------------------------
# DELETE PATIENT
# ------------------------------------------------
@admin_bp.route("/manage-patients/delete/<int:patient_id>")
def delete_patient(patient_id):
    if not require_admin():
        return redirect("/auth/login")

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("SELECT username FROM patients WHERE patient_id=%s", (patient_id,))
    if not cur.fetchone():
        flash("Patient not found!", "danger")
        return redirect("/admin/manage-patients")

    cur.execute("DELETE FROM patients WHERE patient_id=%s", (patient_id,))
    conn.commit()

    log_action("admin", session["admin"]["admin_id"], f"Deleted patient ID {patient_id}")
    flash("Patient removed successfully", "info")

    cur.close()
    conn.close()
    return redirect("/admin/manage-patients")


# ------------------------------------------------
# ADMIN — FULL PATIENT DETAILS PAGE
# ------------------------------------------------
@admin_bp.route("/patient/<int:patient_id>")
def admin_patient_details(patient_id):
    if not require_admin():
        return redirect("/auth/login")

    db = connect_db()
    cur = db.cursor(dictionary=True)

    # BASIC PATIENT INFO
    cur.execute("""
        SELECT p.*, d.name AS doctor_name
        FROM patients p
        LEFT JOIN doctors d ON p.doctor_id=d.doctor_id
        WHERE p.patient_id=%s
    """, (patient_id,))
    patient = cur.fetchone()

    if not patient:
        db.close()
        return "Patient not found", 404

    # PRESCRIPTIONS
    cur.execute("""
        SELECT p.*, d.name AS doctor_name
        FROM prescriptions p
        JOIN doctors d ON p.doctor_id=d.doctor_id
        WHERE p.patient_id=%s
        ORDER BY p.created_at DESC
    """, (patient_id,))
    prescriptions = cur.fetchall()

    for pres in prescriptions:
        meds = pres.get("medicines")
        pres["medicines"] = json.loads(meds) if meds else []

    # LAB REPORTS
    cur.execute("""
        SELECT r.*, d.name AS doctor_name
        FROM lab_reports r
        JOIN doctors d ON r.doctor_id=d.doctor_id
        WHERE r.patient_id=%s
        ORDER BY r.upload_date DESC
    """, (patient_id,))
    reports = cur.fetchall()

    # SUMMARY COUNTS
    cur.execute("SELECT COUNT(*) AS total FROM prescriptions WHERE patient_id=%s", (patient_id,))
    patient["total_prescriptions"] = cur.fetchone()["total"]

    cur.execute("SELECT COUNT(*) AS total FROM lab_reports WHERE patient_id=%s", (patient_id,))
    patient["total_reports"] = cur.fetchone()["total"]

    cur.execute("""
        SELECT created_at 
        FROM prescriptions 
        WHERE patient_id=%s 
        ORDER BY created_at DESC LIMIT 1
    """, (patient_id,))
    row = cur.fetchone()
    patient["last_visit"] = row["created_at"] if row else "-"

    # PATIENT AUDIT LOG
    cur.execute("""
        SELECT *
        FROM audit_logs
        WHERE action LIKE %s OR user_id=%s
        ORDER BY timestamp DESC
    """, (f"%patient ID {patient_id}%", patient_id))
    patient_audit = cur.fetchall()

    cur.close()
    db.close()

    return render_template(
        "admin/patient-details.html",
        patient=patient,
        prescriptions=prescriptions,
        reports=reports,
        patient_audit=patient_audit
    )


# ------------------------------------------------
# AUDIT LOG PAGE
# ------------------------------------------------
@admin_bp.route("/audit-log")
def admin_audit_log():
    if not require_admin():
        return redirect("/auth/login")

    conn = connect_db()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT 500")
    logs = cur.fetchall()

    cur.close()
    conn.close()
    return render_template("admin/audit-log.html", logs=logs)
