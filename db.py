import os
import uuid
import bcrypt
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
import streamlit as st
from datetime import date, timedelta  # 🔹 for streak calc

load_dotenv()  # Load DATABASE_URL from .env

DATABASE_URL = os.getenv("DATABASE_URL")

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

    # 🔹 NEW: USER ACTIVITY TABLE
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS user_activity (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            activity_type VARCHAR(100) NOT NULL,
            description TEXT NOT NULL,
            room_id VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

def find_user_by_username(username):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE LOWER(username) = LOWER(%s)", (username,))
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
    
    # Create project
    cur.execute(
        """
        INSERT INTO projects (user_id, name)
        VALUES (%s, %s)
        RETURNING id
    """,
        (user_id, name),
    )
    project_id = cur.fetchone()["id"]
    
    # Log activity
    log_user_activity(user_id, 'project_created', f'Created project: {name}')
    
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

    # Get user_id for activity logging
    cur.execute("SELECT user_id FROM projects WHERE id = %s", (project_id,))
    project = cur.fetchone()
    
    if project:
        # Log activity
        log_user_activity(project['user_id'], 'file_created', f'Created file: {filename}', room_id)

    conn.commit()
    conn.close()

    return {"id": row["id"], "room_id": row["room_id"]}


def delete_project(project_id):
    """
    Delete a project AND its files.
    CASCADE already deletes files if foreign key is configured, 
    but we delete manually for safety across all DB setups.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Get project info for activity logging
        cur.execute("SELECT name, user_id FROM projects WHERE id = %s", (project_id,))
        project = cur.fetchone()
        
        cur.execute("DELETE FROM project_files WHERE project_id = %s", (project_id,))
        cur.execute("DELETE FROM projects WHERE id = %s", (project_id,))
        
        if project:
            # Log activity
            log_user_activity(project['user_id'], 'project_deleted', f'Deleted project: {project["name"]}')
            
        conn.commit()
        return True
    except Exception as e:
        print("delete_project error:", e)
        return False
    finally:
        conn.close()


def delete_project_file(file_id):
    """
    Delete a single file from project_files table.
    Also decrease the files_count of its project.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        # get project_id and filename for decrement and logging
        cur.execute(
            """
            SELECT pf.id, pf.filename, pf.room_id, p.user_id, p.id as project_id 
            FROM project_files pf
            JOIN projects p ON pf.project_id = p.id
            WHERE pf.id = %s
            """, 
            (file_id,)
        )
        row = cur.fetchone()
        if not row:
            return False
        
        project_id = row["project_id"]
        filename = row["filename"]
        user_id = row["user_id"]

        # delete file
        cur.execute("DELETE FROM project_files WHERE id = %s", (file_id,))

        # update project metadata
        cur.execute(
            "UPDATE projects SET files_count = GREATEST(files_count - 1, 0) WHERE id = %s",
            (project_id,),
        )

        # Log activity
        log_user_activity(user_id, 'file_deleted', f'Deleted file: {filename}')

        conn.commit()
        return True
    except Exception as e:
        print("delete_project_file error:", e)
        return False
    finally:
        conn.close()


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
    
    # Log login activity
    cur.execute("SELECT username FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()
    if user:
        log_user_activity(user_id, 'user_login', f'User {user["username"]} logged in')
    
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
# ACTIVITY TRACKING HELPERS
# ====================


def get_user_activity(user_id, limit=5):
    """Get recent user activity"""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute(
        """
        SELECT 
            description,
            activity_type,
            room_id,
            to_char(created_at, 'YYYY-MM-DD HH24:MI:SS') as timestamp
        FROM user_activity 
        WHERE user_id = %s 
        ORDER BY created_at DESC 
        LIMIT %s
    """,
        (user_id, limit),
    )
    
    activities = cur.fetchall()
    conn.close()
    
    # Format activities for display
    formatted_activities = []
    for activity in activities:
        desc = activity['description']
        activity_type = activity['activity_type']
        timestamp = activity['timestamp']
        
        # Add emojis based on activity type
        if activity_type == 'project_created':
            icon = "📁"
        elif activity_type == 'file_created':
            icon = "📄"
        elif activity_type == 'project_deleted':
            icon = "🗑"
        elif activity_type == 'file_deleted':
            icon = "🗑"
        elif activity_type == 'user_login':
            icon = "🔐"
        elif activity_type == 'room_joined':
            icon = "🚪"
        elif activity_type == 'code_edited':
            icon = "✏"
        else:
            icon = "📝"
            
        formatted_activities.append({
            'description': f"{icon} {desc}",
            'timestamp': timestamp,
            'type': activity_type
        })
    
    return formatted_activities


def log_user_activity(user_id, activity_type, description, room_id=None):
    """Log user activity"""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute(
        """
        INSERT INTO user_activity (user_id, activity_type, description, room_id)
        VALUES (%s, %s, %s, %s)
    """,
        (user_id, activity_type, description, room_id),
    )
    
    conn.commit()
    conn.close()


def log_room_activity(user_id, room_id, action_type, filename=None):
    """Log room-specific activities like joining, editing, etc."""
    actions = {
        'joined': 'Joined room',
        'left': 'Left room', 
        'edited': 'Edited code in',
        'saved': 'Saved file in'
    }
    
    action_text = actions.get(action_type, 'Accessed')
    description = f"{action_text} room"
    if filename:
        description = f"{action_text} {filename}"
    
    log_user_activity(user_id, 'room_activity', description, room_id)


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


# ====================
# FILE MANAGEMENT HELPERS
# ====================


def get_file_by_room_id(room_id):
    """Get file information by room_id"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT pf.*, p.name as project_name, u.username 
        FROM project_files pf
        JOIN projects p ON pf.project_id = p.id
        JOIN users u ON p.user_id = u.id
        WHERE pf.room_id = %s
    """,
        (room_id,),
    )
    row = cur.fetchone()
    conn.close()
    return row


def update_file_language(file_id, language):
    """Update the programming language of a file"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE project_files SET language = %s WHERE id = %s",
        (language, file_id),
    )
    conn.commit()
    conn.close()


def search_user_files(user_id, query):
    """Search files by name for a specific user"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT pf.*, p.name as project_name
        FROM project_files pf
        JOIN projects p ON pf.project_id = p.id
        WHERE p.user_id = %s AND pf.filename ILIKE %s
        ORDER BY pf.created_at DESC
    """,
        (user_id, f'%{query}%'),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def get_recent_files(user_id, limit=5):
    """Get recently created/accessed files for a user"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT pf.*, p.name as project_name
        FROM project_files pf
        JOIN projects p ON pf.project_id = p.id
        WHERE p.user_id = %s
        ORDER BY pf.created_at DESC
        LIMIT %s
    """,
        (user_id, limit),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


# ====================
# STATISTICS HELPERS
# ====================


def get_user_statistics(user_id):
    """Get comprehensive statistics for a user"""
    conn = get_connection()
    cur = conn.cursor()
    
    # Basic stats
    cur.execute(
        """
        SELECT 
            COUNT(DISTINCT p.id) as total_projects,
            COUNT(pf.id) as total_files,
            COALESCE(SUM(p.lines_of_code), 0) as total_lines,
            COUNT(DISTINCT ul.login_date) as total_login_days
        FROM users u
        LEFT JOIN projects p ON u.id = p.user_id
        LEFT JOIN project_files pf ON p.id = pf.project_id
        LEFT JOIN user_logins ul ON u.id = ul.user_id
        WHERE u.id = %s
        GROUP BY u.id
    """,
        (user_id,),
    )
    stats = cur.fetchone()
    
    # Language distribution
    cur.execute(
        """
        SELECT language, COUNT(*) as file_count
        FROM project_files pf
        JOIN projects p ON pf.project_id = p.id
        WHERE p.user_id = %s
        GROUP BY language
        ORDER BY file_count DESC
    """,
        (user_id,),
    )
    languages = cur.fetchall()
    
    # Recent activity count
    cur.execute(
        """
        SELECT COUNT(*) as recent_activities
        FROM user_activity
        WHERE user_id = %s AND created_at >= CURRENT_DATE - INTERVAL '7 days'
    """,
        (user_id,),
    )
    recent_activity = cur.fetchone()
    
    conn.close()
    
    return {
        'basic_stats': stats or {},
        'languages': languages or [],
        'recent_activities': recent_activity['recent_activities'] if recent_activity else 0
    }


def get_project_statistics(project_id):
    """Get detailed statistics for a specific project"""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute(
        """
        SELECT 
            p.*,
            COUNT(pf.id) as file_count,
            STRING_AGG(DISTINCT pf.language, ', ') as languages_used,
            MAX(pf.created_at) as last_file_created
        FROM projects p
        LEFT JOIN project_files pf ON p.id = pf.project_id
        WHERE p.id = %s
        GROUP BY p.id
    """,
        (project_id,),
    )
    
    stats = cur.fetchone()
    conn.close()
    return stats