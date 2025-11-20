import os
import bcrypt
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()  # Load DATABASE_URL from .env

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("❌ DATABASE_URL is missing in .env")

def get_connection():
    """Create a PostgreSQL DB connection"""
    try:
        conn = psycopg2.connect(
            DATABASE_URL,
            sslmode="require",
            cursor_factory=psycopg2.extras.RealDictCursor,
        )
        return conn
    except Exception as e:
        print("❌ Database connection error:", e)
        raise e


def init_db():
    """Create tables if missing"""
    conn = get_connection()
    cur = conn.cursor()

    # USERS TABLE (PostgreSQL syntax)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # PROJECTS TABLE
    cur.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            name VARCHAR(255) NOT NULL,
            lines_of_code INTEGER DEFAULT 0,
            files_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # PASSWORD RESET TABLE
    cur.execute("""
        CREATE TABLE IF NOT EXISTS password_reset (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) NOT NULL,
            otp_code VARCHAR(10) NOT NULL,
            otp_expiry BIGINT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    conn.close()
    print("✔ Database initialized successfully")


# ====================
# AUTH HELPERS
# ====================

def insert_user(username, email, plain_password):
    conn = get_connection()
    cur = conn.cursor()
    hashed = bcrypt.hashpw(plain_password.encode(), bcrypt.gensalt()).decode()

    try:
        cur.execute("""
            INSERT INTO users (username, email, password)
            VALUES (%s, %s, %s)
        """, (username, email, hashed))

        conn.commit()
        return True
    except Exception as e:
        print("insert_user error:", e)
        return False
    finally:
        conn.close()


def find_user_by_email(email):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email = %s", (email,))
    row = cur.fetchone()
    conn.close()
    return row


def update_password(email, new_plain_password):
    conn = get_connection()
    cur = conn.cursor()
    hashed = bcrypt.hashpw(new_plain_password.encode(), bcrypt.gensalt()).decode()

    cur.execute("UPDATE users SET password = %s WHERE email = %s",
                (hashed, email))

    conn.commit()
    updated = cur.rowcount > 0
    conn.close()
    return updated


def check_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


# ====================
# PROJECT HELPERS
# ====================

def get_user_projects(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM projects WHERE user_id = %s", (user_id,))
    rows = cur.fetchall()
    conn.close()
    return rows


def create_project(user_id, name):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO projects (user_id, name)
        VALUES (%s, %s)
        RETURNING id
    """, (user_id, name))
    project_id = cur.fetchone()["id"]
    conn.commit()
    conn.close()
    return project_id


def get_dashboard_stats(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            COUNT(*) AS total_projects,
            COALESCE(SUM(lines_of_code), 0) AS total_lines,
            COALESCE(SUM(files_count), 0) AS total_files
        FROM projects WHERE user_id = %s
    """, (user_id,))
    stats = cur.fetchone()
    conn.close()
    return stats


# ====================
# OTP HELPERS
# ====================

def save_password_reset_otp(email, otp_code, otp_expiry):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM password_reset WHERE email = %s", (email,))

    cur.execute("""
        INSERT INTO password_reset (email, otp_code, otp_expiry)
        VALUES (%s, %s, %s)
    """, (email, otp_code, int(otp_expiry)))

    conn.commit()
    conn.close()


def get_password_reset_record(email):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM password_reset 
        WHERE email = %s 
        ORDER BY id DESC LIMIT 1
    """, (email,))
    row = cur.fetchone()
    conn.close()
    return row


def clear_password_reset(email):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM password_reset WHERE email = %s", (email,))
    conn.commit()
    conn.close()
