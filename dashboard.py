import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from groq import Groq
from dotenv import load_dotenv
import os
import uuid
import random
import urllib.parse  # for encoding filenames in URLs
import traceback

try:
    from db import (
        init_db,
        get_dashboard_stats,
        get_user_projects,
        get_project_files,
        create_project,
        create_project_file,
        get_current_streak,
        delete_project,
        delete_project_file,
        get_recent_files,
    )
    DB_AVAILABLE = True
except ImportError as e:
    st.error(f"Database module import error: {e}")
    DB_AVAILABLE = False
    # Create dummy functions to prevent further errors
    def init_db(): pass
    def get_dashboard_stats(user_id): return {"total_projects": 0, "total_lines": 0, "total_files": 0}
    def get_user_projects(user_id): return []
    def get_project_files(project_id): return []
    def create_project(user_id, name): return True
    def create_project_file(project_id, filename, language): return True
    def get_current_streak(user_id): return 0
    def delete_project(project_id): return True
    def delete_project_file(file_id): return True
    def get_recent_files(user_id, limit=5): return []

# ---------- INIT ----------
load_dotenv()

try:
    init_db()
except Exception as e:
    st.error(f"Database initialization error: {e}")

# Local editor frontend (port 5000 for local)
EDITOR_FRONTEND_URL = os.getenv("EDITOR_FRONTEND_URL", "https://codeverseai-editor.vercel.app")

# Updated Coding Tips with better, shorter shortcuts & tricks
CODING_TIPS = [
    {
        "title": "🚀 VS Code Speedrun",
        "desc": "Ctrl+P: file search • Ctrl+Shift+O: go to symbol • Alt+Click: multi-cursor • Ctrl+B: toggle sidebar"
    },
    {
        "title": "🧠 Debug Like a Pro",
        "desc": "Log with context (console.log({ user, state })) instead of random prints • In Python, use logging.debug/info/error."
    },
    {
        "title": "⚡ Git Lifesavers",
        "desc": "git status -sb for clean view • git diff --staged before commit • git restore . to discard local changes."
    },
    {
        "title": "🎨 CSS Layout Tricks",
        "desc": "Use flex + gap instead of margins • minmax() with grid • clamp() for font sizes • aspect-ratio for media."
    },
    {
        "title": "🐍 Python One-Liners",
        "desc": "any()/all() for checks • list comprehensions for filtering • enumerate(list, 1) for 1-based index."
    },
    {
        "title": "🌐 Modern JS Essentials",
        "desc": "?? for nullish, not falsy • ?. for safe deep access • Array.some()/every() instead of loops."
    },
    {
        "title": "📱 Responsive Mindset",
        "desc": "Start mobile-first • Use rem for fonts • Test in devtools • Respect prefers-reduced-motion."
    },
    {
        "title": "🔒 Security First",
        "desc": "Always validate on server • Use parameterized queries • Never commit secrets • Use HTTPS by default."
    },
    {
        "title": "🚦 Frontend Performance",
        "desc": "Lazy-load heavy components • Debounce search inputs • Use SVG icons • Cache common data."
    },
    {
        "title": "🧪 Testing Mindset",
        "desc": "Test bug cases first • Cover edge values (0, 1, max) • Name tests like user stories."
    },
    {
        "title": "📊 Database Smart Moves",
        "desc": "Index WHERE/JOIN columns • Avoid SELECT * • Use LIMIT for lists • Use EXPLAIN on slow queries."
    },
    {
        "title": "🧩 Code Readability Wins",
        "desc": "Small functions > giant ones • Intent-based names • Early returns to reduce nesting."
    },
]


def dashboard():
    # --------- PAGE CONFIG ----------
    st.set_page_config(page_title="CodeVerse AI", page_icon="🤖", layout="wide")

    # --------- CHECK IF THIS IS CHAT POPUP MODE ----------
    params = st.query_params
    is_chat_mode = params.get("chat", ["0"])[0] == "1"

    if is_chat_mode:
        # --- Chat mode DOES NOT require login ---

        # Load Groq just for chat mode
        try:
            groq_api_key = os.getenv("GROQ_API_KEY")
            if not groq_api_key:
                st.warning("GROQ_API_KEY not found in environment variables")
                client = None
            else:
                client = Groq(api_key=groq_api_key)
        except Exception as e:
            st.error(f"Groq client initialization error: {e}")
            client = None

        # Chat memory
        if "chatbot_messages" not in st.session_state:
            st.session_state.chatbot_messages = [
                {
                    "role": "assistant",
                    "content": "Welcome to CodeVerse AI. How can I help you today? 😊",
                }
            ]

        # Hide Streamlit chrome
        st.markdown(
            """
            <style>
            header {display: none !important;}
            [data-testid="stSidebar"] {display: none !important;}
            [data-testid="stToolbar"] {display: none !important;}
            .block-container {padding-top: 0.4rem !important;}
            .stChatMessageAvatar {display: none !important;}
            </style>
            """,
            unsafe_allow_html=True,
        )

        # Show chat history
        for msg in st.session_state.chatbot_messages:
            st.chat_message(msg["role"]).write(msg["content"])

        # Chat input
        user_input = st.chat_input("Type your message...")

        if user_input:
            st.chat_message("user").write(user_input)
            st.session_state.chatbot_messages.append(
                {"role": "user", "content": user_input}
            )

            if client:
                typing_msg = st.chat_message("assistant")
                typing_placeholder = typing_msg.empty()
                typing_placeholder.write(" typing...")

                try:
                    response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {
                                "role": "system",
                                "content": "You are a helpful and friendly AI assistant.",
                            }
                        ]
                        + st.session_state.chatbot_messages,
                    )
                    reply = response.choices[0].message.content
                    typing_placeholder.empty()
                    st.chat_message("assistant").write(reply)
                    st.session_state.chatbot_messages.append(
                        {"role": "assistant", "content": reply}
                    )
                except Exception as e:
                    typing_placeholder.empty()
                    error_msg = f"Sorry, I encountered an error: {str(e)}"
                    st.chat_message("assistant").write(error_msg)
                    st.session_state.chatbot_messages.append(
                        {"role": "assistant", "content": error_msg}
                    )
            else:
                st.chat_message("assistant").write(
                    "Chat functionality is currently unavailable. Please check your API configuration."
                )

        if st.button(" Clear Conversation"):
            st.session_state.chatbot_messages = [
                {
                    "role": "assistant",
                    "content": "Welcome to CodeVerse AI.  How can I help you today? 😊",
                }
            ]
            st.rerun()

        return  # ✅ Important: end function here for chat mode

    # --------- AUTH GUARD FOR NORMAL DASHBOARD ----------
    user_info = st.session_state.get("user")
    if not user_info:
        st.error("You must be logged in to view the dashboard.")
        st.stop()

    user_id = user_info["id"]
    username = user_info["username"]

    # (rest of your normal dashboard code continues here…)



    # ================= NORMAL DASHBOARD =================

    # Show database status warning
    if not DB_AVAILABLE:
        st.warning("⚠ Database functionality is limited. Some features may not work properly.")

    # --------- DATA FOR THIS USER ----------
    try:
        stats = get_dashboard_stats(user_id) or {
            "total_projects": 0,
            "total_lines": 0,
            "total_files": 0,
        }
        projects = get_user_projects(user_id) or []
        current_streak = get_current_streak(user_id)
        recent_files = get_recent_files(user_id, limit=5)
    except Exception as e:
        st.error(f"Error loading user data: {e}")
        stats = {"total_projects": 0, "total_lines": 0, "total_files": 0}
        projects = []
        current_streak = 0
        recent_files = []

    total_projects = stats.get("total_projects", 0)
    total_lines = stats.get("total_lines", 0)
    total_files = stats.get("total_files", 0)

    avg_files = float(total_files) / total_projects if total_projects else 0.0

    # which project card is currently in "add file" mode
    if "show_add_file_for" not in st.session_state:
        st.session_state["show_add_file_for"] = None

    # Get random coding tips
    if "coding_tips" not in st.session_state:
        st.session_state.coding_tips = random.sample(CODING_TIPS, 4)

    # --------- ENHANCED CSS ----------
    st.markdown(
        """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    
    .stApp {
        font-family: 'Inter', sans-serif;
        background: #0a0f1c;
    }
    
    [data-testid="stSidebar"] {
        background-color: #0f172a !important;
        color: white;
        padding-top: 20px;
        border-right: 1px solid #334155;
        overflow: hidden !important;
    }
    
    [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: white;
    }

    .main {
        background-color: #0a0f1c;
    }
    
    .block-container {
        background: #0a0f1c;
        padding: 2rem;
    }

    h1, h2, h3 {
        color: #f8fafc !important;
    }

    /* Original Metric Cards with Hover */
    .metric-card {
        background: #1e293b;
        border: 1px solid #334155;
        padding: 24px;
        border-radius: 16px;
        text-align: center;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        transition: all 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        border-color: #8b5cf6;
    }
    .metric-title {
        font-size: 15px;
        color: #cbd5e1;
        font-weight: 600;
    }
    .metric-value {
        margin-top: 4px;
        font-size: 30px;
        font-weight: 800;
        background: linear-gradient(135deg, #8b5cf6 0%, #3b82f6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* Enhanced Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #8b5cf6 0%, #3b82f6 100%);
        color: white;
        border-radius: 12px;
        padding: 10px 18px;
        border: none;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(139, 92, 246, 0.3);
        font-size: 14px;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(139, 92, 246, 0.5);
    }

    /* Enhanced Navigation */
    .nav-btn {
        display: block;
        width: 100%;
        background-color: transparent;
        color: #cbd5e1;
        text-align: left;
        padding: 14px 18px;
        border: none;
        border-radius: 12px;
        font-size: 15px;
        margin-bottom: 8px;
        cursor: pointer;
        transition: all 0.3s ease;
        font-weight: 500;
    }
    .nav-btn:hover {
        background: linear-gradient(135deg, #8b5cf6 0%, #3b82f6 100%);
        color: white;
        transform: translateX(8px);
    }
    .nav-btn.active {
        background: linear-gradient(135deg, #8b5cf6 0%, #3b82f6 100%);
        color: white;
        font-weight: 600;
        box-shadow: 0 4px 15px rgba(139, 92, 246, 0.3);
    }

    /* Enhanced Project Cards */
    .project-card {
        background: linear-gradient(135deg, #020617 0%, #0f172a 100%);
        border-radius: 16px;
        border: 1px solid #1f2937;
        padding: 20px;
        box-shadow: 0 8px 32px rgba(15,23,42,0.75);
        margin-bottom: 20px;
        transition: all 0.3s ease;
        position: relative;
    }
    .project-card:hover {
        transform: translateY(-3px);
        border-color: #8b5cf6;
        box-shadow: 0 12px 40px rgba(139, 92, 246, 0.2);
    }
    .project-card-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 8px;
    }
    .project-title-left {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .project-title-left span.name {
        font-size: 18px;
        font-weight: 700;
        color: #f1f5f9;
    }
    .project-meta {
        font-size: 12px;
        color: #94a3b8;
        background: rgba(30, 41, 59, 0.5);
        padding: 4px 10px;
        border-radius: 20px;
    }
    .project-actions {
        display: flex;
        gap: 6px;
        align-items: center;
        justify-content: flex-end;
    }

    /* Delete Buttons */
    .delete-btn {
        background: transparent !important;
        border: 1px solid #ef4444 !important;
        border-radius: 8px !important;
        padding: 6px 12px !important;
        color: #ef4444 !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
        font-size: 12px !important;
        min-height: unset !important;
        height: 32px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 4px !important;
    }
    .delete-btn:hover {
        background: #ef4444 !important;
        color: white !important;
        transform: scale(1.05) !important;
    }

    .compact-delete-btn {
        background: transparent !important;
        border: 1px solid #ef4444 !important;
        border-radius: 6px !important;
        padding: 2px 6px !important;
        color: #ef4444 !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
        font-size: 10px !important;
        min-height: unset !important;
        height: 24px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    .compact-delete-btn:hover {
        background: #ef4444 !important;
        color: white !important;
        transform: scale(1.1) !important;
    }

    .compact-add-btn {
        background: transparent !important;
        border: 1px solid #10b981 !important;
        border-radius: 6px !important;
        padding: 2px 6px !important;
        color: #10b981 !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
        font-size: 10px !important;
        min-height: unset !important;
        height: 24px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    .compact-add-btn:hover {
        background: #10b981 !important;
        color: white !important;
        transform: scale(1.1) !important;
    }

    /* Enhanced File Rows (Projects) */
    .project-files-wrapper {
        margin-top: 6px;
        border-top: 1px solid rgba(31,41,55,0.8);
        padding-top: 4px;
    }
    .project-file-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 8px 4px;
        border-radius: 8px;
        transition: all 0.2s ease;
    }
    .project-file-row:hover {
        background: rgba(30, 41, 59, 0.5);
        transform: translateY(-1px);
    }
    .file-left {
        display: flex;
        align-items: center;
        gap: 10px;
        flex: 1;
    }
    .file-name {
        color: #e5e7eb;
        font-weight: 600;
        font-size: 14px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .file-lang {
        color: #9ca3af;
        font-size: 11px;
        background: rgba(30, 41, 59, 0.7);
        padding: 2px 8px;
        border-radius: 12px;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    .file-actions {
        display: flex;
        gap: 8px;
        align-items: center;
        margin-left: 10px;
    }
    .file-open-btn {
        font-size: 12px;
        padding: 6px 14px;
        border-radius: 20px;
        border: 1px solid #4b5563;
        color: #e5e7eb;
        text-decoration: none;
        transition: all 0.2s ease;
        text-decoration: none;
    }
    .file-open-btn:hover {
        background: #8b5cf6;
        border-color: #8b5cf6;
        color: #ffffff;
        transform: translateY(-1px);
        text-decoration: none;
    }

    /* Enhanced AI Actions - Border around entire section */
    .ai-actions-container {
        background: linear-gradient(135deg, #020617 0%, #0f172a 100%);
        border-radius: 20px;
        border: 2px solid #334155;
        padding: 25px;
        margin: 40px 0;
        position: relative;
        overflow: hidden;
    }
    .ai-actions-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 20px;
    }
    .ai-actions-icon {
        font-size: 28px;
        background: linear-gradient(135deg, #8b5cf6 0%, #3b82f6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .ai-actions-title {
        font-size: 24px;
        font-weight: 700;
        color: #f1f5f9;
        margin: 0;
    }
    .ai-actions-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 15px;
    }
    .ai-action-card {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        transition: all 0.3s ease;
        border: 1px solid #475569;
        text-decoration: none !important;
        color: inherit;
    }
    .ai-action-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(139, 92, 246, 0.3);
        border-color: #8b5cf6;
        text-decoration: none !important;
    }
    .ai-action-icon {
        font-size: 28px;
        margin-bottom: 10px;
        text-decoration: none !important;
    }
    .ai-action-title {
        font-size: 20px;
        font-weight: 600;
        color: #e2e8f0;
        text-decoration: none !important;
    }

    /* Recent Files Cards */
    .activity-card {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        border-radius: 12px;
        padding: 18px;
        border: 1px solid #475569;
        transition: all 0.3s ease;
        margin-bottom: 12px;
    }
    .activity-card:hover {
        transform: translateY(-2px);
        border-color: #10b981;
    }

    /* Coding Tips Section */
    .tips-section {
        background: linear-gradient(135deg, #020617 0%, #0f172a 100%);
        border-radius: 20px;
        border: 2px solid #334155;
        padding: 25px;
        margin: 30px 0;
        box-shadow: 0 8px 32px rgba(15,23,42,0.7);
        position: relative;
    }
    .tips-title {
        font-size: 30px;
        font-weight: 700;
        color: #f1f5f9;
        margin-bottom: 20px;
    }
    .tips-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 16px;
    }
    .tip-card {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        border-radius: 12px;
        padding: 18px;
        border: 1px solid #475569;
        transition: all 0.3s ease;
    }
    .tip-card:hover {
        transform: translateY(-2px);
        border-color: #8b5cf6;
    }
    .tip-card-title {
        font-size: 16px;
        font-weight: 600;
        color: #e2e8f0;
        margin-bottom: 8px;
    }
    .tip-card-desc {
        font-size: 14px;
        color: #94a3b8;
        line-height: 1.5;
    }

    /* Delete Confirmation */
    .delete-confirm {
        background: rgba(239, 68, 68, 0.1);
        border: 1px solid #ef4444;
        border-radius: 12px;
        padding: 16px;
        margin: 12px 0;
    }

    /* Fixed Chat Button */
    .fixed-chat {
        position: fixed !important;
        bottom: 25px !important;
        right: 25px !important;
        z-index: 999999 !important;
    }

    /* No Activity Message */
    .no-activity {
        text-align: center;
        padding: 40px 20px;
        color: #94a3b8;
    }
    .no-activity-icon {
        font-size: 48px;
        margin-bottom: 16px;
        opacity: 0.5;
    }

    /* Project Files Section */
    .project-files-section {
        background: linear-gradient(135deg, #020617 0%, #0f172a 100%);
        border-radius: 20px;
        border: 2px solid #334155;
        padding: 25px;
        margin: 30px 0;
    }
    .project-files-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 20px;
    }
    .project-files-title {
        font-size: 22px;
        font-weight: 700;
        color: #f1f5f9;
        margin: 0;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # --------- SIDEBAR ----------
    with st.sidebar:
        st.markdown(
            """
            <div style="text-align: center; margin-bottom: 32px;">
                <div style="font-size: 32px; font-weight: 800; background: linear-gradient(135deg, #61dafb, #bd93f9); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 4px;">
                    CodeVerse AI
                </div>
                <div style="font-size: 14px; color: #bd93f9; font-weight: 500; letter-spacing: 0.5px;">
                    Collaborative Code Editor
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            "<hr style='border:1px solid #334155; margin: 20px 0;'>",
            unsafe_allow_html=True,
        )

        st.markdown(
            "<button class='nav-btn active'>🏠 Dashboard</button>",
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
<a href="{EDITOR_FRONTEND_URL}/" target="_blank" style="text-decoration: none;">
    <button class='nav-btn'>👨‍💻 Code Editor</button>
</a>
""",
            unsafe_allow_html=True,
        )

        st.markdown(
            "<button class='nav-btn'>⚙ Settings</button>", unsafe_allow_html=True
        )

        st.markdown(
            "<hr style='border:1px solid #334155; margin: 20px 0;'>",
            unsafe_allow_html=True,
        )

        # Quick Stats in Sidebar
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); padding: 16px; border-radius: 12px; border: 1px solid #334155; margin-bottom: 20px;">
                <div style="font-size: 14px; color: #94a3b8; margin-bottom: 8px;">Quick Stats</div>
                <div style="display: flex; justify-content: space-between; font-size: 12px;">
                    <span>Projects: <strong style="color: #8b5cf6;">{total_projects}</strong></span>
                    <span>Files: <strong style="color: #8b5cf6;">{total_files}</strong></span>
                    <span>Streak: <strong style="color: #8b5cf6;">{current_streak}🔥</strong></span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Logout
        if st.button("🚪 Logout", key="logout_sidebar_btn", use_container_width=True):
            for k in ["user", "authenticated", "auth_mode"]:
                st.session_state.pop(k, None)
            st.rerun()

    # --------- MAIN CONTENT ----------

    # Welcome Section
    st.markdown(f"# 👋 Welcome, {username}!")
    st.markdown(
        "<p style='color:#94a3b8;font-size:16px;margin-top:-8px;margin-bottom:30px;'>Ready to code something amazing today?</p>",
        unsafe_allow_html=True,
    )

    # Original Style Metrics with Hover
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(
            f'<div class="metric-card"><div class="metric-title">🧠 Total Projects</div><div class="metric-value">{total_projects}</div></div>',
            unsafe_allow_html=True,
        )
    with m2:
        st.markdown(
            f'<div class="metric-card"><div class="metric-title">🔥 Current Streak</div><div class="metric-value">{current_streak} Days</div></div>',
            unsafe_allow_html=True,
        )
    with m3:
        st.markdown(
            f'<div class="metric-card"><div class="metric-title">📁 Total Files</div><div class="metric-value">{total_files}</div></div>',
            unsafe_allow_html=True,
        )
    with m4:
        st.markdown(
            f'<div class="metric-card"><div class="metric-title">📊 Avg Files / Project</div><div class="metric-value">{avg_files:.1f}</div></div>',
            unsafe_allow_html=True,
        )

    # Enhanced Quick AI Actions with Border and Improved Layout
    def quick_room_link(action_slug: str) -> str:
        room_id = uuid.uuid4().hex
        # For ad-hoc rooms we don't have a filename yet, so no filename param here
        return f"{EDITOR_FRONTEND_URL}/editor/{room_id}?username={username}&from={action_slug}"

    ai_actions_html = f"""
    <div class="ai-actions-container">
        <div class="ai-actions-header">
            <div class="ai-actions-icon">⚡</div>
            <h3 class="ai-actions-title">Quick AI Actions</h3>
        </div>
        <div class="ai-actions-grid">
            <a class="ai-action-card" href="{quick_room_link('explain')}" target="_blank">
                <div class="ai-action-icon">🧠</div>
                <div class="ai-action-title">Explain Code</div>
            </a>
            <a class="ai-action-card" href="{quick_room_link('debug')}" target="_blank">
                <div class="ai-action-icon">🐞</div>
                <div class="ai-action-title">Debug Code</div>
            </a>
            <a class="ai-action-card" href="{quick_room_link('docs')}" target="_blank">
                <div class="ai-action-icon">📝</div>
                <div class="ai-action-title">Generate Docs</div>
            </a>
            <a class="ai-action-card" href="{quick_room_link('optimize')}" target="_blank">
                <div class="ai-action-icon">⚡</div>
                <div class="ai-action-title">Optimize Code</div>
            </a>
        </div>
    </div>
    """
    st.markdown(ai_actions_html, unsafe_allow_html=True)

    # --------- RECENT FILES SECTION (compact horizontal style) ----------
    st.markdown("<div class='tips-title'>🚀 Recent Files</div>", unsafe_allow_html=True,)
    if recent_files:
        for file in recent_files:
            filename = file["filename"]
            encoded_filename = urllib.parse.quote(filename)
            editor_url = (
                f"{EDITOR_FRONTEND_URL}/editor/{file['room_id']}"
                f"?username={username}&filename={encoded_filename}"
            )

            st.markdown(
                f"""
                <div class="activity-card" style="padding:14px;">
                    <div style="display:flex; align-items:center; justify-content:space-between; gap:10px;">
                        <div style="display:flex; align-items:center; gap:8px; font-weight:600; font-size:15px; color:#e2e8f0;">
                            📄 {filename}
                        </div>
                        <div style="font-size:13px; color:#94a3b8; flex:1; text-align:center;">
                            {file.get('project_name', 'Unknown')} • {file.get('language', 'code').upper()}
                        </div>
                        <a href="{editor_url}" target="_blank" 
                           style="font-size:12px; padding:6px 14px; border-radius:20px; border:1px solid #4b5563; color:#e5e7eb; text-decoration:none; transition:0.2s;">
                            Open
                        </a>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            """
            <div class="no-activity">
                <div class="no-activity-icon">📁</div>
                <div>No recent files</div>
                <div style="font-size: 12px; margin-top: 8px;">Create your first file to get started!</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # --------- PROJECTS SECTION ----------
    st.markdown("<div class='tips-title'>📂 Your Projects</div>",unsafe_allow_html=True,)

    # Create Project Form
    with st.form("create_project_form", clear_on_submit=True):
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            new_project_name = st.text_input(
                "Project name",
                placeholder="My awesome project",
                label_visibility="collapsed",
            )
        with col2:
            project_language = st.selectbox(
                "Language",
                ["python", "javascript", "java", "cpp", "html"],
                label_visibility="collapsed",
            )
        with col3:
            create_project_btn = st.form_submit_button(
                "🚀 Create Project", use_container_width=True
            )

        if create_project_btn:
            if not new_project_name.strip():
                st.warning("Please enter a project name.")
            else:
                try:
                    create_project(user_id, new_project_name.strip())
                    st.success(f"Project *{new_project_name}* created.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error creating project: {e}")

    st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)

    if not projects:
        st.info("🌟 You don't have any projects yet. Create your first project above to get started!")
    else:
        # Enhanced Projects list with clean vertical sequence
        for project in projects:
            try:
                files = get_project_files(project["id"]) or []
            except Exception as e:
                st.error(f"Error loading files for project {project['name']}: {e}")
                files = []

            # Project header with name and action buttons
            with st.container():
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    st.markdown(f"### 📁 {project['name']}")
                    st.markdown(f"<div style='color: #94a3b8; font-size: 14px; margin-top: -10px; margin-bottom: 10px;'>{len(files)} file(s)</div>", 
                               unsafe_allow_html=True)
                
                with col2:
                    # Action buttons container
                    btn_col1, btn_col2 = st.columns(2)
                    with btn_col1:
                        if st.button("➕ Add File", 
                                    key=f"add_{project['id']}",
                                    use_container_width=True,
                                    help="Add a new file to this project"):
                            st.session_state["show_add_file_for"] = project["id"]
                            st.rerun()
                    
                    with btn_col2:
                        if st.button("🗑", 
                                    key=f"delete_{project['id']}",
                                    use_container_width=True,
                                    help="Delete this project"):
                            if st.session_state.get(f"confirm_delete_{project['id']}"):
                                try:
                                    if delete_project(project["id"]):
                                        st.success(f"Project '{project['name']}' deleted successfully!")
                                        st.rerun()
                                    else:
                                        st.error("Failed to delete project.")
                                except Exception as e:
                                    st.error(f"Error deleting project: {e}")
                            else:
                                st.session_state[f"confirm_delete_{project['id']}"] = True
                                st.warning(f"Click again to confirm deletion of '{project['name']}'")
            
            # Files list in vertical sequence
            if files:
                st.markdown("<div style='margin-left: 20px;'>", unsafe_allow_html=True)
                
                for f in files:
                    file_lang = f.get("language", "code")
                    filename = f["filename"]
                    encoded_filename = urllib.parse.quote(filename)
                    editor_url = (
                        f"{EDITOR_FRONTEND_URL}/editor/{f['room_id']}"
                        f"?username={username}&filename={encoded_filename}"
                    )
                    
                    # File row with actions
                    with st.container():
                        file_col1, file_col2, file_col3 = st.columns([3, 1, 1])
                        
                        with file_col1:
                            st.markdown(f"📄 {filename}")
                            st.markdown(f"<div style='color: #94a3b8; font-size: 12px; margin-top: -8px;'>Language: {file_lang.upper()}</div>", 
                                       unsafe_allow_html=True)
                        
                        with file_col2:
                            st.markdown(
                                f'<a href="{editor_url}" target="_blank" style="display: inline-block; width: 100%; text-align: center; padding: 6px 12px; border-radius: 6px; border: 1px solid #4b5563; color: #e5e7eb; text-decoration: none; transition: 0.2s; font-size: 12px;">Open</a>',
                                unsafe_allow_html=True
                            )
                        
                        with file_col3:
                            if st.button("🗑", 
                                        key=f"delfile_{f['id']}",
                                        help=f"Delete {filename}",
                                        use_container_width=True):
                                if st.session_state.get(f"confirm_delfile_{f['id']}"):
                                    try:
                                        if delete_project_file(f["id"]):
                                            st.success(f"File '{filename}' deleted successfully!")
                                            st.rerun()
                                        else:
                                            st.error("Failed to delete file.")
                                    except Exception as e:
                                        st.error(f"Error deleting file: {e}")
                                else:
                                    st.session_state[f"confirm_delfile_{f['id']}"] = True
                                    st.warning(f"Click again to confirm deletion of '{filename}'")
                    
                    # Small spacer between files
                    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)

            # Add file form if this project is active
            if st.session_state.get("show_add_file_for") == project["id"]:
                st.markdown("<div style='margin-left: 20px; margin-top: 15px;'>", unsafe_allow_html=True)
                st.markdown("*Add new file*")
                with st.form(f"add_file_form_{project['id']}"):
                    form_col1, form_col2, form_col3 = st.columns([3, 2, 1])
                    with form_col1:
                        filename = st.text_input(
                            "File name",
                            key=f"filename_{project['id']}",
                            placeholder="main.py / index.js ...",
                        )
                    with form_col2:
                        language = st.selectbox(
                            "Language",
                            ["javascript", "python", "cpp", "java"],
                            key=f"lang_{project['id']}",
                        )
                    with form_col3:
                        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                        submit_file = st.form_submit_button("Create", use_container_width=True)
                    
                    if submit_file:
                        if not filename.strip():
                            st.warning("Please enter a file name.")
                        else:
                            try:
                                create_project_file(
                                    project["id"], filename.strip(), language
                                )
                                st.success(f"File *{filename}* created.")
                                st.session_state["show_add_file_for"] = None
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error creating file: {e}")
                
                st.markdown("</div>", unsafe_allow_html=True)
            
            # Divider between projects
            st.markdown("---")

    # Coding Tips Section with working Refresh Button

    header_col1, header_col2 = st.columns([5, 1])
    with header_col1:
        st.markdown(
            "<div class='tips-title'>💡 Pro Coding Tips & Shortcuts</div>",
            unsafe_allow_html=True,
        )
    with header_col2:
        if st.button("🔄 Refresh tips", key="refresh_tips_btn"):
            st.session_state.coding_tips = random.sample(CODING_TIPS, 4)
            st.rerun()

    tips = st.session_state.coding_tips
    tips_html = f"""
        <div class="tips-grid">
            <div class="tip-card">
                <div class="tip-card-title">{tips[0]['title']}</div>
                <div class="tip-card-desc">{tips[0]['desc']}</div>
            </div>
            <div class="tip-card">
                <div class="tip-card-title">{tips[1]['title']}</div>
                <div class="tip-card-desc">{tips[1]['desc']}</div>
            </div>
            <div class="tip-card">
                <div class="tip-card-title">{tips[2]['title']}</div>
                <div class="tip-card-desc">{tips[2]['desc']}</div>
            </div>
            <div class="tip-card">
                <div class="tip-card-title">{tips[3]['title']}</div>
                <div class="tip-card-desc">{tips[3]['desc']}</div>
            </div>
        </div>
    """
    st.markdown(tips_html, unsafe_allow_html=True)

    # Fixed Floating Chat Button (always visible)
    floating_chat = """
<style>
/* Floating button */
#ai_chat_btn {
    position: fixed;
    bottom: 8px;
    right: 25px;
    width: 65px;
    height: 65px;
    border-radius: 50%;
    background: #007bff;
    color: white;
    border: none;
    font-size: 30px;
    cursor: pointer;
    box-shadow: 0 6px 18px rgba(0,0,0,0.4);
    transition: 0.25s;
    z-index: 999999;
}
#ai_chat_btn:hover {
    background: #0056b3;
    transform: scale(1.10);
}

/* Chat popup */
#ai_chat_box {
    position: fixed;
    bottom: 0 px;
    right: 25px;
    width: 380px;
    height: 460px;
    background: #020617;
    border-radius: 14px;
    box-shadow: 0 12px 28px rgba(0,0,0,0.45);
    overflow: hidden;
    z-index: 999999999 !important; 
    display: none;
    transform: translateY(40px);
    opacity: 0;
    transition: all .35s ease;
}
#ai_chat_box.open {
    display: block;
    transform: translateY(0px);
    opacity: 1;
}

/* Header */
#ai_chat_header {
    background: #007bff;
    color: white;
    padding: 10px 14px;
    font-size: 18px;
    font-weight: 600;
    display: flex;
    justify-content: space-between;
    align-items: center;
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 50px;
}
#ai_chat_close {
    cursor: pointer;
    font-size: 22px;
    font-weight: 900;
}
#ai_chat_close:hover {
    color: #ffe5e5;
}

#ai_chat_iframe {
    margin-top: 70px;
}
</style>

<button id="ai_chat_btn">💬</button>

<div id="ai_chat_box">
    <div id="ai_chat_header">
        ChatMate
        <span id="ai_chat_close">✖</span>
    </div>
    <iframe id="ai_chat_iframe" src="?chat=1&page=dashboard"
        width="100%" height="410px" style="border:none;background:#020617;">
    </iframe>
</div>

<script>
const btn = document.getElementById("ai_chat_btn");
const box = document.getElementById("ai_chat_box");
const closeBtn = document.getElementById("ai_chat_close");
btn.onclick = () => box.classList.add("open");
closeBtn.onclick = () => box.classList.remove("open");
</script>
"""

    components.html(
    f"""
    <div style='height:0;width:0;'>
    {floating_chat}
    </div>
    """,
    height=0,
    width=0,
    scrolling=False,
)
if __name__ == "__main__":
    dashboard()