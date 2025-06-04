"""Tests for the chat interface component."""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
import streamlit as st
from src.components.chat_interface import render_chat_interface

@pytest.fixture
def mock_streamlit():
    """Mock Streamlit functions."""
    with patch('streamlit.markdown') as mock_markdown, \
         patch('streamlit.divider') as mock_divider, \
         patch('streamlit.chat_message') as mock_chat_message, \
         patch('streamlit.chat_input') as mock_chat_input, \
         patch('streamlit.spinner') as mock_spinner:
        
        # Create a single chat context that will be reused
        mock_chat_context = MagicMock()
        
        # Configure mock chat_message to always return the same context
        def get_chat_context(*args, **kwargs):
            return MagicMock(
                __enter__=lambda x: mock_chat_context,
                __exit__=lambda x, y, z, w: None
            )
        mock_chat_message.side_effect = get_chat_context
        
        # Configure mock spinner to return a context manager
        mock_spinner_context = MagicMock()
        mock_spinner.return_value = MagicMock(
            __enter__=lambda x: mock_spinner_context,
            __exit__=lambda x, y, z, w: None
        )
        
        yield {
            'markdown': mock_markdown,
            'divider': mock_divider,
            'chat_message': mock_chat_message,
            'chat_input': mock_chat_input,
            'spinner': mock_spinner,
            'chat_context': mock_chat_context,
            'spinner_context': mock_spinner_context
        }

def test_render_chat_interface_initial_render(mock_streamlit):
    """Test initial rendering of chat interface."""
    messages = []
    on_message = Mock()
    
    render_chat_interface(messages, on_message)
    
    # Verify welcome message and title are rendered
    assert any('Welcome to Databricks AI Assistant' in str(call[0][0]) 
              for call in mock_streamlit['markdown'].call_args_list)
    
    # Verify divider is added
    mock_streamlit['divider'].assert_called_once()
    
    # Verify chat input is rendered
    mock_streamlit['chat_input'].assert_called_once_with("Type your message here...")

def test_render_chat_interface_with_messages(mock_streamlit):
    """Test rendering chat interface with existing messages."""
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"}
    ]
    on_message = Mock()
    
    render_chat_interface(messages, on_message)
    
    # Verify each message is rendered with correct role
    mock_streamlit['chat_message'].assert_has_calls([
        call("user"),
        call("assistant")
    ], any_order=True)
    
    # Verify message content is rendered
    mock_streamlit['markdown'].assert_has_calls([
        call("Hello"),
        call("Hi there!")
    ], any_order=True)

def test_render_chat_interface_new_message(mock_streamlit):
    """Test handling new message input."""
    messages = []
    on_message = Mock()
    
    # Simulate user input
    mock_streamlit['chat_input'].return_value = "Test message"
    
    render_chat_interface(messages, on_message)
    
    # Verify user message is displayed
    mock_streamlit['chat_message'].assert_any_call("user")
    
    # Verify message content is rendered
    mock_streamlit['markdown'].assert_any_call("Test message")
    
    # Verify spinner is shown while getting response
    mock_streamlit['spinner'].assert_called_once_with("Thinking and searching...")
    
    # Verify on_message callback is called
    on_message.assert_called_once_with("Test message")

def test_render_chat_interface_no_input(mock_streamlit):
    """Test chat interface when no input is provided."""
    messages = []
    on_message = Mock()
    
    # Simulate no user input
    mock_streamlit['chat_input'].return_value = None
    
    render_chat_interface(messages, on_message)
    
    # Verify on_message is not called
    on_message.assert_not_called()
    
    # Verify no new messages are displayed
    assert not any(call[0][0] == "user" for call in mock_streamlit['chat_message'].call_args_list) 