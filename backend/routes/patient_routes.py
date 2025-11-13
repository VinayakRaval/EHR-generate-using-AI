from flask import Blueprint, render_template, session, redirect, send_from_directory, request, flash
import os
import json
import database
from database import connect_db
from utils.export_utils import export_patient_csv, generate_patient_pdf
from utils.audit_logger import log_action

patient_bp = Blueprint("patient", __name__, url_prefix="/patient")


# --------------------------------------------------
# Helper: Require Logged-in Patient
# --------------------------------------------------
def require_patient():
    return ("patient" in session and session.get("role") == "patient")


# --------------------------------------------------
# Patient Dashboard
# --------------------------------------------------
@patient_bp.route("/dashboard")
def patient_dashboard():
    if not require_patient():
        return redirect("/auth/login")

    patient_session = session["patient"]
    pid = patient_session["patient_id"]

    conn = connect_db()
    cur = conn.cursor(dictionary=True)

    # Refresh full patient record
    cur.execute("""
        SELECT p.*, d.name AS doctor_name
        FROM patients p
        LEFT JOIN doctors d ON p.doctor_id = d.doctor_id
        WHERE p.patient_id = %s
    """, (pid,))
    patient = cur.fetchone()

    # Prescriptions
    cur.execute("""
        SELECT p.*, d.name AS doctor_name
        FROM prescriptions p
        JOIN doctors d ON p.doctor_id=d.doctor_id
        WHERE p.patient_id=%s
        ORDER BY p.created_at DESC
    """, (pid,))
    prescriptions = cur.fetchall()

    for pres in prescriptions:
        meds = pres.get("medicines")
        pres["medicines"] = json.loads(meds) if meds else []

    # Lab Reports
    cur.execute("""
        SELECT *
        FROM lab_reports
        WHERE patient_id=%s
        ORDER BY upload_date DESC
    """, (pid,))
    reports = cur.fetchall()

    # Summary Stats
    cur.execute("SELECT COUNT(*) AS total FROM prescriptions WHERE patient_id=%s", (pid,))
    patient["total_prescriptions"] = cur.fetchone()["total"]

    cur.execute("SELECT COUNT(*) AS total FROM lab_reports WHERE patient_id=%s", (pid,))
    patient["total_reports"] = cur.fetchone()["total"]

    cur.close()
    conn.close()

    return render_template("patient/dashboard.html",
                           patient=patient,
                           prescriptions=prescriptions,
                           reports=reports)


# --------------------------------------------------
# View All Prescriptions
# --------------------------------------------------
@patient_bp.route("/view-prescriptions")
def view_prescriptions():
    if not require_patient():
        return redirect("/auth/login")

    patient = session["patient"]

    conn = connect_db()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT p.*, d.name AS doctor_name
        FROM prescriptions p
        LEFT JOIN doctors d ON p.doctor_id = d.doctor_id
        WHERE p.patient_id = %s
        ORDER BY p.created_at DESC
    """, (patient["patient_id"],))

    prescriptions = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("patient/view-prescriptions.html",
                           patient=patient,
                           prescriptions=prescriptions)


# --------------------------------------------------
# View Reports
# --------------------------------------------------
@patient_bp.route("/view-reports")
def view_reports():
    if not require_patient():
        return redirect("/auth/login")

    patient = session["patient"]

    conn = connect_db()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT lr.*, d.name AS doctor_name
        FROM lab_reports lr
        LEFT JOIN doctors d ON lr.doctor_id = d.doctor_id
        WHERE lr.patient_id = %s
        ORDER BY lr.upload_date DESC
    """, (patient["patient_id"],))

    reports = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("patient/view-reports.html",
                           patient=patient,
                           reports=reports)


# --------------------------------------------------
# Download Report
# --------------------------------------------------
@patient_bp.route("/download-report/<int:report_id>")
def download_report(report_id):
    if not require_patient():
        return redirect("/auth/login")

    conn = connect_db()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT * FROM lab_reports WHERE report_id=%s", (report_id,))
    report = cur.fetchone()

    cur.close()
    conn.close()

    if not report:
        flash("Report not found", "danger")
        return redirect("/patient/view-reports")

    folder = os.path.join(os.getcwd(), "static", "uploads", "reports")
    filename = report["report_file"]

    return send_from_directory(folder, filename, as_attachment=True)


# --------------------------------------------------
# Export Patient Data (CSV / PDF)
# --------------------------------------------------
@patient_bp.route("/export-data", methods=["GET", "POST"])
def export_data():
    if not require_patient():
        return redirect("/auth/login")

    patient = session["patient"]

    if request.method == "POST":
        export_type = request.form.get("export_type", "csv")

        conn = connect_db()
        cur = conn.cursor(dictionary=True)

        # Prescriptions
        cur.execute("""
            SELECT p.*, d.name AS doctor_name
            FROM prescriptions p
            LEFT JOIN doctors d ON p.doctor_id = d.doctor_id
            WHERE p.patient_id = %s
            ORDER BY p.created_at DESC
        """, (patient["patient_id"],))
        prescriptions = cur.fetchall()

        # Reports
        cur.execute("""
            SELECT lr.*, d.name AS doctor_name
            FROM lab_reports lr
            LEFT JOIN doctors d ON lr.doctor_id = d.doctor_id
            WHERE lr.patient_id = %s
            ORDER BY lr.upload_date DESC
        """, (patient["patient_id"],))

        reports = cur.fetchall()

        cur.close()
        conn.close()

        # Generate File
        if export_type == "csv":
            filepath = export_patient_csv(patient, prescriptions, reports)
        else:
            filepath = generate_patient_pdf(patient, prescriptions, reports)

        # Log export
        log_action("patient", patient["patient_id"], f"Exported {export_type.upper()}")

        return redirect("/static/exports/" + os.path.basename(filepath))

    return render_template("patient/export-data.html", patient=patient)
