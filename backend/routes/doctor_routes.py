from flask import Blueprint, request, jsonify, send_file, session, render_template, redirect, abort
import os
import json
from datetime import datetime

from utils.audit_logger import log_action
from database import connect_db
from utils.export_utils import (
    export_patient_csv,
    generate_patient_pdf,
    generate_prescription_pdf
)

doctor_bp = Blueprint("doctor", __name__, url_prefix="/doctor")

# Paths
ROOT_DIR = os.getcwd()
STATIC_DIR = os.path.join(ROOT_DIR, "static")
UPLOADS_DIR = os.path.join(STATIC_DIR, "uploads")
PRESCRIPTIONS_DIR = os.path.join(UPLOADS_DIR, "prescriptions")
REPORTS_DIR = os.path.join(UPLOADS_DIR, "reports")
EXPORT_DIR = os.path.join(STATIC_DIR, "exports")

os.makedirs(PRESCRIPTIONS_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(EXPORT_DIR, exist_ok=True)


# ----------------------------------------
# Helpers
# ----------------------------------------
def get_current_doctor():
    if session.get("role") == "doctor":
        return session.get("doctor")
    return None


def require_doctor():
    return session.get("role") == "doctor" and "doctor" in session


# ========================================================================
#              ADD PRESCRIPTION (NORMAL + AI FINAL TEXT)
# ========================================================================
@doctor_bp.route("/add-prescription", methods=["POST"])
def add_prescription():
    doctor = get_current_doctor()
    if not doctor:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    data = request.get_json(force=True, silent=True) or {}

    patient_id = data.get("patient_id")
    diagnosis = (data.get("diagnosis") or "").strip()
    prescription_text = (data.get("prescription_text") or "").strip()
    medicines = data.get("medicines")

    if not patient_id or not diagnosis or not prescription_text:
        return jsonify({"status": "error",
                        "message": "Missing patient_id, diagnosis or prescription_text"}), 400

    db = connect_db()
    cur = db.cursor(dictionary=True)

    try:
        cur.execute("SELECT patient_id, doctor_id FROM patients WHERE patient_id=%s", (patient_id,))
        patient = cur.fetchone()

        if not patient:
            return jsonify({"status": "error", "message": "Patient not found"}), 404

        if patient["doctor_id"] != doctor["doctor_id"]:
            return jsonify({"status": "error", "message": "This is not your patient"}), 403

        meds_json = json.dumps(medicines, ensure_ascii=False) if medicines else None

        cur.execute("""
            INSERT INTO prescriptions
                (doctor_id, patient_id, diagnosis, prescription_text, medicines, created_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
        """, (doctor["doctor_id"], patient_id, diagnosis, prescription_text, meds_json))

        db.commit()
        pres_id = cur.lastrowid

        log_action("doctor", doctor["doctor_id"], f"Added prescription ID {pres_id}")

        return jsonify({"status": "success", "prescription_id": pres_id})

    except Exception as e:
        db.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

    finally:
        cur.close()
        db.close()


# ========================================================================
#                       UPLOAD LAB REPORT
# ========================================================================
@doctor_bp.route("/upload-report", methods=["POST"])
def upload_report():
    doctor = get_current_doctor()
    if not doctor:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    patient_id = request.form.get("patient_id")
    report_name = request.form.get("report_name") or "Lab Report"
    file = request.files.get("file")

    if not patient_id or not file:
        return jsonify({"status": "error", "message": "Missing data"}), 400

    filename = f"report_{patient_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
    filepath = os.path.join(REPORTS_DIR, filename)
    file.save(filepath)

    db = connect_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        INSERT INTO lab_reports (doctor_id, patient_id, report_name, report_file, upload_date)
        VALUES (%s, %s, %s, %s, NOW())
    """, (doctor["doctor_id"], patient_id, report_name, filename))

    db.commit()
    report_id = cur.lastrowid

    log_action("doctor", doctor["doctor_id"], f"Uploaded report ID {report_id}")

    cur.close()
    db.close()

    return jsonify({
        "status": "success",
        "report_id": report_id,
        "file": filename
    })


# ========================================================================
#                GET PRESCRIPTIONS FOR ONE PATIENT
# ========================================================================
@doctor_bp.route("/prescriptions/<int:pid>")
def get_prescriptions(pid):
    doctor = get_current_doctor()
    if not doctor:
        return jsonify({"status": "error"}), 401

    db = connect_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT p.*, d.name AS doctor_name
        FROM prescriptions p
        JOIN doctors d ON p.doctor_id = d.doctor_id
        WHERE p.patient_id=%s
        ORDER BY p.created_at DESC
    """, (pid,))

    rows = cur.fetchall()

    for r in rows:
        try:
            r["medicines"] = json.loads(r["medicines"]) if r["medicines"] else []
        except:
            r["medicines"] = []

    cur.close()
    db.close()

    return jsonify({"status": "success", "data": rows})


# ========================================================================
#             EXPORT FULL PATIENT PDF (Reports + Prescriptions)
# ========================================================================
@doctor_bp.route("/export_pdf/<int:pid>")
def export_pdf(pid):
    doctor = get_current_doctor()
    if not doctor:
        return redirect("/auth/login")

    db = connect_db()
    cur = db.cursor(dictionary=True)

    cur.execute("SELECT * FROM patients WHERE patient_id=%s", (pid,))
    patient = cur.fetchone()

    if not patient:
        return abort(404)

    cur.execute("""
        SELECT p.*, d.name AS doctor_name
        FROM prescriptions p
        JOIN doctors d ON p.doctor_id=d.doctor_id
        WHERE p.patient_id=%s
    """, (pid,))
    prescriptions = cur.fetchall()

    for p in prescriptions:
        p["medicines"] = json.loads(p["medicines"]) if p["medicines"] else []

    cur.execute("""
        SELECT r.*, d.name AS doctor_name
        FROM lab_reports r
        JOIN doctors d ON r.doctor_id=d.doctor_id
        WHERE r.patient_id=%s
    """, (pid,))
    reports = cur.fetchall()

    filepath = generate_patient_pdf(patient, prescriptions, reports)

    cur.close()
    db.close()

    return send_file(filepath, as_attachment=True)


# ========================================================================
#                   DOWNLOAD SINGLE PRESCRIPTION PDF
# ========================================================================
@doctor_bp.route("/prescription/<int:prescription_id>/pdf")
def download_prescription_pdf(prescription_id):
    db = connect_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT p.*, d.name AS doctor_name, pa.first_name, pa.last_name
        FROM prescriptions p
        JOIN doctors d ON p.doctor_id=d.doctor_id
        JOIN patients pa ON p.patient_id=pa.patient_id
        WHERE p.prescription_id=%s
    """, (prescription_id,))
    pres = cur.fetchone()

    if not pres:
        return abort(404)

    pres["medicines"] = json.loads(pres["medicines"]) if pres["medicines"] else []

    filepath = generate_prescription_pdf(pres)

    cur.close()
    db.close()

    return send_file(filepath, as_attachment=True)


# ========================================================================
#                          DOWNLOAD LAB REPORT
# ========================================================================
@doctor_bp.route("/report/<int:report_id>/download")
def download_report(report_id):
    doctor = get_current_doctor()

    db = connect_db()
    cur = db.cursor(dictionary=True)

    cur.execute("SELECT report_file FROM lab_reports WHERE report_id=%s", (report_id,))
    row = cur.fetchone()

    if not row:
        return abort(404)

    file_path = os.path.join(REPORTS_DIR, row["report_file"])

    if not os.path.exists(file_path):
        return abort(404)

    log_action("doctor", doctor.get("doctor_id"), f"Downloaded report {report_id}")

    cur.close()
    db.close()

    return send_file(file_path, as_attachment=True)


# ========================================================================
#                             DOCTOR DASHBOARD
# ========================================================================
@doctor_bp.route("/dashboard")
def doctor_dashboard():
    if not require_doctor():
        return redirect("/auth/login")

    doctor = session["doctor"]
    did = doctor["doctor_id"]

    db = connect_db()
    cur = db.cursor(dictionary=True)

    # Counts
    cur.execute("SELECT COUNT(*) AS total FROM patients WHERE doctor_id=%s", (did,))
    total_patients = cur.fetchone()["total"]

    cur.execute("SELECT COUNT(*) AS total FROM prescriptions WHERE doctor_id=%s", (did,))
    total_prescriptions = cur.fetchone()["total"]

    cur.execute("SELECT COUNT(*) AS total FROM lab_reports WHERE doctor_id=%s", (did,))
    total_reports = cur.fetchone()["total"]

    cur.execute("SELECT COUNT(*) AS total FROM ai_logs WHERE doctor_id=%s", (did,))
    ai_logs_count = cur.fetchone()["total"]

    # RECENT PATIENTS (fixed age)
    cur.execute("""
        SELECT 
            p.patient_id,
            p.first_name,
            p.last_name,
            TIMESTAMPDIFF(YEAR, p.dob, CURDATE()) AS age,
            p.phone,
            p.address,

            (SELECT MAX(created_at) FROM prescriptions WHERE patient_id = p.patient_id) AS last_visit,
            (SELECT COUNT(*) FROM prescriptions WHERE patient_id = p.patient_id) AS prescription_count,
            (SELECT COUNT(*) FROM lab_reports WHERE patient_id = p.patient_id) AS report_count

        FROM patients p
        WHERE p.doctor_id=%s
        ORDER BY (last_visit IS NULL), last_visit DESC
        LIMIT 8
    """, (did,))

    patients = cur.fetchall()

    cur.close()
    db.close()

    return render_template("doctor/dashboard.html",
                           doctor=doctor,
                           total_patients=total_patients,
                           total_prescriptions=total_prescriptions,
                           total_reports=total_reports,
                           ai_logs_count=ai_logs_count,
                           patients=patients)

# ========================================================================
#                     ADVANCED NLP — STRUCTURE PRESCRIPTION
# ========================================================================
@doctor_bp.route("/ai/structure", methods=["POST"])
def ai_structure():
    from flask import request, jsonify
    import spacy
    import re

    data = request.get_json() or {}
    text = data.get("text", "").strip()

    if not text:
        return jsonify({"status": "error", "message": "No text received"}), 400

    try:
        nlp = spacy.load("en_core_web_sm")
        doc = nlp(text)

        # -------- Diagnosis --------
        diagnosis = ""
        patterns = [
            r"diagnosis is (.*?)(?:\.|$)",
            r"diagnosed with (.*?)(?:\.|$)"
        ]
        for p in patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                diagnosis = m.group(1).strip()
                break

        # fallback
        if not diagnosis:
            for ent in doc.ents:
                if ent.label_ in ["DISEASE", "CONDITION", "SYMPTOM"]:
                    diagnosis = ent.text
                    break

        # -------- Symptoms --------
        symptoms = []
        symptom_words = ["fever", "pain", "cough", "cold", "vomit",
                         "headache", "fatigue", "weakness", "breathing"]

        for sent in doc.sents:
            if any(w in sent.text.lower() for w in symptom_words):
                symptoms.append(sent.text.strip())

        # -------- Medicines --------
        medicines = []
        med_pattern = r"([A-Za-z]+[A-Za-z0-9]*)\s*(\d+mg|\d+ml|\d+mcg)?\s*(tablet|capsule|syrup|drop)?\s*(once|twice|daily|night|morning|evening)?\s*(for\s*\d+\s*(days|weeks))?"

        for m in re.finditer(med_pattern, text, re.IGNORECASE):
            g = m.groups()
            if g[0]:
                medicines.append({
                    "name": g[0],
                    "dose": g[1] or "",
                    "form": g[2] or "",
                    "freq": g[3] or "",
                    "duration": g[4] or ""
                })

        # -------- Build structured preview --------
        structured = f"""
🩺 Diagnosis:
{diagnosis or "Not detected"}

🤒 Symptoms:
{', '.join(symptoms) if symptoms else "Not detected"}

💊 Medicines:
""" + "\n".join([f"- {m['name']} {m['dose']} {m['form']} {m['freq']} {m['duration']}".strip()
                  for m in medicines])

        return jsonify({
            "status": "success",
            "structured": structured,
            "diagnosis": diagnosis,
            "symptoms": symptoms,
            "medicines": medicines
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
