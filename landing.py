import streamlit as st
from base64 import b64encode
import os


# --- 1. Inject Custom CSS ---
def inject_custom_css():
    """Injects custom CSS for CodeVerse AI landing page"""
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
        
        /* Color Variables */
        :root {
            --dark-bg: #0f172a;
            --darker-bg: #0a0f1c;
            --card-bg: #1e293b;
            --accent-blue: #3b82f6;
            --accent-purple: #8b5cf6;
            --accent-cyan: #06b6d4;
            --text-primary: #f8fafc;
            --text-secondary: #cbd5e1;
            --text-muted: #94a3b8;
            --border-color: #334155;
            --gradient-primary: linear-gradient(135deg, #8b5cf6 0%, #3b82f6 100%);
        }
        
        /* Streamlit Defaults Removal */
        .stApp > header { display: none !important; }
        #MainMenu, footer { visibility: hidden; }
        .stApp { margin-top: 20px !important; background: var(--darker-bg); }
        .block-container, .main, .viewerBadge_container__1QSob, .css-1dp5vir, .css-hxt7ib { 
            padding: 0 !important; margin: 0 !important; max-width: 100% !important; 
        }
        
        /* Global Styles */
        .stApp {
            font-family: 'Inter', sans-serif;
            overflow-x: hidden;
            color: var(--text-primary);
        }
        
        a { text-decoration: none !important; }
        
        /* Animations */
        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-10px); }
        }
        .floating { animation: float 6s ease-in-out infinite; }
        
        /* Navbar */
        .navbar {
            margin-top: 40px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1.5rem 5rem;
            background: rgba(15, 23, 42, 0.95);
            backdrop-filter: blur(10px);
            position: sticky;
            top: 0;
            z-index: 100;
            border-bottom: 1px solid var(--border-color);
        }
        
        .navbar-brand {
            display: flex;
            flex-direction: column;
            align-items: flex-start;
        }
        
        .brand-main {
            font-size: 28px !important;
            font-weight: 800 !important;
            background: linear-gradient(135deg, #61dafb, #bd93f9) !important;
            -webkit-background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
            margin-bottom: 2px !important;
            line-height: 1;
        }
        
        .brand-subtitle {
            font-size: 12px !important;
            color: #bd93f9 !important;
            font-weight: 500 !important;
            letter-spacing: 0.5px;
        }
        
        .navbar-right { 
            display: flex; 
            align-items: center;
            gap: 25px;
        }
        
        .nav-link { 
            color: var(--text-primary) !important; 
            font-size: 0.95rem; 
            transition: 0.25s;
            font-weight: 500;
        }
        .nav-link:hover { color: var(--accent-cyan) !important; }
        
        .nav-btn-primary, .nav-btn-secondary {
            padding: 10px 22px; 
            border-radius: 30px; 
            font-weight: 600; 
            cursor: pointer; 
            transition: 0.3s;
            font-size: 0.9rem;
            font-family: 'Inter', sans-serif;
        }
        
        .nav-btn-primary { 
            background: var(--gradient-primary);
            color: white !important; 
            box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4);
        }
        .nav-btn-primary:hover { 
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(59, 130, 246, 0.6);
        }
        
        .nav-btn-secondary { 
            border: 2px solid var(--border-color); 
            background: transparent; 
            color: var(--text-primary) !important;
        }
        .nav-btn-secondary:hover {
            border-color: var(--accent-blue);
            background: rgba(59, 130, 246, 0.1);
        }
        
        /* Hero Section */
        .hero {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 4rem 5rem 6rem;
            background: var(--dark-bg);
            min-height: 85vh;
            position: relative;
            overflow: hidden;
        }
        
        .hero:before {
            content: '';
            position: absolute;
            width: 600px;
            height: 600px;
            border-radius: 50%;
            background: var(--gradient-primary);
            opacity: 0.1;
            filter: blur(100px);
            top: -300px;
            right: -200px;
            z-index: 0;
        }
        
        .hero-left { 
            position: relative; 
            z-index: 1; 
            max-width: 600px; 
        }
        
        .hero-left h2 { 
            font-size: 3.5rem; 
            font-weight: 900; 
            line-height: 1.5; 
            margin-bottom: 1.5rem;
        }
        
        .hero-left p { 
            font-size: 1.3rem; 
            color: var(--text-secondary); 
            margin-bottom: 2.5rem; 
            line-height: 1.6;
        }
        
        .btn-primary {
            background: var(--gradient-primary); 
            padding: 15px 35px; 
            border-radius: 30px;
            font-weight: 600; 
            cursor: pointer; 
            transition: 0.3s;
            border: none;
            color: white !important;
            font-size: 1rem;
            box-shadow: 0 4px 15px rgba(139, 92, 246, 0.4);
            display: inline-block;
        }
        .btn-primary:hover { 
            transform: translateY(-3px);
            box-shadow: 0 10px 25px rgba(139, 92, 246, 0.6);
        }
        
        .hero-right { position: relative; z-index: 1; }
        
        .code-visual {
            background: var(--card-bg);
            border-radius: 15px;
            padding: 2rem;
            border: 1px solid var(--border-color);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
            max-width: 500px;
        }
        
        .code-header {
            display: flex;
            gap: 10px;
            margin-bottom: 1.5rem;
        }
        
        .code-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
        }
        .dot-red { background: #ef4444; }
        .dot-yellow { background: #eab308; }
        .dot-green { background: #22c55e; }
        
        .code-content {
            background: #0f172a;
            border-radius: 10px;
            padding: 1.5rem;
            border: 1px solid var(--border-color);
            font-family: 'Courier New', monospace;
        }
        
        .code-line { margin-bottom: 0.5rem; color: var(--text-secondary); }
        .code-comment { color: #64748b; }
        .code-keyword { color: #3b82f6; }
        .code-string { color: #10b981; }
        .code-function { color: #8b5cf6; }
        
        /* Stats Section */
        .stats-section {
            display: flex;
            justify-content: space-around;
            padding: 3rem 5rem;
            background: var(--card-bg);
            border-top: 1px solid var(--border-color);
            border-bottom: 1px solid var(--border-color);
        }
        
        .stat-item { text-align: center; }
        
        .stat-number {
            font-size: 2.5rem;
            font-weight: 800;
            background: var(--gradient-primary);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        }
        
        .stat-label {
            color: var(--text-secondary);
            font-size: 1rem;
            font-weight: 500;
        }
        
        /* About Section */
        .simple-about {
            padding: 6rem 5rem;
            background: var(--dark-bg);
            position: relative;
            text-align: center;
        }

        .about-container {
            display: flex;
            justify-content: center;
            align-items: center;
        }

        .about-content {
            width: 100%;
            max-width: 900px;
        }

        .about-content h3 {
            font-size: 2.8rem;
            margin-bottom: 2rem;
            font-weight: 800;
        }

        .about-desc {
            font-size: 1.3rem;
            color: var(--text-secondary);
            line-height: 1.7;
            margin-bottom: 3rem;
        }

        .stats {
            display: flex;
            justify-content: center;
            gap: 3rem;
        }

        .stat { text-align: center; }

        /* Features Section */
        .feature-section { 
            display: flex; 
            justify-content: space-around; 
            padding: 5rem 5rem; 
            background: var(--card-bg);
            gap: 2rem;
        }
        
        .feature { 
            flex: 1;
            text-align: center;
            padding: 2.5rem 2rem;
            border-radius: 20px;
            background: var(--dark-bg);
            border: 1px solid var(--border-color);
            transition: 0.3s;
        }
        
        .feature:hover {
            transform: translateY(-10px);
            border-color: var(--accent-blue);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
        }
        
        .feature-icon-main {
            font-size: 3rem;
            margin-bottom: 1.5rem;
            background: var(--gradient-primary);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .feature h4 { 
            margin-bottom: 1rem;
            font-size: 1.4rem;
            font-weight: 700;
        }
        
        .feature p {
            color: var(--text-secondary);
            line-height: 1.6;
            font-size: 1rem;
        }
        
        /* Testimonials Section */
        .testimonials-section {
            padding: 5rem 5rem;
            background: var(--dark-bg);
            text-align: center;
        }
        
        .testimonials-section h3 {
            font-size: 2.5rem;
            margin-bottom: 3rem;
        }
        
        .testimonials-container {
            display: flex;
            justify-content: space-between;
            gap: 2rem;
        }
        
        .testimonial {
            background: var(--card-bg);
            padding: 2.5rem;
            border-radius: 20px;
            text-align: left;
            border: 1px solid var(--border-color);
            flex: 1;
        }
        
        .testimonial-text {
            color: var(--text-secondary);
            font-style: italic;
            margin-bottom: 1.5rem;
            line-height: 1.6;
        }
        
        .testimonial-author {
            display: flex;
            align-items: center;
        }
        
        .author-avatar {
            width: 50px;
            height: 50px;
            border-radius: 50%;
            background: var(--gradient-primary);
            margin-right: 1rem;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
        }
        
        .author-info h5 { margin: 0; font-weight: 600; }
        .author-info p { margin: 0; color: var(--text-muted); font-size: 0.9rem; }
        
        /* CTA Section */
        .cta-section {
            padding: 8rem 5rem;
            text-align: center;
            background: var(--gradient-primary);
            color: white;
            position: relative;
            overflow: hidden;
        }
        
        .cta-section:before, .cta-section:after {
            content: '';
            position: absolute;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.1);
        }
        
        .cta-section:before {
            width: 300px; height: 300px;
            top: -150px; right: -100px;
        }
        
        .cta-section:after {
            width: 200px; height: 200px;
            bottom: -100px; left: -50px;
        }
        
        .cta-content { position: relative; z-index: 2; }
        
        .ai-facts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
            margin-top: 4rem;
            text-align: left;
        }
        
        .ai-fact {
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(10px);
            padding: 2rem;
            border-radius: 15px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: all 0.3s ease;
            text-align: center;
        }
        
        .ai-fact:hover {
            transform: translateY(-5px);
            background: rgba(255, 255, 255, 0.2);
        }
        
        .fact-icon { font-size: 2.5rem; margin-bottom: 1rem; }
        .fact-text { font-size: 1.2rem; font-weight: 600; margin-bottom: 0.8rem; line-height: 1.4; }
        .fact-subtext { font-size: 0.9rem; opacity: 0.9; font-style: italic; line-height: 1.6; }
        
        /* Footer */
        .footer {
            padding: 3rem 5rem 2rem;
            background: var(--darker-bg);
            color: var(--text-secondary);
            border-top: 1px solid var(--border-color);
        }
        
        .footer-content {
            display: flex;
            justify-content: space-between;
            margin-bottom: 3rem;
        }
        
        .footer-column { flex: 1; }
        .footer-column h4 { margin-bottom: 1.5rem; font-size: 1.2rem; }
        
        .footer-links {
            list-style: none;
            padding: 0;
        }
        
        .footer-links li { margin-bottom: 0.8rem; }
        .footer-links a { color: var(--text-secondary); transition: 0.3s; }
        .footer-links a:hover { color: var(--accent-cyan); }
        
        .footer-bottom {
            text-align: center;
            padding-top: 2rem;
            border-top: 1px solid var(--border-color);
            font-size: 0.9rem;
            color: var(--text-muted);
        }
        </style>
    """, unsafe_allow_html=True)


# --- 2. Landing Page ---
def app_main():
    st.set_page_config(page_title="CodeVerse AI", layout="wide", initial_sidebar_state="collapsed")
    inject_custom_css()
        
    # Navbar Section
    st.markdown("""
        <div class="navbar">
            <div class="navbar-brand">
                <div class="brand-main">CodeVerse AI</div>
                <div class="brand-subtitle">Collaborative Code Editor</div>
            </div>
            <div class="navbar-right">
                <a href="#" class="nav-link">About</a>
                <a href="#" class="nav-link">Features</a>
                <a href="#" class="nav-link">Contact</a>
                <a href="?login" class="nav-btn-secondary">Login</a>
                <a href="?signup" class="nav-btn-primary">Get Started</a>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Hero Section
    st.markdown("""
        <div class="hero">
            <div class="hero-left">
                <h2>Collaborate Smarter <br>Code Better <br>That’s CodeVerse AI
</h2>
                <p>Write, optimize, and debug together — with AI intelligence that keeps everyone aligned. The new era of collaboration has arrived.</p>
                <a href="?signup" class="btn-primary">Start Coding</a>
            </div>
            <div class="hero-right">
                <div class="code-visual floating">
                    <div class="code-header">
                        <div class="code-dot dot-red"></div>
                        <div class="code-dot dot-yellow"></div>
                        <div class="code-dot dot-green"></div>
                    </div>
                    <div class="code-content">
                        <div class="code-line"><span class="code-keyword">function</span> <span class="code-function">quickSort</span>(arr) {</div>
                        <div class="code-line">&nbsp;&nbsp;<span class="code-keyword">if</span> (arr.length <= 1) <span class="code-keyword">return</span> arr;</div>
                        <div class="code-line">&nbsp;&nbsp;<span class="code-keyword">const</span> pivot = arr[0];</div>
                        <div class="code-line">&nbsp;&nbsp;<span class="code-keyword">const</span> left = [];</div>
                        <div class="code-line">&nbsp;&nbsp;<span class="code-keyword">const</span> right = [];</div>
                        <div class="code-line">&nbsp;&nbsp;<span class="code-comment">// AI suggested optimization</span></div>
                        <div class="code-line">&nbsp;&nbsp;<span class="code-keyword">for</span> (<span class="code-keyword">let</span> i = 1; i < arr.length; i++) {</div>
                        <div class="code-line">&nbsp;&nbsp;&nbsp;&nbsp;arr[i] < pivot ? left.push(arr[i]) : right.push(arr[i]);</div>
                        <div class="code-line">&nbsp;&nbsp;}</div>
                        <div class="code-line">&nbsp;&nbsp;<span class="code-keyword">return</span> [...quickSort(left), pivot, ...quickSort(right)];</div>
                        <div class="code-line">}</div>
                    </div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Stats Section
    st.markdown("""
        <div class="stats-section">
            <div class="stat-item">
                <div class="stat-number">68%</div>
                <div class="stat-label">Faster Coding</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">60%</div>
                <div class="stat-label">Team Boost</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">24/7</div>
                <div class="stat-label">AI Availability</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">87%</div>
                <div class="stat-label">Less Bugs</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # About Section
    st.markdown("""
    <div class="simple-about">
        <div class="about-container">
            <div class="about-content">
                <h3>Why CodeVerse AI Stands Out</h3>
                <p class="about-desc">
                    We're not just another collaborative editor — we're your AI-powered coding teammate. CodeVerse keeps everyone in sync, understands your project context, adapts to your workflow, and helps your team solve problems faster. From classroom assignments to real-world software builds, every developer levels up — together.
                </p>
                <div class="stats">
                    <div class="stat">
                        <div class="stat-number">10x</div>
                        <div class="stat-label">Faster Development</div>
                    </div>
                    <div class="stat">
                        <div class="stat-number">92%</div>
                        <div class="stat-label">Code Accuracy</div>
                    </div>
                    <div class="stat">
                        <div class="stat-number">24/7</div>
                        <div class="stat-label">AI Assistance</div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Features Section
    st.markdown("""
        <div class="feature-section">
            <div class="feature">
                <div class="feature-icon-main">⚡</div>
                <h4>AI-Powered Coding</h4>
                <p>Get smart suggestions, automatic debugging, and code explanations powered by advanced AI models.</p>
            </div>
            <div class="feature">
                <div class="feature-icon-main">🌍</div>
                <h4>Team Collaboration</h4>
                <p>Work with your team in real-time, share projects, and review code seamlessly.</p>
            </div>
            <div class="feature">
                <div class="feature-icon-main">🔒</div>
                <h4>Secure & Reliable</h4>
                <p>Built with enterprise-grade encryption and robust cloud infrastructure.</p>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Testimonials Section
    st.markdown("""
        <div class="testimonials-section">
            <h3>What Developers Say</h3>
            <div class="testimonials-container">
                <div class="testimonial">
                    <div class="testimonial-text">
                        "CodeVerse AI has completely transformed how I approach coding. The AI suggestions are incredibly accurate and have cut my development time in half."
                    </div>
                    <div class="testimonial-author">
                        <div class="author-avatar">SJ</div>
                        <div class="author-info">
                            <h5>Sarah Johnson</h5>
                            <p>Senior Full-Stack Developer</p>
                        </div>
                    </div>
                </div>
                <div class="testimonial">
                    <div class="testimonial-text">
                        "As a coding bootcamp instructor, I recommend CodeVerse AI to all my students. It's like having a personal tutor available 24/7."
                    </div>
                    <div class="testimonial-author">
                        <div class="author-avatar">MR</div>
                        <div class="author-info">
                            <h5>Michael Rodriguez</h5>
                            <p>Lead Instructor at DevAcademy</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # CTA Section
    st.markdown("""
        <div class="cta-section">
            <div class="cta-content">
                <div class="ai-facts-grid">
                    <div class="ai-fact">
                        <div class="fact-icon">🚀</div>
                        <div class="fact-text">10x Faster Code Generation</div>
                        <div class="fact-subtext">AI completes functions, classes, and entire modules in seconds instead of hours.</div>
                    </div>
                    <div class="ai-fact">
                        <div class="fact-icon">🔍</div>
                        <div class="fact-text">87% Fewer Bugs & Errors</div>
                        <div class="fact-subtext">Real-time code analysis detects syntax errors and security vulnerabilities.</div>
                    </div>
                    <div class="ai-fact">
                        <div class="fact-icon">⚡</div>
                        <div class="fact-text">68% Faster Project Completion</div>
                        <div class="fact-subtext">From MVP to production-ready code with smart refactoring and documentation.</div>
                    </div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Footer Section
    st.markdown("""
        <div class="footer">
            <div class="footer-content">
                <div class="footer-column">
                    <h4>CodeVerse AI</h4>
                    <p>Empowering developers with AI-powered tools to code faster, smarter, and better.</p>
                </div>
                <div class="footer-column">
                    <h4>Product</h4>
                    <ul class="footer-links">
                        <li><a href="#">Features</a></li>
                        <li><a href="#">Pricing</a></li>
                        <li><a href="#">Documentation</a></li>
                    </ul>
                </div>
                <div class="footer-column">
                    <h4>Company</h4>
                    <ul class="footer-links">
                        <li><a href="#">About</a></li>
                        <li><a href="#">Blog</a></li>
                        <li><a href="#">Careers</a></li>
                    </ul>
                </div>
                <div class="footer-column">
                    <h4>Legal</h4>
                    <ul class="footer-links">
                        <li><a href="#">Privacy Policy</a></li>
                        <li><a href="#">Terms of Service</a></li>
                    </ul>
                </div>
            </div>
            <div class="footer-bottom">
                <p>&copy; 2023 CodeVerse AI. All rights reserved.</p>
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