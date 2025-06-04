"""Light theme styles for the Streamlit app."""

LIGHT_THEME = """
<style>
    /* Main app background */
    .stApp {
        background-color: #FFFFFF;
        color: #1E1E1E;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(to bottom, #F8F9FA, #FFFFFF);
        padding: 2rem 1.5rem !important;
        border-right: 1px solid #E6E6E6;
    }

    /* All text in sidebar should be dark */
    [data-testid="stSidebar"] {
        color: #1E1E1E !important;
    }

    [data-testid="stSidebar"] .element-container div {
        color: #1E1E1E !important;
    }

    [data-testid="stSidebar"] label {
        color: #1E1E1E !important;
        font-weight: 500 !important;
    }

    [data-testid="stSidebar"] .stSelectbox div {
        color: #1E1E1E !important;
    }
    
    /* Main Title */
    [data-testid="stSidebar"] h1:first-of-type {
        color: #1E1E1E !important;
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        margin-bottom: 2rem !important;
    }
    
    /* Section Headers */
    [data-testid="stSidebar"] h2,
    .stMarkdown h2 {
        color: #1E1E1E !important;
        font-size: 1.2rem !important;
        font-weight: 600 !important;
        margin: 1.5rem 0 1rem 0 !important;
    }

    /* Inputs and Controls */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > select,
    .stTextArea > div > div > textarea {
        background-color: #FFFFFF;
        border: 1px solid #E6E6E6;
        border-radius: 8px !important;
        padding: 0.75rem !important;
        transition: all 0.3s ease !important;
        color: #1E1E1E !important;
        font-weight: 500 !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div > select:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #4A90E2 !important;
        box-shadow: 0 0 0 1px #4A90E2 !important;
    }
    
    /* Buttons */
    .stButton > button {
        background-color: #4A90E2 !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        opacity: 0.9 !important;
    }
    
    .stButton > button:hover {
        background-color: #357ABD !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 12px rgba(74, 144, 226, 0.2) !important;
        opacity: 1 !important;
    }
    
    /* Chat messages */
    .stChatMessage {
        background-color: #F8F9FA;
        border: 1px solid #E6E6E6;
        border-radius: 12px !important;
        margin: 1rem 0 !important;
        padding: 1.5rem !important;
        transition: all 0.3s ease !important;
    }
    
    .stChatMessage:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05) !important;
    }
    
    /* Toast messages */
    .stToast {
        background-color: #FFFFFF;
        border: 1px solid #E6E6E6;
        border-radius: 8px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important;
    }
    
    /* Saved chat list items */
    [data-testid="stSidebar"] .row-widget.stButton button {
        background-color: #F8F9FA !important;
        border: 1px solid #E6E6E6 !important;
        color: #262730 !important;
        margin: 0.5rem 0 !important;
        opacity: 1 !important;
    }
    
    [data-testid="stSidebar"] .row-widget.stButton button:hover {
        background-color: #4A90E2 !important;
        border-color: #4A90E2 !important;
        color: #FFFFFF !important;
    }

    /* Ensure dropdown text is dark */
    [data-testid="stSidebar"] .stSelectbox > div > div > div {
        color: #1E1E1E !important;
        font-weight: 500 !important;
    }

    [data-testid="stSidebar"] .stSelectbox > div > div > div[data-baseweb="select"] > div {
        color: #1E1E1E !important;
        font-weight: 500 !important;
    }

    /* Dropdown menu items */
    div[data-baseweb="select"] ul li {
        color: #1E1E1E !important;
        font-weight: 500 !important;
    }

    /* Settings expander */
    .streamlit-expanderHeader {
        background-color: #FFFFFF !important;
        color: #1E1E1E !important;
        border-radius: 8px !important;
        padding: 1rem !important;
        font-weight: 600 !important;
        border: 1px solid #E6E6E6 !important;
        transition: all 0.3s ease !important;
    }
    
    .streamlit-expanderHeader:hover {
        background-color: #F8F9FA !important;
        border-color: #D1D1D1 !important;
        transform: translateY(-1px) !important;
    }
</style>
""" 