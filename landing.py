import streamlit as st
from base64 import b64encode
import os


# --- 1. Inject Custom CSS ---
def inject_custom_css():
    """Injects custom CSS for CodeVerse AI landing page with all-white navbar text."""
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap');

        :root {
            --dark-bg: #0B1333;
            --blue-accent: #3A66FF;
            --text-light: #FFFFFF;
            --text-muted: #E6E9F7;
            --wave-light-blue: #F0F4F9;
            --wave-white: #FFFFFF;
        }

        .block-container { padding: 0 !important; margin: 0 !important; max-width: 100% !important; }
        .main, .viewerBadge_container__1QSob, .css-1dp5vir, .css-hxt7ib { padding: 0 !important; margin: 0 !important; }

        .stApp {
            background: linear-gradient(180deg, var(--dark-bg) 0%, var(--wave-light-blue) 100%);
            font-family: 'Inter', sans-serif;
            overflow-x: hidden;
        }

        #MainMenu, footer { visibility: hidden; }

        /* --- Navbar --- */
        .navbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1.5rem 5rem;
            background: transparent;
        }
        .navbar-left h1 { color: var(--text-light); font-size: 1.6rem; font-weight: 700; margin: 0; }
        .navbar-right { display: flex; align-items: center; gap: 25px; }
        .nav-link { color: var(--text-light) !important; font-size: 0.95rem; text-decoration: none; transition: 0.25s; }
        .nav-link:hover { color: var(--blue-accent) !important; }
        .nav-btn-primary, .nav-btn-secondary {
            padding: 8px 18px; border-radius: 20px; font-weight: 600; cursor: pointer; text-decoration: none;
            color: var(--text-light) !important; transition: 0.3s;
        }
        .nav-btn-primary { background-color: var(--blue-accent); }
        .nav-btn-secondary { border: 2px solid var(--text-light); background: transparent; }

        /* --- Hero Section --- */
        .hero {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 6rem 8rem;
            background: var(--dark-bg);
            color: var(--text-light);
            min-height: 90vh;
        }
        .hero-left h2 { font-size: 4.5rem; font-weight: 900; line-height: 1.1; margin-bottom: 1rem; }
        .hero-left p { font-size: 1.15rem; color: var(--text-muted); margin-bottom: 2.5rem; }
        .btn-primary {
            background-color: var(--blue-accent); padding: 12px 30px; border-radius: 25px;
            font-weight: 600; cursor: pointer; transition: 0.3s;
        }
        .btn-primary:hover { background-color: #2D58E0; }

        /* About Section */
        .about-section { padding: 6rem 8rem 2rem; text-align: center; background: var(--wave-white); }
        .about-section h3 { font-size: 2rem; margin-bottom: 1rem; }

        /* Features */
        .feature-section { display: flex; justify-content: space-around; padding: 4rem 6rem; background: #F8FAFF; }
        .feature { max-width: 300px; text-align: center; }
        .feature h4 { color: #3A66FF; margin-bottom: 0.8rem; }
        </style>
    """, unsafe_allow_html=True)


# --- 2. Landing Page ---
def app_main():
    st.set_page_config(page_title="CodeVerse AI", layout="wide", initial_sidebar_state="collapsed")
    inject_custom_css()
    # Load image correctly
    ASSET_PATH = os.path.join("assets", "monitor.png")
    with open(ASSET_PATH, "rb") as file:
        encoded_image = b64encode(file.read()).decode()
    # Navbar
    st.markdown("""
        <div class="navbar">
            <div class="navbar-left"><h1>CodeVerse AI</h1></div>
            <div class="navbar-right">
                <a href="#" class="nav-link">Contact</a>
                <a href="#" class="nav-link">About</a>
                <a href="#" class="nav-link">Privacy</a>
                <a href="?login" class="nav-btn-secondary">Login</a>
                <a href="?signup" class="nav-btn-primary">Create Account</a>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # ⭐ FINAL HERO SECTION WITH IMAGE ON RIGHT & PERFECT ALIGNMENT
    st.markdown(f"""
        <div class="hero">
            <div class="hero-left">
                <h2>Unlock the Future<br>of Coding</h2>
                <p>AI Assisted, Collaborative, Seamless</p>
                <form action="#" method="get">
                    <button class="btn-primary" type="submit" name="login">Get Started</button>
                </form>
            </div>
            <div class="hero-right">
                <img src="data:image/png;base64,{encoded_image}" style="width:450px; border-radius:10px;">
            </div>
        </div>
    """, unsafe_allow_html=True)

    # About Section
    st.markdown("""
        <div class="about-section">
            <h3>Why CodeVerse AI?</h3>
            <p>
                CodeVerse AI empowers developers and learners with intelligent, real-time coding assistance.
                It’s not just a tool — it’s your personal coding partner.
                Whether you’re building your first project or launching an enterprise app,
                CodeVerse AI brings speed, precision, and creativity to every line of code.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Feature Section
    st.markdown("""
        <div class="feature-section">
            <div class="feature">
                <h4>⚡ AI-Powered Coding</h4>
                <p>Get smart suggestions, automatic debugging, and code explanations — all powered by advanced AI models.</p>
            </div>
            <div class="feature">
                <h4>🌍 Team Collaboration</h4>
                <p>Work with your team in real-time, share projects, and review code seamlessly inside the same workspace.</p>
            </div>
            <div class="feature">
                <h4>🔒 Secure & Reliable</h4>
                <p>Built with enterprise-grade encryption and robust cloud infrastructure to keep your data private and protected.</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    

    # Routing
    query_params = st.query_params
    if "login" in query_params:
        st.session_state["auth_mode"] = "login"
        st.rerun()
    elif "signup" in query_params:
        st.session_state["auth_mode"] = "signup"
        st.rerun()

# --- Run Page ---
if __name__ == "_main_":
    app_main()