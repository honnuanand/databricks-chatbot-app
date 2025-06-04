"""Main application file for the Databricks AI Chatbot."""

import streamlit as st
import os
from datetime import datetime
from dotenv import load_dotenv
from typing import Optional

from src.components.sidebar import render_sidebar
from src.components.chat_interface import render_chat_interface
from src.services.chat_service import ChatService
from src.services.agent_service import AgentService

# Load environment variables
load_dotenv()

def configure_page():
    """Configure Streamlit page settings."""
    st.set_page_config(
        page_title="Databricks AI Chatbot",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )

def get_openai_api_key() -> str:
    """
    Get OpenAI API key from either Databricks secrets or environment variables.
    Returns the API key as a string.
    Raises ValueError if no API key is found.
    """
    api_key = None
    
    # Try Databricks secrets first
    try:
        from databricks.sdk.runtime import dbutils
        api_key = dbutils.secrets.get(scope="chatbot-secrets", key="OPENAI_API_KEY")
    except (ImportError, Exception):
        # Not in Databricks environment or secret not found
        pass
    
    # Fall back to environment variable
    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        raise ValueError(
            "OpenAI API key not found. Please set it either in Databricks secrets "
            "or as an environment variable OPENAI_API_KEY"
        )
    
    return api_key

def initialize_session_state():
    """Initialize session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "chat_id" not in st.session_state:
        st.session_state.chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    if "chat_name" not in st.session_state:
        st.session_state.chat_name = None
    if "model" not in st.session_state:
        st.session_state.model = "gpt-3.5-turbo"
    if "temperature" not in st.session_state:
        st.session_state.temperature = 0.7
    if "system_prompt" not in st.session_state:
        st.session_state.system_prompt = "You are a helpful Databricks AI assistant. You have access to tools that can help you provide more accurate and up-to-date information."
    if "theme" not in st.session_state:
        st.session_state.theme = "light"
    if "agent_service" not in st.session_state:
        st.session_state.agent_service = AgentService(
            model_name=st.session_state.model,
            temperature=st.session_state.temperature,
            system_prompt=st.session_state.system_prompt,
            openai_api_key=get_openai_api_key()
        )
    if "chat_service" not in st.session_state:
        st.session_state.chat_service = ChatService()

def handle_settings_change(model: str, temperature: float, system_prompt: str, dark_mode: bool):
    """Handle settings changes and update the application state."""
    st.session_state.model = model
    st.session_state.temperature = temperature
    st.session_state.system_prompt = system_prompt
    st.session_state.theme = "dark" if dark_mode else "light"
    
    # Update agent configuration
    st.session_state.agent_service.update_configuration(
        model_name=model,
        temperature=temperature,
        system_prompt=system_prompt
    )
    st.rerun()

def handle_new_chat():
    """Handle creating a new chat."""
    st.session_state.messages = []
    st.session_state.chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    st.session_state.chat_name = None
    st.rerun()

def handle_save_chat():
    """Handle saving the current chat."""
    st.session_state.chat_service.save_chat(
        st.session_state.chat_id,
        st.session_state.chat_name,
        st.session_state.messages
    )
    st.toast("Chat saved successfully!", icon="✅")

def handle_load_chat(chat_id: str):
    """Handle loading a saved chat."""
    st.session_state.chat_id = chat_id
    st.session_state.chat_name, st.session_state.messages = st.session_state.chat_service.load_chat(chat_id)
    st.rerun()

def handle_delete_chat(chat_id: str):
    """Handle chat deletion."""
    # Delete chat
    st.session_state.chat_service.delete_chat(chat_id)
    
    # If deleting current chat, reset state
    if chat_id == st.session_state.chat_id:
        st.session_state.messages = []
        st.session_state.chat_name = None
        st.session_state.chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    # Rerun app
    st.rerun()

def handle_message(user_input: str):
    """Handle new message in the chat."""
    # Generate chat name from first message if not exists
    if not st.session_state.chat_name and len(st.session_state.messages) == 0:
        st.session_state.chat_name = st.session_state.chat_service.generate_chat_name(
            user_input,
            st.session_state.agent_service.agent_executor.agent.llm
        )
    
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Get assistant response
    response = st.session_state.agent_service.get_response(user_input)
    
    # Add assistant response to history
    st.session_state.messages.append({"role": "assistant", "content": response})
    
    # Auto-save after each message
    handle_save_chat()

def main():
    """Main application function."""
    # Import theme styles
    from src.styles.dark_theme import DARK_THEME
    from src.styles.light_theme import LIGHT_THEME
    
    # Configure page
    configure_page()
    
    # Initialize session state
    initialize_session_state()
    
    # Apply theme
    if st.session_state.theme == "dark":
        st.markdown(DARK_THEME, unsafe_allow_html=True)
    else:
        st.markdown(LIGHT_THEME, unsafe_allow_html=True)
    
    # Render sidebar
    render_sidebar(
        on_settings_change=handle_settings_change,
        on_new_chat=handle_new_chat,
        on_save_chat=handle_save_chat,
        on_load_chat=handle_load_chat,
        on_delete_chat=handle_delete_chat,
        saved_chats=st.session_state.chat_service.get_saved_chats(),
        current_settings={
            "model": st.session_state.model,
            "temperature": st.session_state.temperature,
            "system_prompt": st.session_state.system_prompt,
            "theme": st.session_state.theme
        }
    )
    
    # Render chat interface
    render_chat_interface(
        messages=st.session_state.messages,
        on_message=handle_message
    )

if __name__ == "__main__":
    main() 