from flask import Flask, render_template, session, redirect
from flask_cors import CORS
import database

# Import blueprints
from routes.auth_routes import auth_bp
from routes.doctor_routes import doctor_bp
from routes.patient_routes import patient_bp
from routes.admin_routes import admin_bp

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = "supersecretkey"
app.config["SESSION_TYPE"] = "filesystem"
CORS(app)

# Register Blueprints
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(doctor_bp, url_prefix="/doctor")
app.register_blueprint(patient_bp, url_prefix="/patient")
app.register_blueprint(admin_bp, url_prefix="/admin")

@app.route("/")
def index():
    if "user" in session:
        if session["role"] == "doctor":
            return redirect("/doctor/dashboard")
        elif session["role"] == "admin":
            return redirect("/admin/dashboard")
        elif session["role"] == "patient":
            return redirect("/patient/dashboard")
    return render_template("auth/login.html")

if __name__ == "__main__":
    database.create_tables()
    app.run(debug=True, port=5000)
