import pytest
import json
import os
from unittest.mock import patch, mock_open, call, ANY, Mock
from src.services.chat_service import ChatService

@pytest.fixture
def chat_service():
    return ChatService()

@pytest.fixture
def mock_chat_data():
    return {
        "chat_id": "test_123",
        "chat_name": "Test Chat",
        "messages": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
    }

def test_chat_service_initialization(chat_service):
    """Test if ChatService initializes correctly."""
    assert chat_service.saved_chats_dir == "saved_chats"
    assert os.path.exists(chat_service.saved_chats_dir)

def test_save_chat(chat_service, mock_chat_data):
    """Test saving a chat."""
    expected_data = {
        "chat_id": mock_chat_data["chat_id"],
        "chat_name": mock_chat_data["chat_name"],
        "messages": mock_chat_data["messages"]
    }
    
    mock_file = mock_open()
    with patch('builtins.open', mock_file):
        chat_service.save_chat(
            mock_chat_data["chat_id"],
            mock_chat_data["chat_name"],
            mock_chat_data["messages"]
        )
        
        # Check if file was opened with correct path
        expected_path = os.path.join("saved_chats", f"{mock_chat_data['chat_id']}.json")
        mock_file.assert_called_once_with(expected_path, 'w', encoding='utf-8')
        
        # Verify json.dump was called with correct data
        handle = mock_file()
        
        # Combine all write calls into a single string
        written_data = ""
        for call_args in handle.write.call_args_list:
            written_data += call_args[0][0]
        
        # Parse and verify the written JSON
        assert json.loads(written_data) == expected_data

def test_load_chat(chat_service, mock_chat_data):
    """Test loading a chat."""
    with patch('builtins.open', mock_open(read_data=json.dumps(mock_chat_data))) as mock_file:
        chat_name, messages = chat_service.load_chat(mock_chat_data["chat_id"])
        
        # Check if file was opened with correct path
        expected_path = os.path.join("saved_chats", f"{mock_chat_data['chat_id']}.json")
        mock_file.assert_called_once_with(expected_path, 'r', encoding='utf-8')
        
        # Check returned data
        assert chat_name == mock_chat_data["chat_name"]
        assert messages == mock_chat_data["messages"]

def test_get_saved_chats(chat_service):
    """Test retrieving saved chats."""
    mock_files = ['123.json', '456.json']
    mock_chats = [
        {"chat_id": "123", "chat_name": "Chat 1", "messages": []},
        {"chat_id": "456", "chat_name": "Chat 2", "messages": []}
    ]
    
    with patch('os.listdir', return_value=mock_files), \
         patch('builtins.open', side_effect=[
             mock_open(read_data=json.dumps(chat)).return_value 
             for chat in mock_chats
         ]):
        saved_chats = chat_service.get_saved_chats()
        assert len(saved_chats) == 2
        assert all(chat["chat_id"] in ["123", "456"] for chat in saved_chats)

def test_delete_chat(chat_service):
    """Test deleting a chat."""
    chat_id = "test_123"
    with patch('os.remove') as mock_remove:
        chat_service.delete_chat(chat_id)
        expected_path = os.path.join("saved_chats", f"{chat_id}.json")
        mock_remove.assert_called_once_with(expected_path)

def test_generate_chat_name(chat_service):
    """Test generating a chat name."""
    mock_llm = MockLLM()
    user_input = "What is Databricks?"
    chat_name = chat_service.generate_chat_name(user_input, mock_llm)
    assert isinstance(chat_name, str)
    assert len(chat_name) > 0

def test_generate_chat_name_string_response():
    """Test chat name generation with string response."""
    # Setup
    chat_service = ChatService()
    mock_llm = Mock()
    mock_llm.invoke.return_value = "Generated Title"
    
    # Test
    result = chat_service.generate_chat_name("Hello", mock_llm)
    
    # Verify
    assert result == "Generated Title"
    mock_llm.invoke.assert_called_once()
    assert len(mock_llm.invoke.call_args[0][0]) == 2  # System and Human messages

class MockLLM:
    """Mock LLM for testing."""
    def invoke(self, *args, **kwargs):
        return "Generated Chat Name" 