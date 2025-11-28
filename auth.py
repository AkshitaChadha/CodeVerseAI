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
    record_login,   # 🔹 NEW: for streaks
)
from utils import password_hash
from mail_utils import welcome_mail, send_otp_mail


# ---------- COMMON STYLING ----------

def st_errors_style():
    st.markdown(
        """
        <style>
        /* Base component */
        .stAlert{
            border-radius: 12px !important;
            font-weight: 600 !important;
        }

        /* ERROR (default red) */
        .stAlert div[role="alert"]:has(svg[data-testid="stNotificationIcon-error"]) {
            background: rgba(220, 38, 38, 0.92) !important;
            border: 1px solid rgba(185, 28, 28, 0.6) !important;
            color: #fff !important;
        }

        /* SUCCESS (GREEN STRIP) */
        .stAlert div[role="alert"]:has(svg[data-testid="stNotificationIcon-success"]) {
            background: rgba(34, 197, 94) !important;
            border: 1px solid rgba(21, 128, 61) !important;
            color: #ecfdf5 !important;
        }

        /* INFO (optional light blue) */
        .stAlert div[role="alert"]:has(svg[data-testid="stNotificationIcon-info"]) {
            background: rgba(59, 130, 246, 0.9) !important;
            border: 1px solid rgba(37, 99, 235, 0.6) !important;
            color: white !important;
        }

        /* WARNING (yellow) */
        .stAlert div[role="alert"]:has(svg[data-testid="stNotificationIcon-warning"]) {
            background: rgba(234, 179, 8, 0.92) !important;
            border: 1px solid rgba(202, 138, 4, 0.6) !important;
            color: #1f2937 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )



def inject_auth_css():
    """
    Global CSS for the auth pages.
    Dark theme (matching landing page), compact card, no scroll.
    """
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

        :root {
            --dark-bg: #0f172a;
            --darker-bg: #0a0f1c;
            --card-bg: #020617;
            --card-inner: #020617;
            --accent-blue: #3b82f6;
            --accent-purple: #8b5cf6;
            --accent-cyan: #06b6d4;
            --text-primary: #f8fafc;
            --text-secondary: #cbd5e1;
            --gradient-primary: linear-gradient(135deg, #8b5cf6 0%, #3b82f6 45%, #06b6d4 100%);
        }

        /* Remove Streamlit chrome */
        .stApp > header { display: none !important; }
        #MainMenu, footer { visibility: hidden; }

        .stApp {
            font-family: 'Inter', sans-serif !important;
            background: var(--darker-bg) !important;
        }

        /* Background + vertical placement */
        [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(circle at top, #1f2937 0, var(--dark-bg) 55%, var(--darker-bg) 100%) !important;
        }

        [data-testid="stAppViewContainer"] > .main {
            display: flex;
            align-items: flex-start;                 /* move card up */
            justify-content: center;
            min-height: 100vh;
            padding: 32px 0 24px !important;         /* less dead space at top */
        }

        /* Compact auth card (narrower form) */
        .main .block-container {
            max-width: 360px !important;             /* 🔽 was 420px */
            width: 100% !important;
            margin: 0 auto !important;
            padding: 2.0rem 1.9rem 2.0rem !important;
            background: radial-gradient(circle at top left, #111827 0, #020617 55%) !important;
            border-radius: 18px !important;
            box-shadow: 0 22px 42px rgba(15, 23, 42, 0.9) !important;
            backdrop-filter: blur(16px);
            position: relative;
            overflow: hidden;
            animation: authFadeIn 0.35s ease-out;
        }

        .main .block-container::before {
            display: none !important;
        }

        @keyframes authFadeIn {
            from {
                opacity: 0;
                transform: translateY(8px) scale(0.98);
            }
            to {
                opacity: 1;
                transform: translateY(0) scale(1);
            }
        }

        /* Prevent scroll */
        html, body, [data-testid="stAppViewContainer"] {
            overflow: hidden !important;
        }

        /* HEADER ROW: brand left, form name right */
        .auth-header {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 1.2rem;
            margin-bottom: 0.8rem;
        }

        .auth-header-left {
            display: flex;
            flex-direction: column;
            gap: 0.2rem;
        }

        .brand-main {
            font-size: 2.3rem !important;
            font-weight: 900 !important;
            background: linear-gradient(135deg, #61dafb, #bd93f9) !important;
            -webkit-background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
            line-height: 1.02;
        }

        .brand-subtitle {
            font-size: 0.85rem !important;
            color: #94a3b8 !important;
            font-weight: 500 !important;
            letter-spacing: 0.5px;
        }

        .auth-header-right {
            text-align: right;
        }

        .auth-title {
            font-size: 2.0rem;
            font-weight: 800;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 0.45rem;
            justify-content: flex-end;
        }

        .auth-title-dot {
            width: 10px;
            height: 10px;
            border-radius: 999px;
            background: var(--gradient-primary);
            box-shadow: 0 0 12px rgba(56,189,248,0.9);
        }

        .auth-mode-chip {
            font-size: 0.75rem;
            padding: 0.22rem 0.8rem;
            border-radius: 999px;
            border: 1px solid rgba(148, 163, 184, 0.5);
            color: var(--text-secondary);
            margin-top: 0.35rem;
            display: inline-block;
        }

        .auth-subtitle {
            color: var(--text-secondary);
            margin-bottom: 0.8rem;
            font-size: 1rem;
        }

        .auth-inner {
            max-width: 300px;                        /* 🔽 was 340px */
            margin: 0 auto;
        }

        /* NARROWER INPUT BOXES */
        .auth-inner div[data-testid="stTextInput"] {
            margin-bottom: 0.95rem !important;
            max-width: 260px !important;             /* 🔽 input width */
            margin-left: auto !important;
            margin-right: auto !important;
        }

        div[data-testid="stTextInput"] input {
            background: rgba(15, 23, 42, 0.9) !important;
            border-radius: 10px !important;
            border: 1px solid rgba(148, 163, 184, 0.32) !important;
            height: 44px !important;
            font-size: 0.95rem !important;
            color: var(--text-primary) !important;
            padding: 0 14px !important;
            transition: border 0.18s ease, box-shadow 0.18s ease, background 0.18s ease, transform 0.08s ease;
        }

        div[data-testid="stTextInput"] input:focus {
            border-color: var(--accent-blue) !important;
            box-shadow: 0 0 0 1px rgba(59, 130, 246, 0.8) !important;
            background: rgba(15, 23, 42, 1) !important;
            transform: translateY(-0.5px);
        }

        div[data-testid="stTextInput"] > label > div > p {
            color: var(--text-secondary) !important;
            font-size: 1.0rem !important;
            font-weight: 600 !important;
            margin-bottom: 0.4rem !important;
        }

        .stButton > button {
            width: 100% !important;
            height: 44px !important;
            border-radius: 999px !important;
            font-weight: 600 !important;
            font-size: 0.9rem !important;
            border: none !important;
            margin-top: 0.5rem !important;
            background: var(--gradient-primary) !important;
            color: #f9fafb !important;
            box-shadow: 0 10px 22px rgba(15, 118, 238, 0.55) !important;
            transition: transform 0.16s ease, box-shadow 0.16s ease, filter 0.1s ease;
        }

        .stButton > button:hover {
            transform: translateY(-1px) !important;
            box-shadow: 0 14px 30px rgba(30, 64, 175, 0.75) !important;
            filter: brightness(1.05);
        }

        .stForm .stColumns:nth-of-type(1) > div:nth-child(2) .stButton > button {
            background: transparent !important;
            color: var(--text-primary) !important;
            border: 1px solid rgba(148, 163, 184, 0.6) !important;
            box-shadow: none !important;
        }

        .stForm .stColumns:nth-of-type(1) > div:nth-child(2) .stButton > button:hover {
            background: rgba(15, 23, 42, 0.95) !important;
            border-color: var(--accent-blue) !important;
            box-shadow: 0 6px 16px rgba(15, 23, 42, 0.9) !important;
        }

        .auth-switch {
            text-align: center;
        }

        .auth-switch-text {
            color: var(--text-secondary);
            font-size: 0.85rem;
            margin-bottom: 0.7rem;
            font-weight: 500;
        }

        .auth-switch-note {
            margin-top: 0.5rem;
            font-size: 0.7rem;
            color: #6b7280;
        }

        .auth-switch-note span {
            color: #a5b4fc;
        }

        .stForm {
            margin-bottom: 0 !important;
        }

        @media (max-width: 480px) {
            .main .block-container {
                max-width: 92% !important;
                padding: 1.9rem 1.5rem 1.7rem !important;
                border-radius: 16px !important;
            }

            .brand-main {
                font-size: 2rem !important;
            }

            .auth-title {
                font-size: 1.7rem;
            }

            .auth-inner {
                max-width: 100%;
            }

            .auth-inner div[data-testid="stTextInput"]{
                max-width: 100% !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header(title: str, chip: str, subtitle: str):
    st.markdown(
        f"""
        <div class="auth-header">
            <div class="auth-header-left">
                <div class="brand-main">CodeVerse AI</div>
                <div class="brand-subtitle">Collaborative Code Editor</div>
            </div>
            <div class="auth-header-right">
                <div class="auth-title">
                    <div class="auth-title-dot"></div>
                    <span>{title}</span>
                </div>
                <div class="auth-mode-chip">{chip}</div>
            </div>
        </div>
        <div class="auth-subtitle">{subtitle}</div>
        """,
        unsafe_allow_html=True,
    )


def generate_otp() -> str:
    return f"{random.randint(100000, 999999)}"


# ---------- SIGNUP ----------

def signup():
    inject_auth_css()
    st_errors_style()

    render_header(
        title="Create Account",
        chip="Sign up",
        subtitle="Join our coding community and start collaborative sessions in seconds.",
    )

    st.markdown('<div class="auth-inner">', unsafe_allow_html=True)

    with st.form("signup_form", clear_on_submit=False):

        username = st.text_input("👤 Username")
        email = st.text_input("📧 Email")
        password = st.text_input("🔒 Password", type="password")
        confirm = st.text_input("✅ Confirm Password", type="password")
        agree = st.checkbox("I agree to the Terms & Privacy Policy")

        col1, col2 = st.columns(2)
        with col1:
            sign_btn = st.form_submit_button("🚀 Sign Up", use_container_width=True)
        with col2:
            back_btn = st.form_submit_button("← Login", use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Back button
    if back_btn:
        st.session_state["auth_mode"] = "login"
        st.rerun()

    # Validation on submit
    if sign_btn:
        # Required fields
        if not username or not email or not password or not confirm:
            st.error("⚠ All fields are required")
            return

        # Username length
        if len(username) < 3:
            st.error("⚠ Username must be at least 3 characters")
            return
        if username.isdigit():
            st.error("⚠ Username cannot be only numbers. Please include letters.")
            return

        # Email format
        import re
        email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        if not re.match(email_regex, email):
            st.error("⚠ Enter a valid email address")
            return

        # Password strength
        if len(password) < 6:
            st.error("⚠ Password must be at least 6 characters long")
            return
        if not any(c.isupper() for c in password):
            st.error("⚠ Password must contain at least 1 uppercase,lowercase letter ,number and special character.")
            return
        if not any(c.islower() for c in password):
            st.error("⚠ Password must contain at least 1 uppercase,lowercase letter ,number and special character.")
            return
        if not any(c.isdigit() for c in password):
            st.error("⚠ Password must contain at least 1 uppercase,lowercase letter ,number and special character.")
            return
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>/?" for c in password):
            st.error("⚠ Password must contain at least 1 uppercase,lowercase letter ,number and special character.")
            return

        # Confirm password match
        if password != confirm:
            st.error("⚠ Passwords do not match")
            return

        # Terms & Privacy Agreement
        if not agree:
            st.error("⚠ You must agree to the Terms & Privacy Policy")
            return

        # Email already exists
        if find_user_by_email(email):
            st.error("⚠ Email already registered")
            return

        # Insert and send email
        success = insert_user(username, email, password)
        if success:
            try:
                welcome_mail(email, username)
            except Exception as e:
                print("Mail sending failed:", e)

            st.success("🎉 Account created successfully! Redirecting to login...")
            st.session_state["auth_mode"] = "login"
            st.rerun()
        else:
            st.error("❌ Signup failed! Try again later")

    st.markdown(
        """
        <div class="auth-switch">
            <div class="auth-switch-text">Already have an account?</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Login to your account →", key="signup_switch", use_container_width=True):
        st.session_state["auth_mode"] = "login"
        st.rerun()

    st.markdown(
        """
        <div class="auth-switch-note">
            Secured with <span>OTP verification</span> and encrypted passwords.
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------- LOGIN ----------

def login():
    inject_auth_css()
    st_errors_style()

    render_header(
        title="Welcome Back",
        chip="Log in",
        subtitle="Continue your coding journey with real-time collaboration.",
    )

    st.markdown('<div class="auth-inner">', unsafe_allow_html=True)

    with st.form("login_form", clear_on_submit=False):
        email = st.text_input("📧 Email")
        password = st.text_input("🔒 Password", type="password")

        col1, col2 = st.columns(2)
        with col1:
            login_btn = st.form_submit_button("🔑 Login", use_container_width=True)
        with col2:
            forgot_btn = st.form_submit_button("🔓 Forgot?", use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Forgot Password button
    if forgot_btn:
        st.session_state["auth_mode"] = "reset"
        for key in ["reset_step", "reset_email", "otp_cooldown_until"]:
            st.session_state.pop(key, None)
        st.rerun()

    # Login button validation
    if login_btn:
        import re
        email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"

        # Required fields
        if not email or not password:
            st.error("⚠ Please enter both email and password.")
            return

        # Email format
        if not re.match(email_regex, email):
            st.error("⚠ Please enter a valid email address.")
            return

        # Check if user exists
        user = find_user_by_email(email)
        if not user:
            st.error("⚠ No account found with this email.")
            return

        # Check password
        if not check_password(password, user["password"]):
            st.error("⚠ Incorrect password.")
            return

        # If all validations pass → Login
        st.session_state["authenticated"] = True
        st.session_state["user"] = {
            "id": user["id"],
            "username": user["username"],
        }
        st.session_state["user_email"] = email

        # Session token
        session_token = f"TOKEN-{user['id']}-{int(time.time())}"
        st.session_state["access_token"] = session_token

        # Save token in browser
        st.write(
            f"""
            <script>
                localStorage.setItem("accessToken", "{session_token}");
            </script>
            """,
            unsafe_allow_html=True,
        )

        # Record login history
        try:
            record_login(user["id"])
        except Exception as e:
            print("record_login error:", e)

        st.success("🎉 Login successful! Redirecting...")
        st.session_state["auth_mode"] = "dashboard"
        st.rerun()

    # Bottom switch to signup
    st.markdown(
        """
        <div class="auth-switch">
            <div class="auth-switch-text">Don't have an account?</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Create new account →", key="login_to_signup", use_container_width=True):
        st.session_state["auth_mode"] = "signup"
        st.rerun()

    st.markdown(
        """
        <div class="auth-switch-note">
            Your credentials are encrypted and protected.
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------- RESET WITH OTP FLOW ----------

def reset():
    inject_auth_css()
    st_errors_style()

    if "reset_step" not in st.session_state:
        st.session_state["reset_step"] = "email"

    step = st.session_state["reset_step"]

    # ------------------------------------------
    # STEP 1: EMAIL
    # ------------------------------------------
    if step == "email":
        render_header(
            title="Reset Password",
            chip="Step 1 of 3",
            subtitle="Enter your registered email address and we'll send you a one-time code.",
        )

        st.markdown('<div class="auth-inner">', unsafe_allow_html=True)
        with st.form("reset_email_form", clear_on_submit=False):
            email = st.text_input("📧 Registered Email")
            send_btn = st.form_submit_button("📨 Send OTP", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        if send_btn:
            import re
            email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"

            if not email:
                st.error("⚠ Please enter your email.")
                return
            if not re.match(email_regex, email):
                st.error("⚠ Please enter a valid email address.")
                return

            user = find_user_by_email(email)
            if not user:
                st.error("⚠ No account found with this email.")
                return

            otp = generate_otp()
            expiry = int(time.time()) + 300
            save_password_reset_otp(email, otp, expiry)

            try:
                send_otp_mail(email, otp)
            except Exception as e:
                print("OTP mail error:", e)
                st.error("❌ Could not send OTP. Please try again.")
            else:
                st.session_state["reset_email"] = email
                st.session_state["otp_cooldown_until"] = int(time.time()) + 30
                st.session_state["reset_step"] = "otp"
                st.success("✅ OTP sent to your email")
                st.rerun()

    # ------------------------------------------
    # STEP 2: OTP
    # ------------------------------------------
    elif step == "otp":
        render_header(
            title="Verify OTP",
            chip="Step 2 of 3",
            subtitle="Enter the 6-digit code sent to your email to continue.",
        )

        email = st.session_state.get("reset_email", "")
        if email:
            st.info(f"📧 OTP sent to: *{email}*")

        st.markdown('<div class="auth-inner">', unsafe_allow_html=True)
        with st.form("otp_form", clear_on_submit=False):
            otp_input = st.text_input("🔢 Enter OTP")
            col1, col2 = st.columns(2)
            with col1:
                verify_btn = st.form_submit_button("✅ Verify", use_container_width=True)
            with col2:
                resend_btn = st.form_submit_button("🔄 Resend", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # OTP Verification
        if verify_btn:
            if not otp_input:
                st.error("⚠ Please enter OTP.")
                return
            if not otp_input.isdigit() or len(otp_input) != 6:
                st.error("⚠ OTP must be a 6-digit number.")
                return

            record = get_password_reset_record(email)
            now = int(time.time())
            if not record:
                st.error("⚠ No active OTP found. Please resend OTP.")
            elif now > record["otp_expiry"]:
                st.error("⚠ OTP has expired. Resend OTP.")
            elif otp_input != record["otp_code"]:
                st.error("⚠ Invalid OTP. Please check and try again.")
            else:
                st.success("🎉 OTP verified!")
                st.session_state["reset_step"] = "new_password"
                st.rerun()

        # OTP Resend
        if resend_btn:
            now = int(time.time())
            cooldown_until = st.session_state.get("otp_cooldown_until", 0)
            if now < cooldown_until:
                st.warning(f"⏰ Wait {cooldown_until - now}s before requesting again.")
            else:
                otp = generate_otp()
                expiry = int(time.time()) + 300
                save_password_reset_otp(email, otp, expiry)
                try:
                    send_otp_mail(email, otp)
                except Exception as e:
                    print("OTP resend error:", e)
                    st.error("❌ Could not resend OTP.")
                else:
                    st.success("📨 New OTP sent!")
                    st.session_state["otp_cooldown_until"] = int(time.time()) + 30

    # ------------------------------------------
    # STEP 3: NEW PASSWORD
    # ------------------------------------------
    elif step == "new_password":
        render_header(
            title="New Password",
            chip="Step 3 of 3",
            subtitle="Create a new password for your CodeVerse account.",
        )

        st.markdown('<div class="auth-inner">', unsafe_allow_html=True)
        with st.form("new_password_form", clear_on_submit=False):
            new_pw = st.text_input("🔒 New Password", type="password")
            confirm_pw = st.text_input("✅ Confirm Password", type="password")
            reset_btn = st.form_submit_button("🔄 Reset", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        if reset_btn:
            # Required
            if not new_pw or not confirm_pw:
                st.error("⚠ Please fill both password fields.")
                return

            # Strength validation
            if len(new_pw) < 6:
                st.error("⚠ Password must be at least 6 characters long.")
                return
            if not any(c.isupper() for c in new_pw):
                st.error("⚠ Password must contain at least 1 uppercase,lowercase letter ,number and special character.")
                return
            if not any(c.islower() for c in new_pw):
                st.error("⚠ Password must contain at least 1 uppercase,lowercase letter ,number and special character.")
                return
            if not any(c.isdigit() for c in new_pw):
                st.error("⚠ Password must contain at least 1 uppercase,lowercase letter ,number and special character.")
                return
            if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>/?' for c in new_pw):
                st.error("⚠ Password must contain at least 1 uppercase,lowercase letter ,number and special character.")
                return

            # Confirm match
            if new_pw != confirm_pw:
                st.error("⚠ Passwords do not match.")
                return

            # Update DB
            email = st.session_state.get("reset_email")
            updated = update_password(email, new_pw)
            if updated:
                clear_password_reset(email)
                st.success("🎉 Password reset successful!")
                for key in ["reset_step", "reset_email", "otp_cooldown_until"]:
                    st.session_state.pop(key, None)
                st.session_state["auth_mode"] = "login"
                st.rerun()
            else:
                st.error("❌ Failed to update password. Please try again.")

    # ------------------------------------------
    # Back to Login
    # ------------------------------------------
    st.markdown('<div class="auth-switch">', unsafe_allow_html=True)
    if st.button("← Back to Login", key="reset_to_login", use_container_width=True):
        st.session_state["auth_mode"] = "login"
        st.rerun()
    st.markdown(
        """
        <div class="auth-switch-note">
            Forgot which email you used? Try your primary college or work ID first.
        </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------- ROUTER / ENTRY ----------

def main():
    if "auth_mode" not in st.session_state:
        st.session_state["auth_mode"] = "login"

    mode = st.session_state["auth_mode"]

    if mode == "login":
        login()
    elif mode == "signup":
        signup()
    elif mode == "reset":
        reset()
    else:
        # 🔹 When authenticated, show dashboard
        from dashboard import dashboard
        dashboard()


if __name__ == "_main_":
    main()