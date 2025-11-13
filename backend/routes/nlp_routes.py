# routes/nlp_routes.py
import os
import json
from flask import Blueprint, request, jsonify
from database import connect_db

# install openai: pip install openai
import openai

nlp_bp = Blueprint("nlp", __name__)

OPENAI_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")  # set via env

openai.api_key = OPENAI_KEY

def build_prompt(text, patient_info=None):
    """
    Prompt instructs the model to return pure JSON with keys:
      diagnosis, symptoms (list), medicines (list of objects), transcript
    """
    patient_note = ""
    if patient_info:
        parts = []
        for k in ("name","age","city","phone"):
            v = patient_info.get(k)
            if v:
                parts.append(f"{k}: {v}")
        if parts:
            patient_note = "Patient info: " + "; ".join(parts) + "\n\n"

    return f"""
You are a medical assistant that extracts structured prescription data from a doctor's dictated note.
Return a JSON object and ONLY a JSON object (no extra commentary).

Input text (doctor dictated):
{patient_note}{text}

Required JSON keys:
- diagnosis: string (short)
- symptoms: array of short strings (may be empty)
- medicines: array of objects {{"name": string, "dose": string, "freq": string, "duration": string}} (may be empty)
- transcript: the cleaned original transcript string

If any field is unknown, use an empty string or empty array. Strict JSON only.
"""

@nlp_bp.route("/structure-prescription", methods=["POST"])
def structure_prescription():
    if OPENAI_KEY is None:
        return jsonify({"error":"OpenAI API key not set on server"}), 500

    body = request.get_json(force=True) or {}
    text = body.get("text", "")
    patient_id = body.get("patient_id")

    # optional: fetch patient to include context (name/age/city/phone)
    patient_info = {}
    if patient_id:
        try:
            db = connect_db()
            cur = db.cursor(dictionary=True)
            cur.execute("SELECT first_name, last_name, COALESCE(age,'') AS age, COALESCE(city,'') AS city, COALESCE(phone,'') as phone FROM patients WHERE patient_id=%s", (patient_id,))
            row = cur.fetchone()
            if row:
                patient_info = {
                    "name": f"{row.get('first_name','')} {row.get('last_name','')}".strip(),
                    "age": row.get("age") or "",
                    "city": row.get("city") or "",
                    "phone": row.get("phone") or ""
                }
            cur.close()
            db.close()
        except Exception:
            patient_info = {}

    if not text:
        return jsonify({"error":"No text provided"}), 400

    prompt = build_prompt(text, patient_info)

    try:
        # Use Chat Completion API
        resp = openai.ChatCompletion.create(
            model=OPENAI_MODEL,
            messages=[
                {"role":"system","content":"You are an assistant that outputs only JSON."},
                {"role":"user","content": prompt}
            ],
            temperature=0.0,
            max_tokens=700
        )

        content = ""
        if resp and "choices" in resp and len(resp["choices"])>0:
            content = resp["choices"][0]["message"]["content"].strip()

        # Ensure JSON parse
        try:
            parsed = json.loads(content)
        except Exception:
            # As a fallback, try to extract JSON substring
            import re
            m = re.search(r"\{.*\}", content, flags=re.S)
            if m:
                parsed = json.loads(m.group(0))
            else:
                return jsonify({"error":"OpenAI returned non-JSON response", "raw": content}), 500

        # Attach transcript if missing
        if "transcript" not in parsed:
            parsed["transcript"] = text

        # Ensure keys exist
        parsed.setdefault("diagnosis", "")
        parsed.setdefault("symptoms", [])
        parsed.setdefault("medicines", [])
        parsed.setdefault("transcript", text)

        return jsonify(parsed)
    except openai.error.OpenAIError as e:
        return jsonify({"error":"OpenAI API error", "detail": str(e)}), 500
    except Exception as e:
        return jsonify({"error":"Unexpected server error", "detail": str(e)}), 500
