"""Dark theme styles for the Streamlit app."""

DARK_THEME = """
<style>
    /* Main app background with subtle gradient */
    .stApp {
        background: linear-gradient(to bottom right, #0A0C10, #1A1E24) !important;
        color: #FFFFFF;
    }
    
    /* Sidebar with glass-morphism effect */
    [data-testid="stSidebar"] {
        background: rgba(13, 17, 23, 0.95) !important;
        backdrop-filter: blur(10px) !important;
        -webkit-backdrop-filter: blur(10px) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
        padding: 2rem 1.5rem !important;
    }
    
    /* All text in sidebar should be white */
    [data-testid="stSidebar"] {
        color: #FFFFFF !important;
    }

    [data-testid="stSidebar"] .element-container div {
        color: #FFFFFF !important;
    }

    [data-testid="stSidebar"] label {
        color: #FFFFFF !important;
    }

    [data-testid="stSidebar"] .stSelectbox div {
        color: #FFFFFF !important;
    }
    
    /* Main Title with gradient and text shadow */
    [data-testid="stSidebar"] h1:first-of-type {
        background: linear-gradient(120deg, #FFFFFF, #4A90E2) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        font-size: 2rem !important;
        font-weight: 800 !important;
        letter-spacing: -0.5px !important;
        margin-bottom: 2rem !important;
        text-shadow: 0 0 30px rgba(74, 144, 226, 0.5) !important;
    }
    
    /* Section Headers with accent line */
    [data-testid="stSidebar"] h2,
    .stMarkdown h2 {
        color: #FFFFFF !important;
        font-size: 1.3rem !important;
        font-weight: 600 !important;
        position: relative !important;
        padding-bottom: 8px !important;
        margin: 2rem 0 1rem 0 !important;
    }
    
    [data-testid="stSidebar"] h2::after,
    .stMarkdown h2::after {
        content: "" !important;
        position: absolute !important;
        left: 0 !important;
        bottom: 0 !important;
        width: 50px !important;
        height: 3px !important;
        background: linear-gradient(90deg, #4A90E2, rgba(74, 144, 226, 0)) !important;
        border-radius: 3px !important;
    }
    
    /* Settings expander with hover effect */
    .streamlit-expanderHeader {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        padding: 1rem !important;
        transition: all 0.3s ease !important;
    }
    
    .streamlit-expanderHeader:hover {
        background: rgba(255, 255, 255, 0.1) !important;
        border-color: rgba(74, 144, 226, 0.5) !important;
        transform: translateY(-1px) !important;
    }
    
    /* Inputs and Controls */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > select,
    .stTextArea > div > div > textarea {
        background: rgba(30, 34, 39, 0.95) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px !important;
        color: #FFFFFF !important;
        padding: 0.75rem !important;
        transition: all 0.3s ease !important;
    }
    
    /* Select box specific styling */
    .stSelectbox > div > div {
        background: rgba(30, 34, 39, 0.95) !important;
        color: #FFFFFF !important;
    }

    .stSelectbox > div > div > div[data-baseweb="select"] {
        background: rgba(30, 34, 39, 0.95) !important;
    }

    /* Dropdown menu background */
    div[data-baseweb="popover"] {
        background: rgba(30, 34, 39, 0.95) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }

    div[data-baseweb="select"] ul {
        background: rgba(30, 34, 39, 0.95) !important;
    }

    div[data-baseweb="select"] ul li {
        background: rgba(30, 34, 39, 0.95) !important;
        color: #FFFFFF !important;
    }

    div[data-baseweb="select"] ul li:hover {
        background: rgba(74, 144, 226, 0.2) !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div > select:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #4A90E2 !important;
        box-shadow: 0 0 0 1px #4A90E2 !important;
        background: rgba(35, 40, 45, 0.95) !important;
        color: #FFFFFF !important;
    }
    
    /* Buttons with gradient and hover effect */
    .stButton > button {
        background: linear-gradient(90deg, #4A90E2, #64A5E8) !important;
        border: none !important;
        border-radius: 8px !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        padding: 0.75rem 1.5rem !important;
        transition: all 0.3s ease !important;
        opacity: 0.9 !important;
    }
    
    .stButton > button:hover {
        background: linear-gradient(90deg, #357ABD, #4A90E2) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 12px rgba(74, 144, 226, 0.3) !important;
        opacity: 1 !important;
    }
    
    /* Labels with improved visibility */
    .stTextInput label, 
    .stSelectbox label, 
    .stSlider label, 
    .stTextArea label,
    .stCheckbox label {
        color: #FFFFFF !important;
        font-size: 1rem !important;
        font-weight: 500 !important;
        margin-bottom: 0.5rem !important;
        text-shadow: 0 0 10px rgba(255, 255, 255, 0.1) !important;
    }
    
    /* Slider with custom styling */
    .stSlider > div > div {
        background: rgba(255, 255, 255, 0.1) !important;
    }
    
    .stSlider > div > div > div > div {
        background: linear-gradient(90deg, #4A90E2, #64A5E8) !important;
    }
    
    /* Chat messages with modern styling */
    .stChatMessage {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        backdrop-filter: blur(10px) !important;
        -webkit-backdrop-filter: blur(10px) !important;
        margin: 1rem 0 !important;
        padding: 1.5rem !important;
        transition: all 0.3s ease !important;
    }
    
    .stChatMessage:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2) !important;
    }
    
    /* Toast messages with glass effect */
    .stToast {
        background: rgba(13, 17, 23, 0.95) !important;
        backdrop-filter: blur(10px) !important;
        -webkit-backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px !important;
        color: #FFFFFF !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2) !important;
    }
    
    /* Saved chat list items */
    [data-testid="stSidebar"] .row-widget.stButton button {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        margin: 0.5rem 0 !important;
        opacity: 1 !important;
    }
    
    [data-testid="stSidebar"] .row-widget.stButton button:hover {
        background: rgba(74, 144, 226, 0.1) !important;
        border-color: rgba(74, 144, 226, 0.3) !important;
    }
    
    /* Dark mode toggle with custom styling */
    .stCheckbox > div > div > div {
        background: linear-gradient(90deg, #4A90E2, #64A5E8) !important;
    }

    /* Ensure dropdown text is white */
    [data-testid="stSidebar"] .stSelectbox > div > div > div {
        color: #FFFFFF !important;
    }

    [data-testid="stSidebar"] .stSelectbox > div > div > div[data-baseweb="select"] > div {
        color: #FFFFFF !important;
    }

    /* Input fields with white/bright backgrounds need dark text */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > select,
    .stTextArea > div > div > textarea {
        background: rgba(30, 34, 39, 0.95) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px !important;
        color: #FFFFFF !important;
        padding: 0.75rem !important;
        transition: all 0.3s ease !important;
    }

    /* Style for select boxes and dropdowns */
    .stSelectbox > div > div {
        background: rgba(30, 34, 39, 0.95) !important;
        color: #FFFFFF !important;
    }

    /* Dropdown menu styling */
    div[data-baseweb="select"] {
        background: rgba(30, 34, 39, 0.95) !important;
        color: #FFFFFF !important;
    }

    div[data-baseweb="select"] * {
        color: #FFFFFF !important;
    }

    /* Dropdown options */
    div[data-baseweb="popover"] {
        background: rgba(30, 34, 39, 0.95) !important;
    }

    div[data-baseweb="select"] ul {
        background: rgba(30, 34, 39, 0.95) !important;
    }

    div[data-baseweb="select"] ul li {
        background: rgba(30, 34, 39, 0.95) !important;
        color: #FFFFFF !important;
    }

    /* System prompt textarea specific styling */
    .stTextArea textarea {
        background: rgba(30, 34, 39, 0.95) !important;
        color: #FFFFFF !important;
    }

    /* Model selector specific styling */
    .stSelectbox select {
        background: rgba(30, 34, 39, 0.95) !important;
        color: #FFFFFF !important;
    }

    /* Make sure all input placeholders are visible */
    .stTextInput input::placeholder,
    .stTextArea textarea::placeholder {
        color: rgba(255, 255, 255, 0.6) !important;
    }
</style>
""" 