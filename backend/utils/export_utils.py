import os
import csv
import json
from fpdf import FPDF
from datetime import datetime

ROOT_DIR = os.getcwd()
EXPORT_DIR = os.path.join(ROOT_DIR, "static", "exports")
os.makedirs(EXPORT_DIR, exist_ok=True)


def _safe_filename(s: str):
    return "".join(c for c in s if c.isalnum() or c in (" ", "-", "_")).rstrip().replace(" ", "_")


def generate_patient_pdf(patient: dict, prescriptions: list, reports: list) -> str:
    """
    Generate a basic patient summary PDF and return filepath.
    """
    fname = f"patient_{patient.get('patient_id')}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    filepath = os.path.join(EXPORT_DIR, fname)

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Patient Summary", ln=True, align="C")
    pdf.ln(6)

    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, f"Name: {patient.get('first_name','')} {patient.get('last_name','')}", ln=True)
    pdf.cell(0, 8, f"Username: {patient.get('username','')}", ln=True)
    pdf.cell(0, 8, f"Phone: {patient.get('phone','-')}", ln=True)
    pdf.cell(0, 8, f"DOB: {patient.get('dob','-')}", ln=True)
    pdf.cell(0, 8, f"Assigned Doctor: {patient.get('doctor_name','-')}", ln=True)
    pdf.ln(8)

    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 8, "Prescriptions:", ln=True)
    pdf.set_font("Arial", "", 11)
    if prescriptions:
        for pres in prescriptions:
            pdf.multi_cell(0, 6, f"- [{pres.get('created_at')}] {pres.get('doctor_name','')} — {pres.get('diagnosis','')}")
            txt = pres.get("prescription_text", "")
            if txt:
                pdf.multi_cell(0, 6, f"  {txt}")
            meds = pres.get("medicines") or []
            if isinstance(meds, str):
                try:
                    meds = json.loads(meds)
                except:
                    meds = []
            if meds:
                pdf.multi_cell(0, 6, f"  Medicines:")
                for m in meds:
                    pdf.multi_cell(0, 6, f"    • {m.get('name','')} {m.get('dosage','')}")
            pdf.ln(2)
    else:
        pdf.cell(0, 6, "No prescriptions found.", ln=True)

    pdf.ln(6)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 8, "Lab Reports:", ln=True)
    pdf.set_font("Arial", "", 11)
    if reports:
        for r in reports:
            pdf.cell(0, 6, f"- [{r.get('upload_date')}] {r.get('report_name')} ({r.get('report_file')})", ln=True)
    else:
        pdf.cell(0, 6, "No lab reports found.", ln=True)

    pdf.output(filepath)
    return filepath


def generate_prescription_pdf(prescription: dict) -> str:
    """
    Generate a single prescription PDF and return filepath.
    """
    pid = prescription.get("prescription_id") or prescription.get("id") or "unknown"
    fname = f"prescription_{pid}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    filepath = os.path.join(EXPORT_DIR, fname)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Prescription", ln=True, align="C")
    pdf.ln(6)

    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, f"Date: {prescription.get('created_at','')}", ln=True)
    pdf.cell(0, 8, f"Doctor: {prescription.get('doctor_name','')}", ln=True)
    patient_name = f"{prescription.get('first_name','')} {prescription.get('last_name','')}" \
        if prescription.get('first_name') else ""
    if patient_name:
        pdf.cell(0, 8, f"Patient: {patient_name}", ln=True)
    pdf.ln(6)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Diagnosis:", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 6, prescription.get("diagnosis",""))
    pdf.ln(4)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Prescription:", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 6, prescription.get("prescription_text",""))
    pdf.ln(4)

    meds = prescription.get("medicines") or []
    if isinstance(meds, str):
        try:
            meds = json.loads(meds)
        except:
            meds = []
    if meds:
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "Medicines:", ln=True)
        pdf.set_font("Arial", "", 11)
        for m in meds:
            pdf.multi_cell(0, 6, f"- {m.get('name','')} {m.get('dosage','')}")
    pdf.output(filepath)
    return filepath


def export_patient_csv(patient: dict, prescriptions: list, reports: list) -> str:
    """
    Export patient data to CSV (simple format) and return filepath.
    """
    fname = f"patient_{patient.get('patient_id')}_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
    filepath = os.path.join(EXPORT_DIR, fname)

    with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        # header
        writer.writerow(["Patient ID", patient.get("patient_id")])
        writer.writerow(["Name", f"{patient.get('first_name','')} {patient.get('last_name','')}"])
        writer.writerow(["Username", patient.get("username","")])
        writer.writerow([])
        writer.writerow(["Prescriptions"])
        writer.writerow(["Date", "Doctor", "Diagnosis", "Prescription", "Medicines"])
        for pres in prescriptions:
            meds = pres.get("medicines")
            if isinstance(meds, (list, tuple)):
                meds_text = "; ".join([m.get("name","") + (f" ({m.get('dosage','')})" if m.get("dosage") else "") for m in meds])
            else:
                meds_text = meds or ""
            writer.writerow([pres.get("created_at",""), pres.get("doctor_name",""), pres.get("diagnosis",""), pres.get("prescription_text",""), meds_text])

        writer.writerow([])
        writer.writerow(["Lab Reports"])
        writer.writerow(["Date", "Name", "File", "Doctor"])
        for r in reports:
            writer.writerow([r.get("upload_date",""), r.get("report_name",""), r.get("report_file",""), r.get("doctor_name","")])

    return filepath
