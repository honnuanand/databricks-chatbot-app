"""Tests for the main application."""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
import streamlit as st
from datetime import datetime
from src.app import (
    initialize_session_state,
    handle_settings_change,
    handle_new_chat,
    handle_save_chat,
    handle_load_chat,
    handle_delete_chat,
    handle_message,
    main
)
import os

class MockSessionState(dict):
    """Mock Streamlit session state."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__ = self
    
    def __getattr__(self, key):
        if key not in self:
            return None
        return self[key]
    
    def __setattr__(self, key, value):
        self[key] = value

@pytest.fixture
def mock_streamlit():
    """Mock Streamlit functions."""
    with patch('streamlit.session_state', new_callable=MockSessionState) as mock_session_state, \
         patch('streamlit.set_page_config') as mock_set_page_config, \
         patch('streamlit.markdown') as mock_markdown, \
         patch('streamlit.toast') as mock_toast, \
         patch('streamlit.rerun') as mock_rerun:
        
        yield {
            'session_state': mock_session_state,
            'set_page_config': mock_set_page_config,
            'markdown': mock_markdown,
            'toast': mock_toast,
            'rerun': mock_rerun
        }

@pytest.fixture
def mock_services():
    """Mock chat and agent services."""
    with patch('src.services.chat_service.ChatService') as mock_chat_service_class, \
         patch('src.services.agent_service.AgentService') as mock_agent_service_class:
        
        mock_chat_service = Mock()
        mock_agent_service = Mock()
        
        mock_chat_service_class.return_value = mock_chat_service
        mock_agent_service_class.return_value = mock_agent_service
        
        yield {
            'chat_service': mock_chat_service,
            'agent_service': mock_agent_service,
            'chat_service_class': mock_chat_service_class,
            'agent_service_class': mock_agent_service_class
        }

@pytest.fixture
def mock_components():
    """Mock UI components."""
    with patch('src.components.sidebar.render_sidebar') as mock_render_sidebar, \
         patch('src.components.chat_interface.render_chat_interface') as mock_render_chat_interface:
        yield {
            'render_sidebar': mock_render_sidebar,
            'render_chat_interface': mock_render_chat_interface
        }

def test_initialize_session_state(mock_streamlit, mock_services):
    """Test session state initialization."""
    # Mock environment variables and service creation
    with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}), \
         patch('src.app.AgentService', return_value=mock_services['agent_service']), \
         patch('src.app.ChatService', return_value=mock_services['chat_service']):
        
        initialize_session_state()
        
        # Verify session state variables are initialized
        assert mock_streamlit['session_state'].messages == []
        assert isinstance(mock_streamlit['session_state'].chat_id, str)
        assert mock_streamlit['session_state'].chat_name is None
        assert mock_streamlit['session_state'].model == "gpt-3.5-turbo"
        assert mock_streamlit['session_state'].temperature == 0.7
        assert "You are a helpful Databricks AI assistant" in mock_streamlit['session_state'].system_prompt
        assert mock_streamlit['session_state'].theme == "light"
        
        # Verify services are initialized
        assert mock_streamlit['session_state'].agent_service == mock_services['agent_service']
        assert mock_streamlit['session_state'].chat_service == mock_services['chat_service']

def test_handle_settings_change(mock_streamlit, mock_services):
    """Test settings change handler."""
    # Setup session state
    mock_streamlit['session_state'].agent_service = mock_services['agent_service']
    
    # Call handler
    handle_settings_change(
        model="gpt-4",
        temperature=0.8,
        system_prompt="New prompt",
        dark_mode=True
    )
    
    # Verify state updates
    assert mock_streamlit['session_state'].model == "gpt-4"
    assert mock_streamlit['session_state'].temperature == 0.8
    assert mock_streamlit['session_state'].system_prompt == "New prompt"
    assert mock_streamlit['session_state'].theme == "dark"
    
    # Verify agent service is updated
    mock_services['agent_service'].update_configuration.assert_called_once_with(
        model_name="gpt-4",
        temperature=0.8,
        system_prompt="New prompt"
    )
    
    # Verify app rerun
    mock_streamlit['rerun'].assert_called_once()

def test_handle_new_chat(mock_streamlit):
    """Test new chat handler."""
    # Setup session state
    mock_streamlit['session_state'].messages = ["old message"]
    mock_streamlit['session_state'].chat_name = "Old Chat"
    
    handle_new_chat()
    
    # Verify state reset
    assert mock_streamlit['session_state'].messages == []
    assert mock_streamlit['session_state'].chat_name is None
    assert isinstance(mock_streamlit['session_state'].chat_id, str)
    
    # Verify app rerun
    mock_streamlit['rerun'].assert_called_once()

def test_handle_save_chat(mock_streamlit):
    """Test chat save handler."""
    # Setup session state
    mock_streamlit['session_state'].chat_service = Mock()
    mock_streamlit['session_state'].chat_id = "test_id"
    mock_streamlit['session_state'].chat_name = "Test Chat"
    mock_streamlit['session_state'].messages = ["test message"]
    
    handle_save_chat()
    
    # Verify chat service call
    mock_streamlit['session_state'].chat_service.save_chat.assert_called_once_with(
        "test_id",
        "Test Chat",
        ["test message"]
    )
    
    # Verify success toast
    mock_streamlit['toast'].assert_called_once_with("Chat saved successfully!", icon="✅")

def test_handle_load_chat(mock_streamlit):
    """Test chat load handler."""
    # Setup session state
    mock_streamlit['session_state'].chat_service = Mock()
    mock_streamlit['session_state'].chat_service.load_chat.return_value = ("Test Chat", ["test message"])
    
    handle_load_chat("test_id")
    
    # Verify state updates
    assert mock_streamlit['session_state'].chat_id == "test_id"
    assert mock_streamlit['session_state'].chat_name == "Test Chat"
    assert mock_streamlit['session_state'].messages == ["test message"]
    
    # Verify chat service call
    mock_streamlit['session_state'].chat_service.load_chat.assert_called_once_with("test_id")
    
    # Verify app rerun
    mock_streamlit['rerun'].assert_called_once()

def test_handle_delete_chat_current(mock_streamlit):
    """Test delete handler for current chat."""
    # Setup session state
    mock_streamlit['session_state'].chat_service = Mock()
    mock_streamlit['session_state'].chat_id = "test_id"
    
    # Reset rerun mock to clear any previous calls
    mock_streamlit['rerun'].reset_mock()
    
    handle_delete_chat("test_id")
    
    # Verify chat service call
    mock_streamlit['session_state'].chat_service.delete_chat.assert_called_once_with("test_id")
    
    # Verify state reset (new chat)
    assert mock_streamlit['session_state'].messages == []
    assert mock_streamlit['session_state'].chat_name is None
    assert isinstance(mock_streamlit['session_state'].chat_id, str)
    
    # Verify app rerun
    mock_streamlit['rerun'].assert_called_once()

def test_handle_delete_chat_other(mock_streamlit):
    """Test delete handler for other chat."""
    # Setup session state
    mock_streamlit['session_state'].chat_service = Mock()
    mock_streamlit['session_state'].chat_id = "current_id"
    
    handle_delete_chat("other_id")
    
    # Verify chat service call
    mock_streamlit['session_state'].chat_service.delete_chat.assert_called_once_with("other_id")
    
    # Verify current chat remains unchanged
    assert mock_streamlit['session_state'].chat_id == "current_id"
    
    # Verify app rerun
    mock_streamlit['rerun'].assert_called_once()

def test_handle_message_first(mock_streamlit):
    """Test message handler for first message."""
    # Setup session state
    mock_streamlit['session_state'].messages = []
    mock_streamlit['session_state'].chat_name = None
    mock_streamlit['session_state'].chat_service = Mock()
    mock_streamlit['session_state'].agent_service = Mock()
    mock_streamlit['session_state'].agent_service.get_response.return_value = "Assistant response"
    mock_streamlit['session_state'].chat_service.generate_chat_name.return_value = "Generated Name"
    
    handle_message("Hello")
    
    # Verify chat name generation
    mock_streamlit['session_state'].chat_service.generate_chat_name.assert_called_once()
    assert mock_streamlit['session_state'].chat_name == "Generated Name"
    
    # Verify message handling
    assert mock_streamlit['session_state'].messages == [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Assistant response"}
    ]
    
    # Verify auto-save
    mock_streamlit['session_state'].chat_service.save_chat.assert_called_once()

def test_handle_message_subsequent(mock_streamlit):
    """Test message handler for subsequent messages."""
    # Setup session state
    mock_streamlit['session_state'].messages = [{"role": "user", "content": "Previous"}]
    mock_streamlit['session_state'].chat_name = "Existing Chat"
    mock_streamlit['session_state'].chat_service = Mock()
    mock_streamlit['session_state'].agent_service = Mock()
    mock_streamlit['session_state'].agent_service.get_response.return_value = "Assistant response"
    
    handle_message("Hello")
    
    # Verify no chat name generation
    mock_streamlit['session_state'].chat_service.generate_chat_name.assert_not_called()
    assert mock_streamlit['session_state'].chat_name == "Existing Chat"
    
    # Verify message handling
    assert mock_streamlit['session_state'].messages[-2:] == [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Assistant response"}
    ]
    
    # Verify auto-save
    mock_streamlit['session_state'].chat_service.save_chat.assert_called_once()

def test_handle_message_first_with_name_generation(mock_streamlit):
    """Test handling first message with chat name generation."""
    # Setup
    mock_streamlit['session_state'].messages = []
    mock_streamlit['session_state'].chat_name = None
    mock_streamlit['session_state'].chat_service = Mock()
    mock_streamlit['session_state'].agent_service = Mock()
    mock_streamlit['session_state'].agent_service.get_response.return_value = "Assistant response"
    mock_streamlit['session_state'].chat_service.generate_chat_name.return_value = "Generated Chat Name"
    
    # Call function
    handle_message("Hello")
    
    # Verify chat name generation
    mock_streamlit['session_state'].chat_service.generate_chat_name.assert_called_once_with(
        "Hello",
        mock_streamlit['session_state'].agent_service.agent_executor.agent.llm
    )
    assert mock_streamlit['session_state'].chat_name == "Generated Chat Name"
    
    # Verify message handling
    assert mock_streamlit['session_state'].messages == [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Assistant response"}
    ]
    
    # Verify auto-save
    mock_streamlit['session_state'].chat_service.save_chat.assert_called_once()

def test_main(mock_streamlit, mock_components):
    """Test main application function."""
    # Setup session state
    mock_streamlit['session_state'].theme = "light"
    mock_streamlit['session_state'].chat_service = Mock()
    mock_streamlit['session_state'].chat_service.get_saved_chats.return_value = []
    mock_streamlit['session_state'].messages = []
    mock_streamlit['session_state'].model = "gpt-3.5-turbo"
    mock_streamlit['session_state'].temperature = 0.7
    mock_streamlit['session_state'].system_prompt = "Test prompt"
    
    # Mock Streamlit context and functions
    with patch('streamlit.markdown', mock_streamlit['markdown']), \
         patch('streamlit.set_page_config', mock_streamlit['set_page_config']), \
         patch('streamlit.session_state', mock_streamlit['session_state']), \
         patch('src.components.sidebar.render_sidebar', mock_components['render_sidebar']), \
         patch('src.components.chat_interface.render_chat_interface', mock_components['render_chat_interface']):
        
        # Import and reload the module to ensure mocks are in place
        import importlib
        import src.app
        importlib.reload(src.app)
        
        # Now call main
        src.app.main()
    
    # Verify theme application
    mock_streamlit['markdown'].assert_called()
    
    # Verify component rendering
    mock_components['render_sidebar'].assert_called_once_with(
        on_settings_change=src.app.handle_settings_change,
        on_new_chat=src.app.handle_new_chat,
        on_save_chat=src.app.handle_save_chat,
        on_load_chat=src.app.handle_load_chat,
        on_delete_chat=src.app.handle_delete_chat,
        saved_chats=[],
        current_settings={
            "model": "gpt-3.5-turbo",
            "temperature": 0.7,
            "system_prompt": "Test prompt",
            "theme": "light"
        }
    )
    mock_components['render_chat_interface'].assert_called_once_with(
        messages=[],
        on_message=src.app.handle_message
    ) 