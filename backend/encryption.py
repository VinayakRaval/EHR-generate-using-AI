# D:\EHR-generate-using-AI\backend\encryption.py
# ==============================================
# ⚠️ Development Mode: Plain-text password system
# NOTE: Do NOT use this in production!
# ==============================================

def hash_password(password: str) -> str:
    """
    Plain text password passthrough (no encryption)
    """
    return password


def check_password(plain_password: str, stored_password: str) -> bool:
    """
    Simple comparison for plain text passwords
    """
    try:
        return plain_password == stored_password
    except Exception as e:
        print("[Encryption] Password check error:", e)
        return False
