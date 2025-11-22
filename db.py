import os
import uuid
import bcrypt
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
import streamlit as st
from datetime import date, timedelta  # 🔹 for streak calc

load_dotenv()  # Load DATABASE_URL from .env

DATABASE_URL = os.getenv("DATABASE_URL") or st.secrets.get("DATABASE_URL")

if not DATABASE_URL:
    st.error("DATABASE_URL missing! Please add in Streamlit Secrets.")


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
    """Create tables if missing and ensure required columns exist"""
    conn = get_connection()
    cur = conn.cursor()

    # USERS TABLE
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """
    )

    # PROJECTS TABLE
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS projects (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            name VARCHAR(255) NOT NULL,
            lines_of_code INTEGER DEFAULT 0,
            files_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """
    )

    # PROJECT FILES TABLE (base create)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS project_files (
            id SERIAL PRIMARY KEY,
            project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
            room_id VARCHAR(100) UNIQUE,
            filename VARCHAR(255),
            language VARCHAR(50) DEFAULT 'javascript',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """
    )

    # 🔧 MIGRATION: ensure columns exist even if table was created earlier without them
    try:
        cur.execute(
            """
            ALTER TABLE project_files
            ADD COLUMN IF NOT EXISTS room_id VARCHAR(100);
        """
        )
    except Exception as e:
        print("room_id migration error:", e)

    try:
        cur.execute(
            """
            ALTER TABLE project_files
            ADD COLUMN IF NOT EXISTS filename VARCHAR(255);
        """
        )
    except Exception as e:
        print("filename migration error:", e)

    try:
        cur.execute(
            """
            ALTER TABLE project_files
            ADD COLUMN IF NOT EXISTS language VARCHAR(50) DEFAULT 'javascript';
        """
        )
    except Exception as e:
        print("language migration error:", e)

    # PASSWORD RESET TABLE
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS password_reset (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) NOT NULL,
            otp_code VARCHAR(10) NOT NULL,
            otp_expiry BIGINT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """
    )

    # 🔹 NEW: USER LOGINS TABLE FOR STREAKS
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS user_logins (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            login_date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, login_date)
        );
    """
    )

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
        cur.execute(
            """
            INSERT INTO users (username, email, password)
            VALUES (%s, %s, %s)
        """,
            (username, email, hashed),
        )

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

    cur.execute(
        "UPDATE users SET password = %s WHERE email = %s",
        (hashed, email),
    )

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
    cur.execute(
        "SELECT * FROM projects WHERE user_id = %s ORDER BY created_at DESC",
        (user_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def create_project(user_id, name):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO projects (user_id, name)
        VALUES (%s, %s)
        RETURNING id
    """,
        (user_id, name),
    )
    project_id = cur.fetchone()["id"]
    conn.commit()
    conn.close()
    return project_id


def get_dashboard_stats(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT 
            COUNT(*) AS total_projects,
            COALESCE(SUM(lines_of_code), 0) AS total_lines,
            COALESCE(SUM(files_count), 0) AS total_files
        FROM projects WHERE user_id = %s
    """,
        (user_id,),
    )
    stats = cur.fetchone()
    conn.close()
    return stats


# ---------- PROJECT FILES HELPERS ----------


def get_project_files(project_id):
    """Return all files for a given project."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT * FROM project_files
        WHERE project_id = %s
        ORDER BY created_at ASC
    """,
        (project_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def create_project_file(project_id, filename, language="javascript"):
    """
    Create a new file under a project.
    Each file gets a unique room_id used by the editor as roomId.
    """
    conn = get_connection()
    cur = conn.cursor()

    room_id = uuid.uuid4().hex  # use as roomId in editor route

    cur.execute(
        """
        INSERT INTO project_files (project_id, room_id, filename, language)
        VALUES (%s, %s, %s, %s)
        RETURNING id, room_id
    """,
        (project_id, room_id, filename, language),
    )
    row = cur.fetchone()

    # increment files_count in projects
    cur.execute(
        """
        UPDATE projects
        SET files_count = files_count + 1
        WHERE id = %s
    """,
        (project_id,),
    )

    conn.commit()
    conn.close()

    return {"id": row["id"], "room_id": row["room_id"]}


# ====================
# STREAK / LOGIN HELPERS
# ====================


def record_login(user_id):
    """
    Store a login for today for this user.
    One row per (user, day).
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO user_logins (user_id, login_date)
        VALUES (%s, CURRENT_DATE)
        ON CONFLICT (user_id, login_date) DO NOTHING
    """,
        (user_id,),
    )
    conn.commit()
    conn.close()


def get_current_streak(user_id):
    """
    Calculate the current login streak for a user
    = number of consecutive days with logins, ending at the most recent login day.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT login_date
        FROM user_logins
        WHERE user_id = %s
        ORDER BY login_date DESC
    """,
        (user_id,),
    )
    rows = cur.fetchall()
    conn.close()

    if not rows:
        return 0

    dates = [r["login_date"] for r in rows]
    dates_set = set(dates)

    # streak ends at the latest login date (not necessarily today)
    current_day = dates[0]
    streak = 0

    while current_day in dates_set:
        streak += 1
        current_day = current_day - timedelta(days=1)

    return streak


# ====================
# OTP HELPERS
# ====================


def save_password_reset_otp(email, otp_code, otp_expiry):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM password_reset WHERE email = %s", (email,))

    cur.execute(
        """
        INSERT INTO password_reset (email, otp_code, otp_expiry)
        VALUES (%s, %s, %s)
    """,
        (email, otp_code, int(otp_expiry)),
    )

    conn.commit()
    conn.close()


def get_password_reset_record(email):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT * FROM password_reset 
        WHERE email = %s 
        ORDER BY id DESC LIMIT 1
    """,
        (email,),
    )
    row = cur.fetchone()
    conn.close()
    return row


def clear_password_reset(email):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM password_reset WHERE email = %s", (email,))
    conn.commit()
    conn.close()
