import streamlit as st
from dotenv import load_dotenv

query = st.query_params
if "page" in query:
    st.session_state["auth_mode"] = query["page"]


load_dotenv()
# Initialize session
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if "auth_mode" not in st.session_state:
    st.session_state["auth_mode"] = "landing"


# Always auto-switch to dashboard when authenticated
if st.session_state["authenticated"]:
    st.session_state["auth_mode"] = "dashboard"

mode = st.session_state["auth_mode"]


# Dynamic Imports (avoid circular import)
if mode == "dashboard":
    from dashboard import dashboard
    dashboard()

elif mode == "landing":
    from landing import app_main
    app_main()

elif mode == "login":
    from auth import login
    login()

elif mode == "signup":
    from auth import signup
    signup()

elif mode == "reset":
    from auth import reset
    reset()
