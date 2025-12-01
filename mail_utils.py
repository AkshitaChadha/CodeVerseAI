import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os

def welcome_mail(user_email, username):
    sender_email = os.getenv("SENDER_EMAIL")
    app_password =os.getenv("APP_PASSWORD")

    subject = "Welcome to CodeVerse AI 🚀"
    text_content = f"Hi {username}, welcome to CodeVerse AI! We're thrilled to have you with us."
    html_content = f"""
    <html>
  <body style="font-family: 'Segoe UI', Arial, sans-serif; background-color: #f4f6fb; margin: 0; padding: 0;">
    <table align="center" width="600" cellpadding="0" cellspacing="0" 
           style="background: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin-top: 30px;">
      <tr>
        <td style="background: linear-gradient(90deg, #4a90e2, #6a5acd); padding: 24px; text-align: center;">
          <h1 style="color: #ffffff; font-size: 28px; margin: 0; letter-spacing: 1px;">🚀 Welcome to <span style="font-weight: 600;">CodeVerse AI</span></h1>
        </td>
      </tr>
      <tr>
        <td style="padding: 30px;">
          <p style="font-size: 16px; color: #333;">Hey <b>{username}</b>,</p>
          <p style="font-size: 16px; color: #444; line-height: 1.6;">
            Welcome aboard! We're thrilled to have you join the <b>CodeVerse AI</b> community — a space where 
            innovation meets intelligence. Whether you're exploring AI-powered debugging, smart documentation, 
            or real-time collaboration, you’re now part of a growing network of creators who make code come alive. 💡
          </p>
          <p style="font-size: 16px; color: #444; line-height: 1.6;">
            Start your journey by logging in and trying out the tools built just for you.  
            The dashboard awaits with smart assistants ready to help you code better, faster, and smarter.
          </p>

          <div style="text-align: center; margin-top: 30px;">
            <a href="https://codeverseai.streamlit.app/~/+/?login"
               style="background: #4a90e2; color: white; padding: 12px 30px; 
                      border-radius: 8px; text-decoration: none; font-weight: 600;">
              Launch Dashboard
            </a>
          </div>

          <p style="margin-top: 40px; color: #666; font-size: 14px; text-align: center;">
            Let’s build something extraordinary together.  
            <br>— The <b>CodeVerse AI</b> Team 🧠💻
          </p>
        </td>
      </tr>
      <tr>
        <td style="background-color: #f0f2f8; padding: 16px; text-align: center; font-size: 13px; color: #777;">
          © 2025 CodeVerse AI. All rights reserved.<br>
          Crafted with 💙 by the CodeVerse Team.
        </td>
      </tr>
    </table>
  </body>
</html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = user_email

    msg.attach(MIMEText(text_content, "plain"))
    msg.attach(MIMEText(html_content, "html"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, app_password)
            server.sendmail(sender_email, user_email, msg.as_string())
        print(f"✅ Mail sent successfully to {user_email}")
    except Exception as e:
        print("❌ Error sending email:", e)


def send_otp_mail(user_email, otp_code: str):
    """Send password reset OTP email."""
    sender_email = "team.codeverseai@gmail.com"
    app_password = "fplrvoodbrycrous"

    subject = "CodeVerse AI - Password Reset OTP"
    text_content = f"Your CodeVerse AI password reset OTP is {otp_code}. It is valid for 5 minutes."

    html_content = f"""
    <html>
      <body style="font-family: 'Segoe UI', Arial, sans-serif; background-color: #f4f6fb; margin: 0; padding: 0;">
        <table align="center" width="600" cellpadding="0" cellspacing="0" 
               style="background: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin-top: 30px;">
          <tr>
            <td style="background: linear-gradient(90deg, #3A66FF, #2D58E0); padding: 24px; text-align: center;">
              <h1 style="color: #ffffff; font-size: 24px; margin: 0;">Password Reset OTP</h1>
            </td>
          </tr>
          <tr>
            <td style="padding: 30px;">
              <p style="font-size: 16px; color: #333;">Hi,</p>
              <p style="font-size: 16px; color: #444; line-height: 1.6;">
                We received a request to reset your <b>CodeVerse AI</b> account password.
              </p>
              <p style="font-size: 16px; color: #444; line-height: 1.6; text-align:center;">
                Your OTP code is:
              </p>
              <p style="font-size: 32px; font-weight: 700; color: #3A66FF; text-align:center; letter-spacing: 4px;">
                {otp_code}
              </p>
              <p style="font-size: 14px; color: #777; text-align:center;">
                This OTP is valid for <b>5 minutes</b>. If you did not request a password reset, you can safely ignore this email.
              </p>
            </td>
          </tr>
          <tr>
            <td style="background-color: #f0f2f8; padding: 16px; text-align: center; font-size: 13px; color: #777;">
              © 2025 CodeVerse AI. All rights reserved.
            </td>
          </tr>
        </table>
      </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = user_email

    msg.attach(MIMEText(text_content, "plain"))
    msg.attach(MIMEText(html_content, "html"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, app_password)
            server.sendmail(sender_email, user_email, msg.as_string())
        print(f"✅ OTP email sent successfully to {user_email}")
    except Exception as e:
        print("❌ Error sending OTP email:", e)
