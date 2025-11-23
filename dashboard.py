import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from groq import Groq
from dotenv import load_dotenv
import os
import uuid
import random

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
)

# ---------- INIT ----------
load_dotenv()
init_db()

# Local editor frontend (port 5000 for local)
EDITOR_FRONTEND_URL = os.getenv("EDITOR_FRONTEND_URL", "https://codeverseai-editor.vercel.app")

# Add this after your imports, before the dashboard() function
CODING_TIPS = [
    {
        "title": "Write Readable Code",
        "desc": "Always write code as if the next person to maintain it is a violent psychopath who knows where you live."
    },
    {
        "title": "Use Version Control",
        "desc": "Commit early and often. Small, frequent commits make it easier to track changes and revert if needed."
    },
    {
        "title": "Test Your Code",
        "desc": "Write tests before you write the code (TDD). It helps clarify requirements and prevents bugs."
    },
    {
        "title": "Keep Functions Small",
        "desc": "Functions should do one thing and do it well. If it's doing multiple things, split it up."
    },
    {
        "title": "Use Meaningful Names",
        "desc": "Variable and function names should reveal intent. Avoid abbreviations and single-letter names."
    },
    {
        "title": "Document Your Code",
        "desc": "Write comments that explain why, not what. The code should be self-explanatory for the what."
    },
    {
        "title": "Refactor Regularly",
        "desc": "Don't let technical debt accumulate. Refactor code as you work on it."
    },
    {
        "title": "Learn Debugging Tools",
        "desc": "Master your IDE's debugging features. It will save you hours of debugging time."
    },
    {
        "title": "Code Review",
        "desc": "Always have someone else review your code. Fresh eyes catch things you might miss."
    },
    {
        "title": "Stay Updated",
        "desc": "Keep learning new technologies and best practices, but don't chase every new trend."
    },
    {
        "title": "Error Handling",
        "desc": "Always handle errors gracefully. Don't let your application crash unexpectedly."
    },
    {
        "title": "Performance Matters",
        "desc": "Write efficient code, but don't optimize prematurely. Focus on readability first."
    }
]

def dashboard():
    # --------- PAGE CONFIG ----------
    st.set_page_config(page_title="CodeVerse AI", page_icon="🤖", layout="wide")

    # --------- AUTH GUARD ----------
    user_info = st.session_state.get("user")
    if not user_info:
        st.error("You must be logged in to view the dashboard.")
        st.stop()

    user_id = user_info["id"]
    username = user_info["username"]

    # --------- LOAD GROQ & CHAT MEMORY ----------
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    if "chatbot_messages" not in st.session_state:
        st.session_state.chatbot_messages = [
            {
                "role": "assistant",
                "content": "Welcome to CodeVerse AI. How can I help you today? 😊",
            }
        ]

    # --------- CHECK IF THIS IS CHAT POPUP MODE ----------
    params = st.query_params
    is_chat_mode = params.get("chat", "0") == "1"

    if is_chat_mode:
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

            # Typing animation
            typing_msg = st.chat_message("assistant")
            typing_placeholder = typing_msg.empty()
            typing_placeholder.write(" typing...")

            # Call Groq model
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

            # Replace typing animation
            typing_placeholder.empty()
            st.chat_message("assistant").write(reply)
            st.session_state.chatbot_messages.append(
                {"role": "assistant", "content": reply}
            )

        # Clear chat
        if st.button(" Clear Conversation"):
            st.session_state.chatbot_messages = [
                {
                    "role": "assistant",
                    "content": "Welcome to CodeVerse AI.  How can I help you today? 😊",
                }
            ]
            st.rerun()

        st.stop()

    # ================= NORMAL DASHBOARD =================

    # --------- DATA FOR THIS USER ----------
    stats = get_dashboard_stats(user_id) or {
        "total_projects": 0,
        "total_lines": 0,
        "total_files": 0,
    }
    projects = get_user_projects(user_id) or []
    current_streak = get_current_streak(user_id)

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
        padding: 12px 20px;
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
        margin-bottom: 12px;
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
        gap: 8px;
        align-items: center;
    }

    /* Compact Delete Buttons */
    .compact-delete-btn {
        background: transparent !important;
        border: 1px solid #ef4444 !important;
        border-radius: 6px !important;
        padding: 2px 2px !important;
        color: #ef4444 !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
        font-size: 10px !important;
        min-height: unset !important;
        height: 24px !important;
        width: 5px !important;
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
        padding: 2px 2px !important;
        color: #10b981 !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
        font-size: 10px !important;
        min-height: unset !important;
        height: 24px !important;
        width: 5px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    .compact-add-btn:hover {
        background: #10b981 !important;
        color: white !important;
        transform: scale(1.1) !important;
    }

    /* Enhanced File Rows */
    .file-row {
        font-size: 14px;
        padding: 12px 0;
        border-top: 1px solid rgba(31,41,55,0.75);
        display: flex;
        align-items: center;
        justify-content: space-between;
        transition: all 0.2s ease;
    }
    .file-row:hover {
        background: rgba(30, 41, 59, 0.3);
        border-radius: 8px;
        padding: 12px;
        margin: 0 -8px;
    }
    .file-left {
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .file-name {
        color: #e5e7eb;
        font-weight: 600;
    }
    .file-lang {
        color: #9ca3af;
        font-size: 11px;
        background: rgba(30, 41, 59, 0.5);
        padding: 2px 8px;
        border-radius: 12px;
    }
    .file-actions {
        display: flex;
        gap: 8px;
        align-items: center;
    }
    .file-open-btn {
        font-size: 12px;
        padding: 6px 14px;
        border-radius: 20px;
        border: 1px solid #4b5563;
        color: #e5e7eb;
        text-decoration: none;
        transition: all 0.2s ease;
    }
    .file-open-btn:hover {
        background: #8b5cf6;
        border-color: #8b5cf6;
        color: #ffffff;
        transform: translateY(-1px);
    }

    /* Enhanced AI Actions - Border around entire section */
    .ai-actions-container {
        background: linear-gradient(135deg, #020617 0%, #0f172a 100%);
        border-radius: 20px;
        border: 2px solid #334155;
        padding: 25px;
        margin: 20px 0;
        position: relative;
        overflow: hidden;
    }
    .ai-actions-container::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(135deg, #020617 0%, #0f172a 100%);
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

    /* Remove underlines from all links in AI actions */
    .ai-action-card, .ai-action-card:hover, .ai-action-card:visited {
        text-decoration: none !important;
    }

    /* Coding Tips Section with Refresh Button */
    .tips-section {
        background: linear-gradient(135deg, #020617 0%, #0f172a 100%);
        border-radius: 20px;
        border: 2px solid #334155;
        padding: 24px;
        margin: 20px 0;
        box-shadow: 0 8px 32px rgba(15,23,42,0.7);
        position: relative;
    }
    .tips-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
    }
    .tips-title {
        font-size: 20px;
        font-weight: 700;
        color: #f1f5f9;
        margin: 0;
    }
    .refresh-tips-btn {
        background: transparent;
        border: 1px solid #8b5cf6;
        border-radius: 8px;
        padding: 8px 12px;
        color: #8b5cf6;
        cursor: pointer;
        transition: all 0.3s ease;
        font-size: 14px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .refresh-tips-btn:hover {
        background: #8b5cf6;
        color: white;
        transform: rotate(15deg);
    }
    .tips-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 16px;
    }
    .tip-card {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        border-radius: 12px;
        padding: 20px;
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
        line-height: 1.4;
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

    # Enhanced Projects Section
    st.markdown("### 📁 Your Projects")
    
    # Create Project Form
    with st.form("create_project_form", clear_on_submit=True):
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            new_project_name = st.text_input(
                "Project name", 
                placeholder="My awesome project",
                label_visibility="collapsed"
            )
        with col2:
            project_language = st.selectbox(
                "Language",
                ["python", "javascript", "java", "cpp", "html"],
                label_visibility="collapsed"
            )
        with col3:
            create_project_btn = st.form_submit_button(
                "🚀 Create Project",
                use_container_width=True
            )
        
        if create_project_btn:
            if not new_project_name.strip():
                st.warning("Please enter a project name.")
            else:
                create_project(user_id, new_project_name.strip())
                st.success(f"Project *{new_project_name}* created.")
                st.rerun()

    st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)

    if not projects:
        st.info("🌟 You don't have any projects yet. Create your first project above to get started!")
    else:
        # Enhanced Projects Grid
        for project in projects:
            files = get_project_files(project["id"]) or []

            st.markdown('<div class="project-card-big">', unsafe_allow_html=True)

            header_col1, header_col2 = st.columns([4, 1])
            with header_col1:
                st.markdown(
                    f"""
                    <div class="project-header-row">
                        <div class="project-title-left">
                            <span>📁</span>
                            <span class="name">{project['name']}</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f"<div class='project-meta'>{len(files)} file(s)</div>",
                    unsafe_allow_html=True,
                )

            with header_col2:
                add_clicked = st.button(
                    "➕ File",
                    key=f"project_add_btn_{project['id']}",
                    help="Add a new file to this project",
                )
                if add_clicked:
                    st.session_state["show_add_file_for"] = project["id"]

            # thin file rows
            if files:
                for f in files:
                    file_lang = f.get("language", "code")
                    editor_url = (
                        f"{EDITOR_FRONTEND_URL}/editor/{f['room_id']}?username={username}"
                    )
                    st.markdown(
                        f"""
                        <div class="file-row-thin">
                            📄 <strong>{f['filename']}</strong>
                            <span class="lang">{file_lang.upper()}</span>
                            <a class="file-open-pill" href="{editor_url}" target="_blank">Open</a>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            else:
                st.markdown(
                    "<div style='font-size:11px;color:#6b7280;margin-top:4px;'>No files yet. Use the ➕ File button above.</div>",
                    unsafe_allow_html=True,
                )

            # inline add-file form if this card is active
            if st.session_state.get("show_add_file_for") == project["id"]:
                st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
                st.markdown("*Add new file*")
                with st.form(f"add_file_form_{project['id']}"):
                    fc1, fc2 = st.columns([3, 2])
                    with fc1:
                        filename = st.text_input(
                            "File name",
                            key=f"filename_{project['id']}",
                            placeholder="main.py / index.js ...",
                        )
                    with fc2:
                        language = st.selectbox(
                            "Language",
                            ["javascript", "python", "cpp", "java"],
                            key=f"lang_{project['id']}",
                        )
                    submit_file = st.form_submit_button("Create file")
                    if submit_file:
                        if not filename.strip():
                            st.warning("Please enter a file name.")
                        else:
                            create_project_file(
                                project["id"], filename.strip(), language
                            )
                            st.success(f"File *{filename}* created.")
                            st.session_state["show_add_file_for"] = None
                            st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

    # Coding Tips Section with Refresh Button
    tips_html = f"""
    <div class="tips-section">
        <div class="tips-header">
            <h3 class="tips-title">💡 Pro Coding Tips</h3>
            <button class="refresh-tips-btn" onclick="refreshTips()">
                🔄 
            </button>
        </div>
        <div class="tips-grid">
            <div class="tip-card">
                <div class="tip-card-title">{st.session_state.coding_tips[0]['title']}</div>
                <div class="tip-card-desc">{st.session_state.coding_tips[0]['desc']}</div>
            </div>
            <div class="tip-card">
                <div class="tip-card-title">{st.session_state.coding_tips[1]['title']}</div>
                <div class="tip-card-desc">{st.session_state.coding_tips[1]['desc']}</div>
            </div>
            <div class="tip-card">
                <div class="tip-card-title">{st.session_state.coding_tips[2]['title']}</div>
                <div class="tip-card-desc">{st.session_state.coding_tips[2]['desc']}</div>
            </div>
            <div class="tip-card">
                <div class="tip-card-title">{st.session_state.coding_tips[3]['title']}</div>
                <div class="tip-card-desc">{st.session_state.coding_tips[3]['desc']}</div>
            </div>
        </div>
    </div>
    """
    st.markdown(tips_html, unsafe_allow_html=True)

    # JavaScript for refresh tips
    components.html(
        """
        <script>
        function refreshTips() {
            window.parent.postMessage({
                type: 'streamlit:setComponentValue',
                value: {refreshTips: true}
            }, '*');
        }
        </script>
        """,
        height=0
    )

    # Handle refresh tips
    if st.session_state.get('refreshTips'):
        st.session_state.coding_tips = random.sample(CODING_TIPS, 4)
        st.session_state.refreshTips = False
        st.rerun()

    # Fixed Floating Chat Button (always visible)
    floating_chat = """
    <style>
    #ai_chat_btn {
        position: fixed !important;
        bottom: 25px !important;
        right: 25px !important;
        width: 65px !important;
        height: 65px !important;
        border-radius: 50% !important;
        background: linear-gradient(135deg, #8b5cf6 0%, #3b82f6 100%) !important;
        color: white !important;
        border: none !important;
        font-size: 30px !important;
        cursor: pointer !important;
        box-shadow: 0 6px 22px rgba(15,23,42,0.85) !important;
        transition: 0.25s !important;
        z-index: 999999 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    #ai_chat_btn:hover {
        transform: scale(1.12) !important;
        box-shadow: 0 10px 30px rgba(15,23,42,0.95) !important;
    }

    #ai_chat_box {
        position: fixed !important;
        bottom: 10px !important;
        right: 25px !important;
        width: 380px !important;
        height: 460px !important;
        background: #020617 !important;
        border-radius: 16px !important;
        box-shadow: 0 16px 40px rgba(0,0,0,0.65) !important;
        overflow: hidden !important;
        z-index: 999999 !important;
        display: none !important;
        transform: translateY(40px) !important;
        opacity: 0 !important;
        transition: all .35s ease !important;
        border: 1px solid #334155 !important;
    }
    #ai_chat_box.open {
        display: block !important;
        transform: translateY(0px) !important;
        opacity: 1 !important;
    }

    [data-testid="stSidebar"] { overflow: hidden !important; }

    #ai_chat_header {
        background: linear-gradient(135deg, #8b5cf6 0%, #3b82f6 100%) !important;
        color: white !important;
        padding: 10px 14px !important;
        font-size: 18px !important;
        font-weight: 600 !important;
        display: flex !important;
        justify-content: space-between !important;
        align-items: center !important;
        position: absolute !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        height: 50px !important;
        z-index: 1000000000 !important;
    }
    #ai_chat_close {
        cursor: pointer !important;
        font-size: 22px !important;
        font-weight: 900 !important;
    }
    #ai_chat_close:hover {
        color: #ffe5e5 !important;
    }

    #ai_chat_iframe {
        margin-top: 60px !important;
    }
    </style>

    <button id="ai_chat_btn">💬</button>

    <div id="ai_chat_box">
        <div id="ai_chat_header">
            CodeVerse AI
            <span id="ai_chat_close">✖</span>
        </div>
        <iframe id="ai_chat_iframe" src="/?chat=1"
            width="100%"
            height="410px"
            style="border:none;background:#020617;"></iframe>
    </div>

    <script>
    const btn = document.getElementById("ai_chat_btn");
    const box = document.getElementById("ai_chat_box");
    const closeBtn = document.getElementById("ai_chat_close");

    btn.onclick = () => {
        box.classList.add("open");
    };
    closeBtn.onclick = () => {
        box.classList.remove("open");
    };

    // Make sure chat button stays fixed during scroll
    window.addEventListener('scroll', function() {
        const chatBtn = document.getElementById('ai_chat_btn');
        if (chatBtn) {
            chatBtn.style.position = 'fixed';
            chatBtn.style.bottom = '25px';
            chatBtn.style.right = '25px';
        }
    });
    </script>
    """

    components.html(
        f"""
        <div style="height:0;width:0;">
        {floating_chat}
        </div>
        """,
        height=0,
        width=0,
        scrolling=False,
    )


if __name__ == "main":
    dashboard()