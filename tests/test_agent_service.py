import pytest
from unittest.mock import Mock, patch
from src.services.agent_service import AgentService

@pytest.fixture
def mock_openai_key():
    return "test-key-123"

@pytest.fixture
def agent_service(mock_openai_key):
    with patch('langchain_openai.ChatOpenAI') as mock_chat:
        # Configure the mock
        mock_chat.return_value = Mock()
        return AgentService(
            model_name="gpt-3.5-turbo",
            temperature=0.7,
            system_prompt="You are a test assistant",
            openai_api_key=mock_openai_key
        )

def test_agent_service_initialization(agent_service):
    """Test if AgentService initializes with correct attributes."""
    assert agent_service.model_name == "gpt-3.5-turbo"
    assert agent_service.temperature == 0.7
    assert agent_service.system_prompt == "You are a test assistant"
    assert agent_service.memory is not None
    assert agent_service.agent_executor is not None

def test_agent_service_initialization_with_invalid_temperature():
    """Test initialization with invalid temperature."""
    with pytest.raises(ValueError):
        AgentService(
            model_name="gpt-3.5-turbo",
            temperature=2.0,  # Invalid temperature > 1.0
            system_prompt="Test",
            openai_api_key="test-key"
        )
    
    with pytest.raises(ValueError):
        AgentService(
            model_name="gpt-3.5-turbo",
            temperature=-1.0,  # Invalid temperature < 0.0
            system_prompt="Test",
            openai_api_key="test-key"
        )

def test_update_configuration(agent_service):
    """Test if configuration updates correctly."""
    with patch('langchain_openai.ChatOpenAI') as mock_chat:
        # Configure the mock
        mock_chat.return_value = Mock()
        
        agent_service.update_configuration(
            model_name="gpt-4",
            temperature=0.5,
            system_prompt="New prompt"
        )
        
        assert agent_service.model_name == "gpt-4"
        assert agent_service.temperature == 0.5
        assert agent_service.system_prompt == "New prompt"

def test_update_configuration_partial(agent_service):
    """Test partial configuration updates."""
    original_model = agent_service.model_name
    original_temp = agent_service.temperature
    original_prompt = agent_service.system_prompt
    
    # Update only temperature
    agent_service.update_configuration(temperature=0.3)
    assert agent_service.model_name == original_model
    assert agent_service.temperature == 0.3
    assert agent_service.system_prompt == original_prompt
    
    # Update only system prompt
    agent_service.update_configuration(system_prompt="New prompt only")
    assert agent_service.model_name == original_model
    assert agent_service.temperature == 0.3
    assert agent_service.system_prompt == "New prompt only"

@patch('langchain_openai.ChatOpenAI')
@patch('langchain.agents.create_openai_functions_agent')
@patch('langchain.agents.AgentExecutor')
def test_get_response(mock_agent_executor, mock_create_agent, mock_chat_openai, agent_service):
    """Test if get_response returns expected output."""
    # Setup mock response
    mock_response = {"output": "Test response"}
    mock_agent_executor.return_value.invoke.return_value = mock_response
    
    # Configure the agent executor mock
    agent_service.agent_executor = mock_agent_executor.return_value
    
    # Test
    response = agent_service.get_response("Test input")
    
    # Assertions
    assert response == "Test response"
    mock_agent_executor.return_value.invoke.assert_called_once_with({
        "input": "Test input"
    })

@patch('langchain_openai.ChatOpenAI')
@patch('langchain.agents.create_openai_functions_agent')
@patch('langchain.agents.AgentExecutor')
def test_get_response_with_empty_input(mock_agent_executor, mock_create_agent, mock_chat_openai, agent_service):
    """Test get_response with empty input."""
    with pytest.raises(ValueError):
        agent_service.get_response("")

@patch('langchain_openai.ChatOpenAI')
@patch('langchain.agents.create_openai_functions_agent')
@patch('langchain.agents.AgentExecutor')
def test_get_response_with_none_input(mock_agent_executor, mock_create_agent, mock_chat_openai, agent_service):
    """Test get_response with None input."""
    with pytest.raises(ValueError):
        agent_service.get_response(None)

@patch('langchain_openai.ChatOpenAI')
@patch('langchain.agents.create_openai_functions_agent')
@patch('langchain.agents.AgentExecutor')
def test_get_response_executor_error(mock_agent_executor, mock_create_agent, mock_chat_openai, agent_service):
    """Test get_response when executor fails."""
    # Setup mock to raise an exception
    mock_agent_executor.return_value.invoke.side_effect = Exception("Test error")
    agent_service.agent_executor = mock_agent_executor.return_value
    
    with pytest.raises(Exception):
        agent_service.get_response("Test input")

def test_validate_temperature_invalid_type():
    """Test temperature validation with invalid type."""
    with pytest.raises(ValueError, match="Temperature must be a number"):
        AgentService.validate_temperature("0.5")

@patch('langchain_openai.ChatOpenAI')
@patch('langchain.agents.create_openai_functions_agent')
@patch('langchain.agents.AgentExecutor')
def test_get_response_error_handling(mock_agent_executor, mock_create_agent, mock_chat_openai):
    """Test error handling in get_response."""
    # Setup
    mock_agent_executor.return_value.invoke.side_effect = Exception("API Error")
    
    agent_service = AgentService(
        model_name="gpt-3.5-turbo",
        temperature=0.7,
        system_prompt="Test prompt",
        openai_api_key="test-key"
    )
    
    agent_service.agent_executor = mock_agent_executor.return_value
    
    # Test
    with pytest.raises(Exception, match="API Error"):
        agent_service.get_response("Test input") 