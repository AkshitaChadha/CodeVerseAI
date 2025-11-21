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

def st_errors_style():
    st.markdown("""
    <style>
    .stAlert{
        border-radius: 10px !important;
        font-weight: 600 !important;
    }
    .stAlert div[role="alert"]{
        background-color: #D32F2F !important;
        border-color: #B71C1C !important;
        color:white !important;
    }
    </style>
    """, unsafe_allow_html=True)

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

        /* ---- CENTER CARD ---- */
        
        .auth-title {
            font-size: 2.3rem;
            font-weight: 900;
            text-align: center;
            margin-bottom: 1.8rem;
        }

        /* ---- INPUT FIELDS ---- */
        div[data-testid="stTextInput"] input {
            background-color: rgba(255,255,255,0.95);
            border-radius: 12px;
            border: none;
            height: 48px;
            font-size: 1rem;
            color: #001A43;
            padding-left: 14px;
        }
        div[data-testid="stTextInput"] > label > div > p {
            color: #D7E2FF !important;
            font-size: 0.9rem;
            font-weight: 600;
        }

        /* ---- MAIN SUBMIT BUTTON ---- */
        div.stButton>button {
            width: 100%;
            height: 48px;
            font-size: 1rem;
            border-radius: 12px;
            background: linear-gradient(90deg, #3A66FF, #2D58E0);
            font-weight: 700;
        }

        div.stButton>button:hover {
            transform: translateY(-2px);
            background: linear-gradient(90deg, #2D58E0, #3A66FF);
            box-shadow: 0 0 12px rgba(58,102,255,0.5);
        }

        /* ---- LINK BUTTON ---- */
        .link-btn > button {
            background: transparent !important;
            border: none !important;
            color: #9EC1FF !important;
            text-decoration: underline;
            font-size: .9rem;
            margin-top: 1rem;
        }
        .link-btn > button:hover {
            opacity: .8;
        }
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
    st_errors_style()

    with centered_container():
        st.markdown('<div class="auth-title">Create Account</div>', unsafe_allow_html=True)

        # 🧾 Input Form (NO submit button inside)
        with st.form("signup_form", clear_on_submit=False):
            username = st.text_input("Username")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            confirm = st.text_input("Confirm Password", type="password")

            form_submitted = st.form_submit_button("✓ Hidden Submit", disabled=True)  
            # hidden / disabled just to enable form validation structure

        # 🎨 Styled Main Submit Button
        sign_btn = st.button("Sign Up")

        if sign_btn:
            # Validate Fields
            if not username or not email or not password or not confirm:
                st.error("All fields are required")
                return
            
            if "@" not in email or "." not in email:
                st.error("Please enter a valid email address")
                return
            
            if len(password) < 6:
                st.error("Password must be at least 6 characters long")
                return
            
            if password != confirm:
                st.error("Passwords do not match")
                return
            
            existing_user = find_user_by_email(email)
            if existing_user:
                st.warning("Email already registered")
                return

            # Insert User in DB
            success = insert_user(username, email, password)

            if success:
                try:
                    welcome_mail(email, username)
                except Exception as e:
                    print("Mail sending failed:", e)

                st.success("Account created successfully!")
                st.session_state["auth_mode"] = "login"
                st.rerun()
            else:
                st.error("Signup failed! Try again")
                return

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Already have an account? Login"):
            st.session_state["auth_mode"] = "login"
            st.rerun()



# --- LOGIN ---
def login():
    inject_auth_css()
    st_errors_style()
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
            if not email or not password:
                st.error("Please enter both email and password.")
                return
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
    st_errors_style()
    if "reset_step" not in st.session_state:
        st.session_state["reset_step"] = "email"

    step = st.session_state["reset_step"]

    with centered_container(): 
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
