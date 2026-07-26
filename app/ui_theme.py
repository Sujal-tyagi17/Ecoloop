import streamlit as st

def apply_custom_theme():
    """Applies modern dark glassmorphism theme with custom CSS styling."""
    st.markdown("""
        <style>
        /* Main background and fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        .main {
            background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
            color: #f8fafc;
        }

        /* Glassmorphism Card Header */
        .header-card {
            background: rgba(30, 41, 59, 0.7);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
        }

        .header-title {
            font-size: 2.2rem;
            font-weight: 700;
            background: linear-gradient(90deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 0;
        }

        .header-subtitle {
            color: #94a3b8;
            font-size: 1.05rem;
            margin-top: 6px;
        }

        /* Metric Cards */
        .metric-card {
            background: rgba(30, 41, 59, 0.6);
            backdrop-filter: blur(8px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 18px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
            transition: transform 0.2s ease;
        }

        .metric-card:hover {
            transform: translateY(-3px);
            border-color: rgba(56, 189, 248, 0.4);
        }

        .metric-value {
            font-size: 1.9rem;
            font-weight: 700;
            color: #38bdf8;
        }

        .metric-label {
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #94a3b8;
            margin-top: 4px;
        }

        .metric-badge-green {
            background: rgba(34, 197, 94, 0.2);
            color: #4ade80;
            border: 1px solid rgba(34, 197, 94, 0.3);
            border-radius: 20px;
            padding: 3px 10px;
            font-size: 0.8rem;
            font-weight: 600;
            display: inline-block;
            margin-top: 6px;
        }

        .metric-badge-blue {
            background: rgba(56, 189, 248, 0.2);
            color: #38bdf8;
            border: 1px solid rgba(56, 189, 248, 0.3);
            border-radius: 20px;
            padding: 3px 10px;
            font-size: 0.8rem;
            font-weight: 600;
            display: inline-block;
            margin-top: 6px;
        }

        /* Status Badge */
        .status-badge-active {
            background: rgba(16, 185, 129, 0.15);
            color: #10b981;
            border: 1px solid rgba(16, 185, 129, 0.4);
            border-radius: 30px;
            padding: 6px 16px;
            font-weight: 600;
            font-size: 0.9rem;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }

        .pulse-dot {
            width: 8px;
            height: 8px;
            background-color: #10b981;
            border-radius: 50%;
            display: inline-block;
            box-shadow: 0 0 10px #10b981;
        }

        /* Tabs styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 12px;
        }

        .stTabs [data-baseweb="tab"] {
            background: rgba(30, 41, 59, 0.5);
            border-radius: 8px;
            color: #94a3b8;
            padding: 10px 20px;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }

        .stTabs [aria-selected="true"] {
            background: rgba(56, 189, 248, 0.15) !important;
            color: #38bdf8 !important;
            border-color: rgba(56, 189, 248, 0.4) !important;
            font-weight: 600;
        }

        </style>
    """, unsafe_allow_html=True)
