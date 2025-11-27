import os
import uuid
import bcrypt
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
import streamlit as st
from datetime import date, timedelta
from contextlib import contextmanager

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL") or st.secrets.get("DATABASE_URL")

if not DATABASE_URL:
    st.error("DATABASE_URL missing! Please add in Streamlit Secrets.")

def get_connection():
    """Get database connection - FIXED: No more yield"""
    try:
        conn = psycopg2.connect(
            DATABASE_URL,
            sslmode="require",
            cursor_factory=psycopg2.extras.RealDictCursor,
            connect_timeout=10
        )
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        raise e

@contextmanager
def get_db_cursor():
    """Context manager for database operations - PROPER connection handling"""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        yield cur
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()

def init_db():
    """Create tables if missing and ensure required columns exist"""
    with get_db_cursor() as cur:
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

        # PROJECT FILES TABLE
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS project_files (
                id SERIAL PRIMARY KEY,
                project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
                room_id VARCHAR(100) UNIQUE,
                filename VARCHAR(255),
                language VARCHAR(50) DEFAULT 'javascript',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """
        )

        # MIGRATION: ensure columns exist
        try:
            cur.execute("ALTER TABLE project_files ADD COLUMN IF NOT EXISTS room_id VARCHAR(100);")
        except Exception as e:
            print("room_id migration error:", e)

        try:
            cur.execute("ALTER TABLE project_files ADD COLUMN IF NOT EXISTS filename VARCHAR(255);")
        except Exception as e:
            print("filename migration error:", e)

        try:
            cur.execute("ALTER TABLE project_files ADD COLUMN IF NOT EXISTS language VARCHAR(50) DEFAULT 'javascript';")
        except Exception as e:
            print("language migration error:", e)

        try:
            cur.execute("ALTER TABLE project_files ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;")
        except Exception as e:
            print("updated_at migration error:", e)

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

        # USER LOGINS TABLE FOR STREAKS
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
    print("✔ Database initialized successfully")

# ====================
# AUTH HELPERS
# ====================

def insert_user(username, email, plain_password):
    with get_db_cursor() as cur:
        hashed = bcrypt.hashpw(plain_password.encode(), bcrypt.gensalt()).decode()
        try:
            cur.execute(
                """
                INSERT INTO users (username, email, password)
                VALUES (%s, %s, %s)
            """,
                (username, email, hashed),
            )
            return True
        except Exception as e:
            print("insert_user error:", e)
            return False

def find_user_by_email(email):
    with get_db_cursor() as cur:
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        return cur.fetchone()

def update_password(email, new_plain_password):
    with get_db_cursor() as cur:
        hashed = bcrypt.hashpw(new_plain_password.encode(), bcrypt.gensalt()).decode()
        cur.execute(
            "UPDATE users SET password = %s WHERE email = %s",
            (hashed, email),
        )
        return cur.rowcount > 0

def check_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())

# ====================
# PROJECT HELPERS
# ====================

def get_user_projects(user_id):
    with get_db_cursor() as cur:
        cur.execute(
            "SELECT * FROM projects WHERE user_id = %s ORDER BY created_at DESC",
            (user_id,),
        )
        return cur.fetchall()

def create_project(user_id, name):
    with get_db_cursor() as cur:
        cur.execute(
            """
            INSERT INTO projects (user_id, name)
            VALUES (%s, %s)
            RETURNING id
        """,
            (user_id, name),
        )
        result = cur.fetchone()
        return result["id"] if result else None

def get_dashboard_stats(user_id):
    with get_db_cursor() as cur:
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
        return stats or {"total_projects": 0, "total_lines": 0, "total_files": 0}

# ---------- PROJECT FILES HELPERS ----------

def get_project_files(project_id):
    with get_db_cursor() as cur:
        cur.execute(
            """
            SELECT * FROM project_files
            WHERE project_id = %s
            ORDER BY created_at ASC
        """,
            (project_id,),
        )
        return cur.fetchall()

def create_project_file(project_id, filename, language="javascript"):
    with get_db_cursor() as cur:
        room_id = uuid.uuid4().hex

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

        return {"id": row["id"], "room_id": row["room_id"]} if row else None

def delete_project(project_id):
    with get_db_cursor() as cur:
        try:
            cur.execute("DELETE FROM project_files WHERE project_id = %s", (project_id,))
            cur.execute("DELETE FROM projects WHERE id = %s", (project_id,))
            return True
        except Exception as e:
            print("delete_project error:", e)
            return False

def delete_project_file(file_id):
    with get_db_cursor() as cur:
        try:
            # get project_id for decrement
            cur.execute("SELECT project_id FROM project_files WHERE id = %s", (file_id,))
            row = cur.fetchone()
            if not row:
                return False
            project_id = row["project_id"]

            # delete file
            cur.execute("DELETE FROM project_files WHERE id = %s", (file_id,))

            # update project metadata
            cur.execute(
                "UPDATE projects SET files_count = GREATEST(files_count - 1, 0) WHERE id = %s",
                (project_id,),
            )
            return True
        except Exception as e:
            print("delete_project_file error:", e)
            return False

# ====================
# STREAK / LOGIN HELPERS
# ====================

def record_login(user_id):
    with get_db_cursor() as cur:
        cur.execute(
            """
            INSERT INTO user_logins (user_id, login_date)
            VALUES (%s, CURRENT_DATE)
            ON CONFLICT (user_id, login_date) DO NOTHING
        """,
            (user_id,),
        )

def get_current_streak(user_id):
    with get_db_cursor() as cur:
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

    if not rows:
        return 0

    dates = [r["login_date"] for r in rows]
    dates_set = set(dates)

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
    with get_db_cursor() as cur:
        cur.execute("DELETE FROM password_reset WHERE email = %s", (email,))
        cur.execute(
            """
            INSERT INTO password_reset (email, otp_code, otp_expiry)
            VALUES (%s, %s, %s)
        """,
            (email, otp_code, int(otp_expiry)),
        )

def get_password_reset_record(email):
    with get_db_cursor() as cur:
        cur.execute(
            """
            SELECT * FROM password_reset 
            WHERE email = %s 
            ORDER BY id DESC LIMIT 1
        """,
            (email,),
        )
        return cur.fetchone()

def clear_password_reset(email):
    with get_db_cursor() as cur:
        cur.execute("DELETE FROM password_reset WHERE email = %s", (email,))
        
def get_recent_files(user_id=None, limit=10):
    with get_db_cursor() as cur:
        if user_id is not None:
            cur.execute(
                """
                SELECT pf.id, pf.room_id, pf.filename, pf.created_at as updated_at, 
                       p.name AS project_name, pf.language, p.user_id
                FROM project_files pf
                JOIN projects p ON pf.project_id = p.id
                WHERE p.user_id = %s
                ORDER BY pf.created_at DESC
                LIMIT %s
                """,
                (user_id, limit)
            )
        else:
            cur.execute(
                """
                SELECT pf.id, pf.room_id, pf.filename, pf.created_at as updated_at, 
                       p.name AS project_name, pf.language, p.user_id
                FROM project_files pf
                JOIN projects p ON pf.project_id = p.id
                ORDER BY pf.created_at DESC
                LIMIT %s
                """,
                (limit,)
            )
        return cur.fetchall()