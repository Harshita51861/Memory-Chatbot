# backend/config.py

class Config:
    # =========================
    # MySQL Database Settings
    # =========================
    MYSQL_HOST = "localhost"
    MYSQL_USER = "root"
    MYSQL_PASSWORD = "@MONA689"   # CHANGE THIS
    MYSQL_DATABASE = "memory_chatbot"

    # =========================
    # Admin credentials
    # =========================
    ADMIN_USERNAME = "admin"
    ADMIN_PASSWORD = "12345"

    # =========================
    # Memory settings
    # =========================
    MIN_CONFIDENCE = 0.7
    DECAY_RATE = 0.01

    # =========================
    # Flask settings
    # =========================
    SECRET_KEY = "your-secret-key-change-this"
    DEBUG = True

    # =========================
    # CORS
    # =========================
    CORS_ORIGINS = ["http://localhost:3000"]
