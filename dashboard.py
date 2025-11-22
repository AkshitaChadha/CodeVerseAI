import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
from groq import Groq
from dotenv import load_dotenv
import os
import uuid

from db import (
    init_db,
    get_dashboard_stats,
    get_user_projects,
    get_project_files,
    create_project,
    create_project_file,
    get_current_streak,
)

# ---------- INIT ----------

load_dotenv()
init_db()

# Local editor frontend (port 5000 for local)
EDITOR_FRONTEND_URL = os.getenv("EDITOR_FRONTEND_URL", "https://codeverseai-editor.vercel.app")


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

    # --------- CHECK IF THIS IS CHAT POPUP MODE ----------
    params = st.query_params
    is_chat_mode = params.get("chat", "0") == "1"

    # ========== INLINE CHAT MODE (POPUP) ==========
    if is_chat_mode:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))

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

        if "chatbot_messages" not in st.session_state:
            st.session_state.chatbot_messages = [
                {
                    "role": "assistant",
                    "content": "Welcome to CodeVerse AI. How can I help you today? 😊",
                }
            ]

        for msg in st.session_state.chatbot_messages:
            st.chat_message(msg["role"]).write(msg["content"])

        user_input = st.chat_input("Type your message...")

        if user_input:
            st.chat_message("user").write(user_input)
            st.session_state.chatbot_messages.append(
                {"role": "user", "content": user_input}
            )

            typing_msg = st.chat_message("assistant")
            typing_placeholder = typing_msg.empty()
            typing_placeholder.write(" typing...")

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

    # which project card is currently in “add file” mode
    if "show_add_file_for" not in st.session_state:
        st.session_state["show_add_file_for"] = None

    # --------- CSS ----------
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

    .stButton>button {
        background: linear-gradient(135deg, #8b5cf6 0%, #3b82f6 100%);
        color: white;
        border-radius: 10px;
        padding: 10px 18px;
        border: none;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(139, 92, 246, 0.3);
        font-size: 13px;
    }
    .stButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 8px 25px rgba(139, 92, 246, 0.5);
        background: linear-gradient(135deg, #8b5cf6 0%, #3b82f6 100%);
        color: white;
    }
    
    .collab-box {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 16px;
        padding: 16px;
        color: #f8fafc;
        box-shadow: 0 8px 32px rgba(0,0,0,0.2);
        margin-bottom: 12px;
    }

    .collab-item {
        background: rgba(139, 92, 246, 0.1);
        padding: 8px 10px;
        border-radius: 10px;
        margin-bottom: 6px;
        border-left: 4px solid #8b5cf6;
        font-weight: 500;
        font-size: 13px;
    }
    
    .nav-btn {
        display: block;
        width: 100%;
        background-color: transparent;
        color: #cbd5e1;
        text-align: left;
        padding: 12px 16px;
        border: none;
        border-radius: 8px;
        font-size: 15px;
        margin-bottom: 8px;
        cursor: pointer;
        transition: all 0.2s ease;
        font-weight: 500;
    }
    .nav-btn:hover {
        background: linear-gradient(135deg, #8b5cf6 0%, #3b82f6 100%);
        color: white;
        transform: translateX(5px);
    }
    .nav-btn.active {
        background: linear-gradient(135deg, #8b5cf6 0%, #3b82f6 100%);
        color: white;
        font-weight: 600;
    }

    .green-btn {
        display: block;
        width: 100%;
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        border: none;
        border-radius: 50px;
        font-size: 15px;
        font-weight: 600;
        padding: 11px 16px;
        margin-top: 15px;
        margin-bottom: 8px;
        cursor: pointer;
        transition: 0.3s ease;
    }
    .green-btn:hover {
        background: linear-gradient(135deg, #059669 0%, #047857 100%);
        color: white;
        transform: translateY(-2px);
    }

    .logout-btn {
        display: block;
        width: 100%;
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        color: white;
        border: none;
        border-radius: 50px;
        font-size: 15px;
        padding: 11px 16px;
        margin-top: 15px;
        cursor: pointer;
        font-weight: 600;
        transition: 0.3s ease;
    }
    .logout-btn:hover {
        background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
        transform: translateY(-2px);
    }

    /* Project big card */
    .project-card-big {
        background: #020617;
        border-radius: 16px;
        border: 1px solid #1f2937;
        padding: 14px 16px 12px 16px;
        box-shadow: 0 12px 35px rgba(15,23,42,0.7);
        margin-bottom: 18px;
    }
    .project-header-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 4px;
    }
    .project-title-left {
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .project-title-left span.name {
        font-size: 15px;
        font-weight: 600;
        color: #e5e7eb;
    }
    .project-meta {
        font-size: 11px;
        color: #9ca3af;
    }
    .project-plus-btn {
        background: #0f172a;
        border-radius: 999px;
        border: 1px solid #4b5563;
        padding: 4px 10px;
        font-size: 12px;
        color: #e5e7eb;
        display: inline-flex;
        align-items: center;
        gap: 4px;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    .project-plus-btn:hover {
        background: #4f46e5;
        border-color: #4f46e5;
        color: #ffffff;
    }

    .file-row-thin {
        font-size: 13px;
        padding: 4px 0;
        border-bottom: 1px solid rgba(31,41,55,0.65);
    }
    .file-row-thin:last-child {
        border-bottom: none;
    }
    .file-row-thin strong {
        color: #e5e7eb;
    }
    .file-row-thin span.lang {
        color: #9ca3af;
        font-size: 11px;
        margin-left: 4px;
    }
    .file-open-pill {
        font-size: 11px;
        padding: 2px 8px;
        border-radius: 999px;
        border: 1px solid #4b5563;
        color: #e5e7eb;
        text-decoration: none;
        margin-left: 8px;
    }
    .file-open-pill:hover {
        background: #4f46e5;
        border-color: #4f46e5;
        color: #ffffff;
    }

    /* Quick AI buttons inside card */
    .ai-quick-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 8px;
        margin-top: 10px;
    }
    .ai-quick-btn {
        width: 100%;
        background: linear-gradient(135deg, #8b5cf6 0%, #3b82f6 100%);
        color: #ffffff;
        border-radius: 10px;
        padding: 8px 10px;
        border: none;
        font-size: 12px;
        font-weight: 600;
        cursor: pointer;
        box-shadow: 0 4px 15px rgba(139,92,246,0.25);
        transition: all 0.2s ease;
    }
    .ai-quick-btn:hover {
        transform: translateY(-1px);
        box-shadow: 0 8px 20px rgba(139,92,246,0.40);
    }
    .ai-quick-btn:active {
        transform: translateY(0px) scale(0.98);
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # --------- SIDEBAR ----------
    with st.sidebar:
        st.markdown(
            """
            <div style="text-align: center; margin-bottom: 30px;">
                <div style="font-size: 28px; font-weight: 800; background: linear-gradient(135deg, #61dafb, #bd93f9); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 5px;">
                    CodeVerse AI
                </div>
                <div style="font-size: 12px; color: #bd93f9; font-weight: 500;">
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
            "<button class='nav-btn active'>🏠 Overview</button>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<button class='nav-btn'>📁 My Projects</button>",
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
<a href="{EDITOR_FRONTEND_URL}/" target="_blank" style="text-decoration: none;">
    <button class='nav-btn' style="width: 100%;">👨‍💻 Open Editor Home</button>
</a>
""",
            unsafe_allow_html=True,
        )

        st.markdown(
            "<button class='nav-btn'>⚙ Settings</button>", unsafe_allow_html=True
        )

        st.markdown(
            "<hr style='border:1px solid #334155;'>", unsafe_allow_html=True
        )

        st.markdown(
            "<button class='green-btn'>➕ Create New Project</button>",
            unsafe_allow_html=True,
        )

        st.markdown(
            "<hr style='border:1px solid #334155;'>", unsafe_allow_html=True
        )

        if st.button("🚪 Logout", key="logout_sidebar"):
            for k in ["user", "authenticated", "auth_mode"]:
                st.session_state.pop(k, None)
            st.rerun()

    # --------- MAIN: WELCOME + METRICS ----------
    st.markdown(f"## 👋 Welcome back, *{username}!*")

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
            f'<div class="metric-card"><div class="metric-title">📏 Total Lines of Code</div><div class="metric-value">{total_lines}</div></div>',
            unsafe_allow_html=True,
        )

    # soft spacer
    st.markdown("<div style='height:18px;'></div>", unsafe_allow_html=True)

    # ================== PROJECT SECTION ==================
    st.markdown("### 📁 Your Projects")

    # new project form
    with st.form("create_project_form"):
        c1, c2 = st.columns([4, 1])
        with c1:
            new_project_name = st.text_input(
                "Project name", placeholder="My awesome project"
            )
        with c2:
            create_project_btn = st.form_submit_button("Create")
        if create_project_btn:
            if not new_project_name.strip():
                st.warning("Please enter a project name.")
            else:
                create_project(user_id, new_project_name.strip())
                st.success(f"Project **{new_project_name}** created.")
                st.rerun()

    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

    if not projects:
        st.info("You don't have any projects yet. Create one above to get started.")
    else:
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
                st.markdown("**Add new file**")
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
                            st.success(f"File **{filename}** created.")
                            st.session_state["show_add_file_for"] = None
                            st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

    # more breathing space
    st.markdown("<div style='height:22px;'></div>", unsafe_allow_html=True)

    # ================= ACTIVITY + RIGHT BOXES =================
    st.markdown("### 📊 Activity & Insights")

    left, right = st.columns([2, 1])

    with left:
        data = pd.DataFrame(
            {
                "Month": ["May", "Jun", "Jul", "Aug", "Sep", "Oct"],
                "Projects": [3, 4, 2, 5, 4, 6],
            }
        )
        fig = px.line(
            data,
            x="Month",
            y="Projects",
            markers=True,
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#cbd5e1"),
        )
        fig.update_xaxes(gridcolor="#334155")
        fig.update_yaxes(gridcolor="#334155")
        st.plotly_chart(fig, use_container_width=True)

    # helper for quick rooms
    def quick_room_link(action_slug: str) -> str:
        room_id = uuid.uuid4().hex
        return f"{EDITOR_FRONTEND_URL}/editor/{room_id}?username={username}&from={action_slug}"

    with right:
        # Quick AI Actions in a side card
        explain_url = quick_room_link("explain")
        debug_url = quick_room_link("debug")
        docs_url = quick_room_link("docs")
        optimize_url = quick_room_link("optimize")

        ai_html = f"""
        <div class="collab-box">
            <h3 style="margin-top:0;">⚡ Quick AI Actions</h3>
            <div class="ai-quick-grid">
                <a href="{explain_url}" target="_blank" style="text-decoration:none;">
                    <button class="ai-quick-btn">🧠 Explain Code</button>
                </a>
                <a href="{debug_url}" target="_blank" style="text-decoration:none;">
                    <button class="ai-quick-btn">🐞 Debug Code</button>
                </a>
                <a href="{docs_url}" target="_blank" style="text-decoration:none;">
                    <button class="ai-quick-btn">📝 Generate Docs</button>
                </a>
                <a href="{optimize_url}" target="_blank" style="text-decoration:none;">
                    <button class="ai-quick-btn">🚀 Optimize Code</button>
                </a>
            </div>
        </div>
        """
        st.markdown(ai_html, unsafe_allow_html=True)

        # Quick stats below it
        st.markdown(
            """
        <div class="collab-box">
            <h3 style="margin-top:0;">📈 Quick Stats</h3>
            <div style="font-size:13px;color:#cbd5e1;margin-top:6px;">
                Sessions this week: <b>4</b><br/>
                Avg. session length: <b>32 min</b><br/>
                Most used language: <b>Python</b>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # ================= FLOATING CHAT BUTTON =================
    floating_chat = """
    <style>
    #ai_chat_btn {
        position: fixed;
        bottom: 25px;
        right: 25px;
        width: 70px;
        height: 70px;
        border-radius: 50%;
        background: linear-gradient(135deg, #8b5cf6 0%, #3b82f6 100%);
        color: white;
        border: none;
        font-size: 32px;
        cursor: pointer;
        box-shadow: 0 8px 25px rgba(139, 92, 246, 0.4);
        transition: all 0.3s ease;
        z-index: 10000;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    #ai_chat_btn:hover {
        transform: scale(1.15) rotate(5deg);
        box-shadow: 0 12px 35px rgba(139, 92, 246, 0.6);
    }

    #ai_chat_box {
        position: fixed;
        bottom: 100px;
        right: 25px;
        width: 380px;
        height: 500px;
        background: #1e293b;
        border-radius: 20px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.4);
        overflow: hidden;
        z-index: 10000;
        display: none;
        transform: translateY(20px) scale(0.95);
        opacity: 0;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        border: 1px solid #334155;
    }
    #ai_chat_box.open {
        display: block;
        transform: translateY(0) scale(1);
        opacity: 1;
    }

    #ai_chat_header {
        background: linear-gradient(135deg, #8b5cf6 0%, #3b82f6 100%);
        color: white;
        padding: 15px 20px;
        font-size: 18px;
        font-weight: 600;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    #ai_chat_close {
        cursor: pointer;
        font-size: 20px;
        font-weight: bold;
        transition: 0.2s ease;
    }
    #ai_chat_close:hover {
        transform: scale(1.2);
        color: #ffe5e5;
    }

    #ai_chat_iframe {
        border: none;
        background: #1e293b;
    }
    </style>

    <button id="ai_chat_btn">💬</button>

    <div id="ai_chat_box">
        <div id="ai_chat_header">
            CodeVerse AI Assistant
            <span id="ai_chat_close">✕</span>
        </div>
        <iframe id="ai_chat_iframe" src="/?chat=1"
            width="100%"
            height="460px"
            style="border:none;"></iframe>
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
    
    document.addEventListener('click', (e) => {
        if (!box.contains(e.target) && e.target !== btn) {
            box.classList.remove('open');
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
    )


if __name__ == "__main__":
    dashboard()
