import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
from groq import Groq
from dotenv import load_dotenv
import os

def dashboard():
    # --------- PAGE CONFIG ----------
    st.set_page_config(page_title="Codeverse Ai", page_icon="🤖", layout="wide")

    # --------- LOAD GROQ & CHAT MEMORY ----------
    # --------- LOAD GROQ & CHAT MEMORY ----------
    load_dotenv()
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    # Separate key for chatbot messages
    if "chatbot_messages" not in st.session_state:
        st.session_state.chatbot_messages = [
            {"role": "assistant", "content": "Welcome to CodeVerse AI. How can I help you today? 😊"}
        ]

    # --------- CHECK IF THIS IS CHAT POPUP MODE ----------
    params = st.query_params
    is_chat_mode = params.get("chat", "0") == "1"

    if is_chat_mode:
        # Hide Streamlit top bar + sidebar
        st.markdown("""
        <style>
        header {display: none !important;}
        [data-testid="stSidebar"] {display: none !important;}
        [data-testid="stToolbar"] {display: none !important;}
        .block-container {padding-top: 0.4rem !important;}
        .stChatMessageAvatar {display: none !important;}
        </style>
        """, unsafe_allow_html=True)

        # Show chat history
        for msg in st.session_state.chatbot_messages:
            st.chat_message(msg["role"]).write(msg["content"])

        # Chat input
        user_input = st.chat_input("Type your message...")

        if user_input:
            st.chat_message("user").write(user_input)
            st.session_state.chatbot_messages.append({"role": "user", "content": user_input})

            # Typing animation
            typing_msg = st.chat_message("assistant")
            typing_placeholder = typing_msg.empty()
            typing_placeholder.write(" typing...")

            # Call Groq model
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": "You are a helpful and friendly AI assistant."}] +
                        st.session_state.chatbot_messages
            )
            reply = response.choices[0].message.content

            # Replace typing animation
            typing_placeholder.empty()
            st.chat_message("assistant").write(reply)
            st.session_state.chatbot_messages.append({"role": "assistant", "content": reply})

        # Clear chat
        if st.button(" Clear Conversation"):
            st.session_state.chatbot_messages = [
                {"role": "assistant", "content": "Welcome to CodeVerse AI.  How can I help you today? 😊"}
            ]
            st.rerun()

        st.stop()



    # ================= NORMAL DASHBOARD BELOW (YOUR ORIGINAL CODE) =================

    # --------- CUSTOM CSS ----------
    st.markdown("""
    <style>
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #0f1c2e;
        color: white;
        padding-top: 20px;
    }
    [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: white;
    }

    /* Main Page */
    .main {
        background-color: #f8f9fa;
    }

    /* Metric Cards */
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .metric-title {
        font-size: 16px;
        color: #6c757d;
        font-weight: 600;
    }
    .metric-value {
        font-size: 28px;
        color: #007bff;
        font-weight: 700;
    }

    /* Buttons */
    .stButton>button {
        background-color: #007bff;
        color: white;
        border-radius: 8px;
        padding: 10px 20px;
        border: none;
        font-weight: 500;
    }
    .stButton>button:hover {
        background-color: #0056b3;
        color: white;
    }
    /* COLLAB BOX */
        .collab-box {
            background: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-radius: 12px;
            padding: 20px;
            color: #1E2A3A;
            box-shadow: 0px 2px 6px rgba(0,0,0,0.05);
        }

        .collab-item {
            background: #F2F4F7;
            padding: 8px 10px;
            border-radius: 6px;
            margin-bottom: 6px;
        }
    </style>
    """, unsafe_allow_html=True)


    # --------- SIDEBAR ----------
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/4712/4712105.png", width=80)
        st.markdown("<h2 style='color:white; margin-top:10px;'>CodeVerse Ai</h2>", unsafe_allow_html=True)
        st.markdown("<hr style='border:1px solid #1f2f47;'>", unsafe_allow_html=True)

        st.markdown("""
        <style>
        /* Sidebar Buttons */
        .nav-btn {
            display: block;
            width: 100%;
            background-color: transparent;
            color: white;
            text-align: left;
            padding: 10px 16px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            margin-bottom: 6px;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .nav-btn:hover {
            background-color: #007bff;
            color: white;
        }
        .nav-btn.active {
            background-color: #007bff;
            color: #0f1c2e;
            font-weight: 600;
        }

        /* Rounded Green Button */
        .green-btn {
            display: block;
            width: 100%;
            background-color: #2ecc71;
            color: #0f1c2e;
            border: none;
            border-radius: 50px;
            font-size: 16px;
            font-weight: 600;
            padding: 10px 16px;
            margin-top: 15px;
            margin-bottom: 8px;
            cursor: pointer;
            transition: 0.3s ease;
        }
        .green-btn:hover {
            background-color: #27ae60;
            color: white;
        }

        /* Rounded Transparent Button (white border) */
        .white-border-btn {
            display: block;
            width: 100%;
            background-color: transparent;
            color: white;
            border: 1px solid white;
            border-radius: 50px;
            font-size: 16px;
            padding: 10px 16px;
            margin-bottom: 10px;
            cursor: pointer;
            transition: 0.3s ease;
        }
        .white-border-btn:hover {
            background-color: #007bff;
            border-color: #007bff;
            color: white;
        }

        /* Rounded Logout Button (Red) */
        .logout-btn {
            display: block;
            width: 100%;
            background-color: #e74c3c;
            color: white;
            border: none;
            border-radius: 50px;
            font-size: 16px;
            padding: 10px 16px;
            margin-top: 15px;
            cursor: pointer;
            font-weight: 600;
            transition: 0.3s ease;
        }
        .logout-btn:hover {
            background-color: #c0392b;
        }

        .sidebar-footer {
            color: gray;
            text-align: center;
            font-size: 13px;
            margin-top: 10px;
        }
        </style>
        """, unsafe_allow_html=True)

        # --- Navigation Buttons ---
        st.markdown(f"<button class='nav-btn active'>🏠 Dashboard</button>", unsafe_allow_html=True)
        st.markdown(f"<button class='nav-btn'>📊 View Editor</button>", unsafe_allow_html=True)
        st.markdown(f"<button class='nav-btn'>💬 Chat</button>", unsafe_allow_html=True)
        st.markdown(f"<button class='nav-btn'>⚙ Settings</button>", unsafe_allow_html=True)

        st.markdown("<hr style='border:1px solid #1f2f47;'>", unsafe_allow_html=True)

        # --- Rounded Action Buttons ---
        st.markdown("<button class='green-btn'>➕ Create New Project</button>", unsafe_allow_html=True)

        st.markdown("<hr style='border:1px solid #1f2f47;'>", unsafe_allow_html=True)
        st.markdown("<button class='logout-btn' onClick='window.location.href=\"/pages/1_Login\"'>🚪 Logout</button>", unsafe_allow_html=True)


    # --------- MAIN DASHBOARD ----------
    
    st.markdown("## 👋 Welcome back, *Akshit!*")

    # --- METRICS SECTION ---
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown('<div class="metric-card"><div class="metric-title">🧠 Total Projects Generated</div><div class="metric-value">1345</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="metric-card"><div class="metric-title">🔥 Streak</div><div class="metric-value">3 Days</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="metric-card"><div class="metric-title">💡 AI Tip</div><div class="metric-value">Keep code modular!</div></div>', unsafe_allow_html=True)

    # --- ⚡ QUICK AI ACTIONS SECTION ---
    st.markdown("### ⚡ Quick AI Actions")

    colA, colB, colC = st.columns(3)

    with colA:
        if st.button("🧠 Explain Code"):
            st.success("✅ AI is explaining your code...")

    with colB:
        if st.button("🐞 Debug Code"):
            st.warning("🔍 AI is debugging your code...")

    with colC:
        if st.button("📝 Generate Docs"):
            st.info("🧾 AI is generating documentation...")

    # --- ACTIVITY CHART ---
    st.markdown("### 📊 Project Generation Activity (Last 6 Months)")

    data = pd.DataFrame({
        "Month": ["May", "Jun", "Jul", "Aug", "Sep", "Oct"],
        "AI Basics": [5, 7, 8, 6, 9, 10],
        "Python Logic": [4, 6, 5, 7, 8, 9],
        "ML Quiz": [3, 4, 5, 6, 5, 7]
    })

    fig = px.bar(
        data, x="Month", y=["AI Basics", "Python Logic", "ML Quiz"],
        barmode="group",
        color_discrete_sequence=["#007bff", "#17a2b8", "#28a745"]
    )
    st.plotly_chart(fig, use_container_width=True)

    # --- RECENT HISTORY TABLE ---
    st.markdown("### 🕒 Recent Project History")
    recent_data = pd.DataFrame({
        "Project Name": ["AI Fundamentals", "Python Logic", "ML Concepts","AI Fundamentals", "Python Logic", "ML Concepts"],
        "Created On": ["2025-10-20", "2025-10-29", "2025-11-08","2025-10-20", "2025-10-29", "2025-11-08"],
        "Status": ["✅ Completed", "⏳ Ongoing", "📝 Draft","✅ Completed", "⏳ Ongoing", "📝 Draft"]
    })
    st.dataframe(recent_data, use_container_width=True)
    
        # --- Collaborators Section ---
    st.markdown('<div class="collab-box">', unsafe_allow_html=True)
    st.subheader("💬 Collaborators Online")
    st.markdown('<div class="collab-item">🟢 Priya – Editing auth.py</div>', unsafe_allow_html=True)
    st.markdown('<div class="collab-item">🟢 Raj – Debugging utils.py</div>', unsafe_allow_html=True)
    st.markdown('<div class="collab-item">🟢 Asif – Reviewing dashboard.py</div>', unsafe_allow_html=True)
    st.markdown('<div class="collab-item">🟢 Amit – Working on AI tools</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


    # ================= FLOATING CHAT BUTTON + POPUP =================
    # NOTE: height is NON-ZERO so the chat is *visible*, not cut/hidden "behind" the table
    floating_chat = """
    <style>
    /* Floating button */
    #ai_chat_btn {
        position: fixed;
        bottom: 25px;
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

    /* Chat popup with SLIDE animation */
    #ai_chat_box {
        position: fixed;
        bottom: 8px;
        right: 25px;
        width: 380px;
        height: 460px;
        background: white;
        border-radius: 14px;
        box-shadow: 0 12px 28px rgba(0,0,0,0.45);
        overflow: hidden;
        z-index: 999999;
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
        z-index: 1000000000; /* ABOVE IFRAME */
    }
    #ai_chat_close {
        cursor: pointer;
        font-size: 22px;
        font-weight: 900;
    }
    #ai_chat_close:hover {
        color: #ffe5e5;
    }

    /* Push iframe below header */
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
        <iframe id="ai_chat_iframe" src="/?chat=1"
            width="100%"
            height="410px"
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
    </script>
    """
    components.html(
    f"""
    <div style="height:100vh;width:100vw;">
    {floating_chat}
    </div>
    """,
    height=0,
    width=0,
    scrolling=False
)
