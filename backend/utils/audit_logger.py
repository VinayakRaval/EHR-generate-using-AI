import database
from datetime import datetime

def log_action(user_role, user_id, action):
    """
    Records an activity log entry in the activity_logs table.
    user_role: "admin" | "doctor" | "patient"
    user_id: int
    action: string describing the activity
    """
    try:
        conn = database.connect_db()
        cursor = conn.cursor()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
            INSERT INTO activity_logs (user_role, user_id, action, timestamp)
            VALUES (%s, %s, %s, %s)
        """, (user_role, user_id, action, timestamp))

        conn.commit()
        cursor.close()
        conn.close()

    except Exception as e:
        print(f"[AuditLogger] Failed to record action: {e}")
