import streamlit as st
import time
import random

from db import (
    insert_user,
    find_user_by_email,
    update_password,
    check_password,
    save_password_reset_otp,
    get_password_reset_record,
    clear_password_reset,
)
from utils import password_hash
from mail_utils import welcome_mail, send_otp_mail


def inject_auth_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap');

        body, .stApp {
            background: linear-gradient(180deg, #0B1333 0%, #101D61 100%);
            color: white !important;
            font-family: 'Inter', sans-serif;
        }

        #MainMenu, footer {visibility: hidden;}

        .auth-title {
            font-size: 2rem;
            font-weight: 800;
            color: white ;
            text-align: center;
            margin-bottom: 2rem;
            margin-top: -2rem;
        }

        div[data-testid="stTextInput"] input {
            background-color: rgba(255,255,255,0.1);
            border-radius: 10px;
            border: 1px solid rgba(58,102,255,0.3);
            color: black !important;
        }
        div[data-testid="stTextInput"] input:focus {
            border: 1px solid #3A66FF;
            box-shadow: 0 0 8px #3A66FF80;
        }
        
        div[data-testid="stTextInput"] > label > div > p {
            color: #FFFFFF !important;
            font-weight: 500;
            font-size: 0.9rem;
        }

        div.stButton>button {
            background: linear-gradient(90deg, #3A66FF, #2D58E0);
            color: white;
            font-weight: 600;
            border: none;
            border-radius: 30px;
            padding: 0.6rem 2.2rem;
            cursor: pointer;
            transition: 0.3s;
            white-space: nowrap;
            display: inline-block;
            width: auto !important;
            max-width: none !important;
            text-align: center;
        }
        div.stButton>button:hover {
            background: linear-gradient(90deg, #2D58E0, #3A66FF);
            box-shadow: 0 0 15px rgba(58, 102, 255, 0.4);
        }

        .secondary-btn {
            color: #3A66FF !important;
            font-weight: 600;
            text-decoration: none;
            display: block;
            text-align: center;
            margin-top: 1rem;
        }
        .secondary-btn:hover {text-decoration: underline;}
        </style>
    """, unsafe_allow_html=True)


# Helper: small centered layout
def centered_container():
    """Creates a visually centered narrow column for forms."""
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    left, center, right = st.columns([1, 0.6, 1])
    return center


def generate_otp() -> str:
    """Generate a 6-digit OTP as string."""
    return f"{random.randint(100000, 999999)}"


# --- SIGNUP ---
def signup():
    inject_auth_css()
    with centered_container():
        st.markdown('<div class="auth-title">Create Account</div>', unsafe_allow_html=True)

        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm = st.text_input("Confirm Password", type="password")

        if st.button("Sign Up"):
            if password != confirm:
                st.error("Passwords do not match.")
                st.stop()
            existing_user = find_user_by_email(email)
            if existing_user:
                st.warning("Email already registered.")
                st.stop()
            success = insert_user(username, email, password)
            if success:
                try:
                    welcome_mail(email, username)
                except Exception as e:
                    print("Mail error:", e)
                st.session_state["auth_mode"] = "login"
                st.rerun()
            else:
                st.error("Failed to create account. Please try again.")
        
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("Already have an account? Login", key="signup_to_login_center"):
                st.session_state["auth_mode"] = "login"
                st.rerun()


# --- LOGIN ---
def login():
    inject_auth_css()
    with centered_container():
        st.markdown('<div class="auth-title">Login to CodeVerse AI</div>', unsafe_allow_html=True)

        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        col1, col2 = st.columns(2)
        with col1:
            login_btn = st.button("Login")
        with col2:
            forgot_btn = st.button("Forgot Password?")

        if login_btn:
            user = find_user_by_email(email)
            if not user:
                st.error("No account found.")
            elif check_password(password, user["password"]):
                # Store user identity for dashboard
                st.session_state["user"] = {
                    "id": user["id"],
                    "username": user["username"]
                }
                st.session_state["authenticated"] = True
                st.session_state["auth_mode"] = "dashboard"
                
                # Clear inputs when rerender
                st.session_state.pop("email", None)
                st.session_state.pop("password", None)

                st.rerun()  # 👈 Redirect immediately to dashboard

            else:
                st.error("Invalid password.")

        if forgot_btn:
            st.session_state["auth_mode"] = "reset"
            for key in ["reset_step", "reset_email", "otp_cooldown_until"]:
                st.session_state.pop(key, None)
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("No account? Signup", key="login_to_signup_center"):
                st.session_state["auth_mode"] = "signup"
                st.rerun()

# --- RESET WITH OTP FLOW ---
def reset():
    inject_auth_css()

    if "reset_step" not in st.session_state:
        st.session_state["reset_step"] = "email"

    step = st.session_state["reset_step"]

    with centered_container():
        # STEP 1: Enter email → Send OTP
        if step == "email":
            st.markdown('<div class="auth-title">Reset Password</div>', unsafe_allow_html=True)

            email = st.text_input("Registered Email")

            if st.button("Send OTP"):
                user = find_user_by_email(email)
                if not user:
                    st.error("No account found with this email.")
                else:
                    otp = generate_otp()
                    expiry = int(time.time()) + 300  # 5 minutes
                    save_password_reset_otp(email, otp, expiry)

                    try:
                        send_otp_mail(email, otp)
                    except Exception as e:
                        print("OTP mail error:", e)
                        st.error("Could not send OTP. Please try again.")
                    else:
                        st.session_state["reset_email"] = email
                        st.session_state["otp_cooldown_until"] = int(time.time()) + 30  # 30s cooldown
                        st.session_state["reset_step"] = "otp"
                        st.success("An OTP has been sent to your email. It is valid for 5 minutes.")
                        st.rerun()

        # STEP 2: Verify OTP
        elif step == "otp":
            st.markdown('<div class="auth-title">Verify OTP</div>', unsafe_allow_html=True)
            email = st.session_state.get("reset_email", "")
            if email:
                st.write(f"OTP sent to: **{email}**")

            otp_input = st.text_input("Enter OTP")

            col1, col2 = st.columns(2)
            with col1:
                verify_btn = st.button("Verify OTP")
            with col2:
                resend_btn = st.button("Resend OTP")

            now = int(time.time())

            if verify_btn:
                record = get_password_reset_record(email)
                if not record:
                    st.error("No active OTP found. Please resend OTP.")
                else:
                    if now > record["otp_expiry"]:
                        st.error("OTP has expired. Please resend OTP.")
                    elif otp_input != record["otp_code"]:
                        st.error("Invalid OTP. Please check and try again.")
                    else:
                        st.success("OTP verified! Set your new password.")
                        st.session_state["reset_step"] = "new_password"
                        st.rerun()

            if resend_btn:
                cooldown_until = st.session_state.get("otp_cooldown_until", 0)
                if now < cooldown_until:
                    remaining = cooldown_until - now
                    st.warning(f"Please wait {remaining} seconds before resending OTP.")
                else:
                    otp = generate_otp()
                    expiry = int(time.time()) + 300
                    save_password_reset_otp(email, otp, expiry)
                    try:
                        send_otp_mail(email, otp)
                    except Exception as e:
                        print("OTP mail resend error:", e)
                        st.error("Could not resend OTP. Please try again.")
                    else:
                        st.success("A new OTP has been sent to your email.")
                        st.session_state["otp_cooldown_until"] = int(time.time()) + 30

        # STEP 3: Set New Password
        elif step == "new_password":
            st.markdown('<div class="auth-title">Set New Password</div>', unsafe_allow_html=True)

            new_pw = st.text_input("New Password", type="password")
            confirm_pw = st.text_input("Confirm New Password", type="password")

            if st.button("Reset Password"):
                email = st.session_state.get("reset_email")
                if not email:
                    st.error("Something went wrong. Please restart the reset process.")
                elif new_pw != confirm_pw:
                    st.warning("Passwords do not match.")
                else:
                    updated = update_password(email, new_pw)
                    if updated:
                        clear_password_reset(email)
                        st.success("✅ Password reset successful! Please log in.")
                        for key in ["reset_step", "reset_email", "otp_cooldown_until"]:
                            st.session_state.pop(key, None)
                        st.session_state["auth_mode"] = "login"
                        st.rerun()
                    else:
                        st.error("Something went wrong while updating password.")

        # Back link (works together with app.py's back button)
        st.markdown('<a class="secondary-btn" href="?login">← Back to Login</a>', unsafe_allow_html=True)
