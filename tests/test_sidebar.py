"""Tests for the sidebar component."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import streamlit as st
from src.components.sidebar import render_sidebar

@pytest.fixture
def mock_streamlit():
    """Mock Streamlit functions."""
    with patch('streamlit.sidebar.title') as mock_title, \
         patch('streamlit.sidebar.expander') as mock_expander, \
         patch('streamlit.sidebar.divider') as mock_divider, \
         patch('streamlit.sidebar.subheader') as mock_subheader, \
         patch('streamlit.sidebar.columns') as mock_columns, \
         patch('streamlit.selectbox') as mock_selectbox, \
         patch('streamlit.slider') as mock_slider, \
         patch('streamlit.text_area') as mock_text_area, \
         patch('streamlit.toggle') as mock_toggle, \
         patch('streamlit.button') as mock_button:
        
        # Configure mock expander to return a context manager
        mock_expander_context = MagicMock()
        mock_expander_context.selectbox = mock_selectbox
        mock_expander_context.slider = mock_slider
        mock_expander_context.text_area = mock_text_area
        mock_expander_context.toggle = mock_toggle
        mock_expander_context.button = mock_button
        
        mock_expander.return_value = MagicMock(
            __enter__=lambda x: mock_expander_context,
            __exit__=lambda x, y, z, w: None
        )
        
        # Configure mock columns to return a list of column objects
        mock_col1, mock_col2 = MagicMock(), MagicMock()
        mock_col1.__enter__ = lambda x: mock_col1
        mock_col1.__exit__ = lambda x, y, z, w: None
        mock_col2.__enter__ = lambda x: mock_col2
        mock_col2.__exit__ = lambda x, y, z, w: None
        mock_columns.return_value = [mock_col1, mock_col2]
        
        yield {
            'title': mock_title,
            'expander': mock_expander,
            'expander_context': mock_expander_context,
            'divider': mock_divider,
            'subheader': mock_subheader,
            'columns': mock_columns,
            'col1': mock_col1,
            'col2': mock_col2,
            'selectbox': mock_selectbox,
            'slider': mock_slider,
            'text_area': mock_text_area,
            'toggle': mock_toggle,
            'button': mock_button
        }

@pytest.fixture
def mock_callbacks():
    """Mock callback functions."""
    return {
        'on_settings_change': Mock(),
        'on_new_chat': Mock(),
        'on_save_chat': Mock(),
        'on_load_chat': Mock(),
        'on_delete_chat': Mock()
    }

@pytest.fixture
def mock_current_settings():
    """Mock current settings."""
    return {
        'model': 'gpt-3.5-turbo',
        'temperature': 0.7,
        'system_prompt': 'You are a test assistant',
        'theme': 'light'
    }

def test_render_sidebar_initial_render(mock_streamlit, mock_callbacks, mock_current_settings):
    """Test initial rendering of sidebar."""
    saved_chats = []
    
    render_sidebar(
        on_settings_change=mock_callbacks['on_settings_change'],
        on_new_chat=mock_callbacks['on_new_chat'],
        on_save_chat=mock_callbacks['on_save_chat'],
        on_load_chat=mock_callbacks['on_load_chat'],
        on_delete_chat=mock_callbacks['on_delete_chat'],
        saved_chats=saved_chats,
        current_settings=mock_current_settings
    )
    
    # Verify title is rendered
    mock_streamlit['title'].assert_called_once_with("Databricks AI Chatbot")
    
    # Verify settings expander is created
    mock_streamlit['expander'].assert_called_once_with("⚙️ Settings", expanded=False)
    
    # Verify chat management section is rendered
    assert any('Chat Management' in str(call[0][0]) 
              for call in mock_streamlit['subheader'].call_args_list)

def test_render_sidebar_with_saved_chats(mock_streamlit, mock_callbacks, mock_current_settings):
    """Test rendering sidebar with saved chats."""
    saved_chats = [
        {'id': '123', 'name': 'Chat 1'},
        {'id': '456', 'name': 'Chat 2'}
    ]
    
    render_sidebar(
        on_settings_change=mock_callbacks['on_settings_change'],
        on_new_chat=mock_callbacks['on_new_chat'],
        on_save_chat=mock_callbacks['on_save_chat'],
        on_load_chat=mock_callbacks['on_load_chat'],
        on_delete_chat=mock_callbacks['on_delete_chat'],
        saved_chats=saved_chats,
        current_settings=mock_current_settings
    )
    
    # Verify saved chats section is rendered
    assert any('Saved Chats' in str(call[0][0]) 
              for call in mock_streamlit['subheader'].call_args_list)

def test_render_sidebar_settings_change(mock_streamlit, mock_callbacks, mock_current_settings):
    """Test settings change in sidebar."""
    saved_chats = []
    
    # Configure mock settings inputs
    mock_streamlit['selectbox'].return_value = "gpt-4"
    mock_streamlit['slider'].return_value = 0.5
    mock_streamlit['text_area'].return_value = "New prompt"
    mock_streamlit['toggle'].return_value = True
    mock_streamlit['button'].return_value = True
    
    render_sidebar(
        on_settings_change=mock_callbacks['on_settings_change'],
        on_new_chat=mock_callbacks['on_new_chat'],
        on_save_chat=mock_callbacks['on_save_chat'],
        on_load_chat=mock_callbacks['on_load_chat'],
        on_delete_chat=mock_callbacks['on_delete_chat'],
        saved_chats=saved_chats,
        current_settings=mock_current_settings
    )
    
    # Verify settings change callback is called with new values
    mock_callbacks['on_settings_change'].assert_called_once_with(
        "gpt-4",  # model
        0.5,      # temperature
        "New prompt",  # system_prompt
        True      # theme
    )

def test_render_sidebar_chat_management(mock_streamlit, mock_callbacks, mock_current_settings):
    """Test chat management buttons in sidebar."""
    saved_chats = []
    
    # Configure mock buttons in columns
    mock_streamlit['col1'].button.return_value = True  # New Chat
    mock_streamlit['col2'].button.return_value = True  # Save Chat
    
    render_sidebar(
        on_settings_change=mock_callbacks['on_settings_change'],
        on_new_chat=mock_callbacks['on_new_chat'],
        on_save_chat=mock_callbacks['on_save_chat'],
        on_load_chat=mock_callbacks['on_load_chat'],
        on_delete_chat=mock_callbacks['on_delete_chat'],
        saved_chats=saved_chats,
        current_settings=mock_current_settings
    )
    
    # Verify chat management callbacks are called
    mock_callbacks['on_new_chat'].assert_called_once()
    mock_callbacks['on_save_chat'].assert_called_once() 