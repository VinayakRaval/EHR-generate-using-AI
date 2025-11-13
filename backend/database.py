import mysql.connector
from mysql.connector import Error

# ✅ MySQL Configuration (XAMPP Default)
DB_CONFIG = {
    "host": "localhost",
    "user": "root",        # Default XAMPP MySQL username
    "password": "",         # Leave empty unless you've set a password
    "database": "ehr_ai_db" # Your EHR database
}

# ✅ Create Connection
def connect_db():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            print("✅ Connected to MySQL Database: ehr_ai_db")
            return connection
    except Error as e:
        print(f"❌ Error connecting to MySQL: {e}")
        return None


# ✅ Function to Create All Tables (Safe to Run Multiple Times)
def create_tables():
    connection = connect_db()
    if not connection:
        print("⚠️ Could not connect to database. Please check XAMPP MySQL.")
        return

    cursor = connection.cursor()

    # Admins Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admins (
        admin_id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        email VARCHAR(150) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Doctors Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS doctors (
        doctor_id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        email VARCHAR(150) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL,
        specialization VARCHAR(100),
        phone VARCHAR(15),
        address VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Patients Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS patients (
        patient_id INT AUTO_INCREMENT PRIMARY KEY,
        doctor_id INT,
        first_name VARCHAR(100) NOT NULL,
        last_name VARCHAR(100),
        gender ENUM('Male','Female','Other'),
        dob DATE,
        phone VARCHAR(15),
        email VARCHAR(150),
        address VARCHAR(255),
        username VARCHAR(100) UNIQUE,
        password VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id)
    )
    """)

    # Prescriptions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS prescriptions (
        prescription_id INT AUTO_INCREMENT PRIMARY KEY,
        doctor_id INT,
        patient_id INT,
        visit_reason VARCHAR(255),
        diagnosis TEXT,
        prescription_text TEXT,
        medicines JSON,
        tests_recommended TEXT,
        next_visit_date DATE,
        doctor_notes TEXT,
        voice_to_text_source TEXT,
        digital_signature VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id),
        FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
    )
    """)

    # Lab Reports Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS lab_reports (
        report_id INT AUTO_INCREMENT PRIMARY KEY,
        patient_id INT,
        doctor_id INT,
        report_name VARCHAR(150) NOT NULL,
        report_file VARCHAR(255) NOT NULL,
        upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
        FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id)
    )
    """)

    # Activity Logs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS activity_logs (
        log_id INT AUTO_INCREMENT PRIMARY KEY,
        user_role ENUM('Admin','Doctor','Patient') NOT NULL,
        user_id INT NOT NULL,
        action VARCHAR(255) NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Encryption Keys Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS encryption_keys (
        key_id INT AUTO_INCREMENT PRIMARY KEY,
        key_name VARCHAR(100) NOT NULL,
        aes_key VARBINARY(255) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # AI Logs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ai_logs (
        ai_log_id INT AUTO_INCREMENT PRIMARY KEY,
        doctor_id INT,
        patient_id INT,
        action_type ENUM('voice_to_text','ai_suggestion','summary'),
        input_text TEXT,
        output_text TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id),
        FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
    )
    """)

    connection.commit()
    cursor.close()
    connection.close()
    print("✅ All tables checked or created successfully!")
