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
    main,
    get_openai_api_key
)
import os

class MockSessionState(dict):
    """Mock Streamlit session state."""
    def __init__(self, **kwargs):
        super().__init__()
        for key, value in kwargs.items():
            self[key] = value

    def __getattr__(self, key):
        if key not in self:
            return None
        return self[key]

    def __setattr__(self, key, value):
        self[key] = value

@pytest.fixture
def mock_streamlit():
    """Mock Streamlit functionality."""
    session_state = MockSessionState()
    return {
        'session_state': session_state,
        'set_page_config': MagicMock(),
        'markdown': MagicMock(),
        'rerun': MagicMock(),
        'toast': MagicMock()
    }

@pytest.fixture
def mock_services():
    """Mock service classes and instances."""
    return {
        'agent_service_class': MagicMock(),
        'agent_service': Mock(),
        'chat_service_class': MagicMock(),
        'chat_service': Mock()
    }

@pytest.fixture
def mock_dbutils():
    """Mock Databricks dbutils functionality."""
    mock = MagicMock()
    mock.secrets.get.return_value = "test-key"
    return mock

@pytest.fixture
def mock_components():
    """Mock UI components."""
    with patch('src.components.sidebar.render_sidebar') as mock_render_sidebar, \
         patch('src.components.chat_interface.render_chat_interface') as mock_render_chat_interface:
        yield {
            'render_sidebar': mock_render_sidebar,
            'render_chat_interface': mock_render_chat_interface
        }

@pytest.fixture(autouse=True)
def setup_streamlit(mock_streamlit):
    """Setup Streamlit mocks for all tests."""
    with patch('streamlit.session_state', mock_streamlit['session_state']), \
         patch('streamlit.set_page_config', mock_streamlit['set_page_config']), \
         patch('streamlit.markdown', mock_streamlit['markdown']), \
         patch('streamlit.rerun', mock_streamlit['rerun']), \
         patch('streamlit.toast', mock_streamlit['toast']):
        yield

@pytest.fixture(autouse=True)
def mock_streamlit_module():
    """Mock Streamlit module for all tests."""
    with patch('streamlit.set_page_config'), \
         patch('streamlit.markdown'), \
         patch('streamlit.sidebar.title'):
        yield

@pytest.fixture(autouse=True)
def mock_streamlit_script_runner():
    """Mock Streamlit script runner context."""
    script_run_ctx = Mock()
    script_run_ctx.sidebar = Mock()
    script_run_ctx.sidebar.title = Mock()
    script_run_ctx.sidebar.expander = Mock()
    script_run_ctx.sidebar.expander.return_value = Mock(__enter__=Mock(), __exit__=Mock())
    script_run_ctx.sidebar.divider = Mock()
    script_run_ctx.sidebar.subheader = Mock()
    
    # Create column mocks with context manager support
    col1 = Mock(__enter__=Mock(), __exit__=Mock())
    col2 = Mock(__enter__=Mock(), __exit__=Mock())
    script_run_ctx.sidebar.columns = Mock(return_value=[col1, col2])
    
    with patch('streamlit.runtime.scriptrunner.add_script_run_ctx'), \
         patch('streamlit.runtime.scriptrunner.get_script_run_ctx', return_value=script_run_ctx), \
         patch('streamlit.runtime.state.session_state_proxy.SessionStateProxy', return_value=Mock()), \
         patch('streamlit.sidebar', script_run_ctx.sidebar), \
         patch('streamlit.selectbox', Mock(return_value="gpt-3.5-turbo")), \
         patch('streamlit.slider', Mock(return_value=0.7)), \
         patch('streamlit.text_area', Mock(return_value="Test prompt")), \
         patch('streamlit.subheader', Mock()), \
         patch('streamlit.toggle', Mock(return_value=False)), \
         patch('streamlit.button', Mock(return_value=False)):
        yield

def test_initialize_session_state(mock_streamlit, mock_services):
    """Test session state initialization."""
    # Mock environment variables and service creation
    with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}), \
         patch('src.app.AgentService', return_value=mock_services['agent_service']), \
         patch('src.app.ChatService', return_value=mock_services['chat_service']), \
         patch('src.app.get_openai_api_key', return_value='test-key'):

        initialize_session_state()

        # Verify session state initialization
        assert mock_streamlit['session_state'].messages == []
        assert isinstance(mock_streamlit['session_state'].chat_id, str)
        assert mock_streamlit['session_state'].chat_name is None
        assert mock_streamlit['session_state'].model == "gpt-3.5-turbo"
        assert mock_streamlit['session_state'].temperature == 0.7
        assert mock_streamlit['session_state'].system_prompt == "You are a helpful Databricks AI assistant. You have access to tools that can help you provide more accurate and up-to-date information."
        assert mock_streamlit['session_state'].theme == "light"
        assert mock_streamlit['session_state'].agent_service == mock_services['agent_service']
        assert mock_streamlit['session_state'].chat_service == mock_services['chat_service']

def test_handle_settings_change(mock_streamlit):
    """Test settings change handler."""
    # Setup session state
    mock_streamlit['session_state'].agent_service = Mock()
    
    # Call function
    handle_settings_change("gpt-4", 0.8, "New prompt", True)
    
    # Verify state changes
    assert mock_streamlit['session_state'].model == "gpt-4"
    assert mock_streamlit['session_state'].temperature == 0.8
    assert mock_streamlit['session_state'].system_prompt == "New prompt"
    assert mock_streamlit['session_state'].theme == "dark"
    
    # Verify agent service update
    mock_streamlit['session_state'].agent_service.update_configuration.assert_called_once_with(
        model_name="gpt-4",
        temperature=0.8,
        system_prompt="New prompt"
    )
    mock_streamlit['rerun'].assert_called_once()

def test_handle_new_chat(mock_streamlit):
    """Test new chat handler."""
    # Setup session state
    mock_streamlit['session_state'].messages = []
    
    # Call function
    handle_new_chat()
    
    # Verify state reset
    assert mock_streamlit['session_state'].messages == []
    assert isinstance(mock_streamlit['session_state'].chat_id, str)
    assert mock_streamlit['session_state'].chat_name is None
    mock_streamlit['rerun'].assert_called_once()

def test_handle_save_chat(mock_streamlit):
    """Test chat save handler."""
    # Setup session state
    mock_streamlit['session_state'].chat_service = Mock()
    mock_streamlit['session_state'].chat_id = "test_id"
    mock_streamlit['session_state'].chat_name = "Test Chat"
    mock_streamlit['session_state'].messages = ["test message"]
    
    # Call function
    handle_save_chat()
    
    # Verify chat service call
    mock_streamlit['session_state'].chat_service.save_chat.assert_called_once_with(
        "test_id",
        "Test Chat",
        ["test message"]
    )
    mock_streamlit['toast'].assert_called_once()

def test_handle_load_chat(mock_streamlit):
    """Test chat load handler."""
    # Setup session state
    mock_streamlit['session_state'].chat_service = Mock()
    mock_streamlit['session_state'].chat_service.load_chat.return_value = ("Test Chat", ["test message"])
    
    # Call function
    handle_load_chat("test_id")
    
    # Verify state changes
    assert mock_streamlit['session_state'].chat_id == "test_id"
    assert mock_streamlit['session_state'].chat_name == "Test Chat"
    assert mock_streamlit['session_state'].messages == ["test message"]
    mock_streamlit['rerun'].assert_called_once()

def test_handle_delete_chat_current(mock_streamlit):
    """Test delete handler for current chat."""
    # Setup session state
    mock_streamlit['session_state'].chat_service = Mock()
    mock_streamlit['session_state'].chat_id = "test_id"
    
    # Reset rerun mock to clear any previous calls
    mock_streamlit['rerun'].reset_mock()
    
    # Call function
    handle_delete_chat("test_id")
    
    # Verify chat service call and state reset
    mock_streamlit['session_state'].chat_service.delete_chat.assert_called_once_with("test_id")
    assert mock_streamlit['session_state'].messages == []
    assert mock_streamlit['session_state'].chat_name is None
    assert isinstance(mock_streamlit['session_state'].chat_id, str)
    mock_streamlit['rerun'].assert_called_once()

def test_handle_delete_chat_other(mock_streamlit):
    """Test delete handler for other chat."""
    # Setup session state
    mock_streamlit['session_state'].chat_service = Mock()
    mock_streamlit['session_state'].chat_id = "current_id"
    
    # Call function
    handle_delete_chat("other_id")
    
    # Verify chat service call without state reset
    mock_streamlit['session_state'].chat_service.delete_chat.assert_called_once_with("other_id")
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
    
    # Call function
    handle_message("Hello")
    
    # Verify message handling
    assert len(mock_streamlit['session_state'].messages) == 2
    assert mock_streamlit['session_state'].messages[0] == {"role": "user", "content": "Hello"}
    assert mock_streamlit['session_state'].messages[1] == {"role": "assistant", "content": "Assistant response"}
    assert mock_streamlit['session_state'].chat_name == "Generated Name"

def test_handle_message_subsequent(mock_streamlit):
    """Test message handler for subsequent messages."""
    # Setup session state
    mock_streamlit['session_state'].messages = [{"role": "user", "content": "Previous"}]
    mock_streamlit['session_state'].chat_name = "Existing Chat"
    mock_streamlit['session_state'].chat_service = Mock()
    mock_streamlit['session_state'].agent_service = Mock()
    mock_streamlit['session_state'].agent_service.get_response.return_value = "Assistant response"
    
    # Call function
    handle_message("Hello")
    
    # Verify message handling
    assert len(mock_streamlit['session_state'].messages) == 3
    assert mock_streamlit['session_state'].messages[-2] == {"role": "user", "content": "Hello"}
    assert mock_streamlit['session_state'].messages[-1] == {"role": "assistant", "content": "Assistant response"}
    assert mock_streamlit['session_state'].chat_name == "Existing Chat"

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
    
    # Verify chat name generation and message handling
    assert mock_streamlit['session_state'].chat_name == "Generated Chat Name"
    assert len(mock_streamlit['session_state'].messages) == 2
    assert mock_streamlit['session_state'].messages[0] == {"role": "user", "content": "Hello"}
    assert mock_streamlit['session_state'].messages[1] == {"role": "assistant", "content": "Assistant response"}

def test_main(mock_streamlit, mock_components):
    """Test main application function."""
    # Setup session state
    mock_session_state = MockSessionState()
    mock_session_state.theme = "light"
    mock_session_state.chat_service = Mock()
    mock_session_state.chat_service.get_saved_chats.return_value = []
    mock_session_state.messages = []
    mock_session_state.model = "gpt-3.5-turbo"
    mock_session_state.temperature = 0.7
    mock_session_state.system_prompt = "Test prompt"
    mock_session_state.agent_service = Mock()
    
    # Create column mocks with context manager support
    col1 = Mock(__enter__=Mock(), __exit__=Mock())
    col2 = Mock(__enter__=Mock(), __exit__=Mock())
    
    # Mock Streamlit module
    with patch('streamlit.session_state', mock_session_state), \
         patch('src.app.render_sidebar', mock_components['render_sidebar']), \
         patch('src.app.render_chat_interface', mock_components['render_chat_interface']), \
         patch('src.app.get_openai_api_key', return_value='test-key'), \
         patch('src.app.configure_page') as mock_configure_page, \
         patch('src.app.initialize_session_state') as mock_initialize_session_state, \
         patch('streamlit.markdown') as mock_markdown, \
         patch('src.styles.light_theme.LIGHT_THEME', 'light-theme-css'), \
         patch('src.styles.dark_theme.DARK_THEME', 'dark-theme-css'):
        
        # Call main
        main()
        
        # Verify main functionality
        mock_configure_page.assert_called_once()
        mock_initialize_session_state.assert_called_once()
        mock_markdown.assert_any_call('light-theme-css', unsafe_allow_html=True)
        mock_components['render_sidebar'].assert_called_once_with(
            on_settings_change=handle_settings_change,
            on_new_chat=handle_new_chat,
            on_save_chat=handle_save_chat,
            on_load_chat=handle_load_chat,
            on_delete_chat=handle_delete_chat,
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
            on_message=handle_message
        )

def test_get_openai_api_key_from_secrets():
    """Test getting OpenAI API key from Databricks secrets."""
    mock_dbutils = MagicMock()
    mock_dbutils.secrets.get.return_value = "test-key"
    mock_runtime = MagicMock()
    mock_runtime.dbutils = mock_dbutils
    
    with patch.dict('sys.modules', {'databricks.sdk.runtime': mock_runtime}), \
         patch.dict('os.environ', clear=True):
        api_key = get_openai_api_key()
        assert api_key == "test-key"
        mock_dbutils.secrets.get.assert_called_once_with(scope="RAG-demo-scope", key="openai_api_key")

def test_get_openai_api_key_from_env():
    """Test getting OpenAI API key from environment variables."""
    with patch.dict('os.environ', {'OPENAI_API_KEY': 'env-test-key'}), \
         patch.dict('sys.modules', {'databricks.sdk.runtime': None}):
        api_key = get_openai_api_key()
        assert api_key == "env-test-key"

def test_get_openai_api_key_missing():
    """Test error when OpenAI API key is missing."""
    with patch.dict('os.environ', clear=True), \
         patch.dict('sys.modules', {'databricks.sdk.runtime': None}):
        with pytest.raises(ValueError):
            get_openai_api_key()

def test_initialize_session_state_with_theme():
    """Test session state initialization with theme."""
    mock_session_state = MockSessionState()
    with patch('streamlit.session_state', mock_session_state), \
         patch('src.app.AgentService') as mock_agent_service, \
         patch('src.app.ChatService') as mock_chat_service, \
         patch('src.app.get_openai_api_key', return_value='test-key'):
        
        # Create mock service instances
        mock_agent_service_instance = Mock()
        mock_chat_service_instance = Mock()
        mock_agent_service.return_value = mock_agent_service_instance
        mock_chat_service.return_value = mock_chat_service_instance
        
        initialize_session_state()
        
        # Verify state initialization
        assert mock_session_state.theme == "light"
        assert mock_session_state.messages == []
        assert mock_session_state.model == "gpt-3.5-turbo"
        assert mock_session_state.temperature == 0.7
        assert mock_session_state.system_prompt == "You are a helpful Databricks AI assistant. You have access to tools that can help you provide more accurate and up-to-date information."
        assert mock_session_state.agent_service == mock_agent_service_instance
        assert mock_session_state.chat_service == mock_chat_service_instance

def test_handle_settings_change_with_theme():
    """Test settings change with theme."""
    with patch('streamlit.session_state', Mock()) as mock_session_state, \
         patch('streamlit.rerun') as mock_rerun:
        # Call the function
        handle_settings_change(
            model="gpt-4",
            temperature=0.5,
            system_prompt="Test prompt",
            dark_mode=True
        )
        
        # Verify state changes
        assert mock_session_state.model == "gpt-4"
        assert mock_session_state.temperature == 0.5
        assert mock_session_state.system_prompt == "Test prompt"
        assert mock_session_state.theme == "dark"
        
        # Verify agent service update
        mock_session_state.agent_service.update_configuration.assert_called_once_with(
            model_name="gpt-4",
            temperature=0.5,
            system_prompt="Test prompt"
        )
        
        # Verify rerun
        mock_rerun.assert_called_once()

def test_theme_application():
    """Test theme application."""
    mock_session_state = MockSessionState()
    mock_session_state.chat_service = Mock()
    mock_session_state.chat_service.get_saved_chats.return_value = []
    mock_session_state.messages = []
    mock_session_state.model = "gpt-3.5-turbo"
    mock_session_state.temperature = 0.7
    mock_session_state.system_prompt = "Test prompt"
    mock_session_state.agent_service = Mock()
    
    with patch('streamlit.session_state', mock_session_state), \
         patch('streamlit.markdown') as mock_markdown, \
         patch('streamlit.set_page_config') as mock_set_page_config, \
         patch('src.components.sidebar.render_sidebar', Mock()), \
         patch('src.components.chat_interface.render_chat_interface', Mock()), \
         patch('src.app.get_openai_api_key', return_value='test-key'), \
         patch('streamlit.sidebar.title', Mock()), \
         patch('src.styles.light_theme.LIGHT_THEME', 'light-theme-css'), \
         patch('src.styles.dark_theme.DARK_THEME', 'dark-theme-css'):
        
        # Test light theme
        mock_session_state.theme = "light"
        main()
        mock_markdown.assert_any_call('light-theme-css', unsafe_allow_html=True)
        
        # Reset mocks
        mock_markdown.reset_mock()
        mock_set_page_config.reset_mock()
        
        # Test dark theme
        mock_session_state.theme = "dark"
        main()
        mock_markdown.assert_any_call('dark-theme-css', unsafe_allow_html=True) 