"""Tests for the theme components."""

import pytest
from src.styles.dark_theme import DARK_THEME
from src.styles.light_theme import LIGHT_THEME

def test_dark_theme_structure():
    """Test dark theme CSS structure."""
    assert isinstance(DARK_THEME, str)
    assert DARK_THEME.strip().startswith('<style>')
    assert DARK_THEME.strip().endswith('</style>')
    
    # Check for essential dark theme properties
    assert 'background: linear-gradient(to bottom right, #0A0C10, #1A1E24)' in DARK_THEME  # Dark background
    assert 'color: #FFFFFF' in DARK_THEME  # Light text
    assert '.stApp' in DARK_THEME  # Main app container
    assert '[data-testid="stSidebar"]' in DARK_THEME  # Sidebar styling

def test_light_theme_structure():
    """Test light theme CSS structure."""
    assert isinstance(LIGHT_THEME, str)
    assert LIGHT_THEME.strip().startswith('<style>')
    assert LIGHT_THEME.strip().endswith('</style>')
    
    # Check for essential light theme properties
    assert 'background-color: #FFFFFF' in LIGHT_THEME  # Light background
    assert 'color: #1E1E1E' in LIGHT_THEME  # Dark text
    assert '.stApp' in LIGHT_THEME  # Main app container
    assert '[data-testid="stSidebar"]' in LIGHT_THEME  # Sidebar styling

def test_theme_button_styles():
    """Test button styles in both themes."""
    # Dark theme buttons
    assert '.stButton > button' in DARK_THEME
    assert 'background: linear-gradient(90deg, #4A90E2, #64A5E8)' in DARK_THEME  # Primary button color
    assert 'color: #FFFFFF' in DARK_THEME  # Button text color
    
    # Light theme buttons
    assert '.stButton > button' in LIGHT_THEME
    assert 'background-color: #4A90E2' in LIGHT_THEME  # Primary button color
    assert 'color: #FFFFFF' in LIGHT_THEME  # Button text color

def test_theme_input_styles():
    """Test input field styles in both themes."""
    # Dark theme inputs
    assert '.stTextInput > div > div > input' in DARK_THEME
    assert '.stTextArea > div > div > textarea' in DARK_THEME
    assert '.stSelectbox > div > div > select' in DARK_THEME
    assert 'background: rgba(30, 34, 39, 0.95)' in DARK_THEME  # Dark input background
    
    # Light theme inputs
    assert '.stTextInput > div > div > input' in LIGHT_THEME
    assert '.stTextArea > div > div > textarea' in LIGHT_THEME
    assert '.stSelectbox > div > div > select' in LIGHT_THEME
    assert 'background-color: #FFFFFF' in LIGHT_THEME  # Light input background

def test_theme_chat_message_styles():
    """Test chat message styles in both themes."""
    # Dark theme chat messages
    assert '.stChatMessage' in DARK_THEME
    assert 'background: rgba(255, 255, 255, 0.05)' in DARK_THEME  # Dark chat background
    assert 'border-radius: 12px' in DARK_THEME
    assert 'transition: all 0.3s ease' in DARK_THEME
    
    # Light theme chat messages
    assert '.stChatMessage' in LIGHT_THEME
    assert 'background-color: #F8F9FA' in LIGHT_THEME  # Light chat background
    assert 'border-radius: 12px' in LIGHT_THEME
    assert 'transition: all 0.3s ease' in LIGHT_THEME

def test_theme_hover_effects():
    """Test hover effects in both themes."""
    # Dark theme hover effects
    assert ':hover' in DARK_THEME
    assert 'transform: translateY' in DARK_THEME
    assert 'box-shadow' in DARK_THEME
    assert 'background: rgba(255, 255, 255, 0.1)' in DARK_THEME  # Dark hover background
    
    # Light theme hover effects
    assert ':hover' in LIGHT_THEME
    assert 'transform: translateY' in LIGHT_THEME
    assert 'box-shadow' in LIGHT_THEME
    assert 'background-color: #F8F9FA' in LIGHT_THEME  # Light hover background 