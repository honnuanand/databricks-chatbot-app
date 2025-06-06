"""Sidebar component for the Streamlit app."""

import streamlit as st
from typing import Tuple, Callable

def render_sidebar(
    on_settings_change: Callable[[str, float, str, bool], None],
    on_new_chat: Callable[[], None],
    on_save_chat: Callable[[], None],
    on_load_chat: Callable[[str], None],
    on_delete_chat: Callable[[str], None],
    saved_chats: list,
    current_settings: dict
) -> None:
    """Render the sidebar with all its components."""
    st.sidebar.title("Databricks AI Chatbot")
    
    # Settings in an accordion
    with st.sidebar.expander("⚙️ Settings", expanded=False):
        # Model selection
        model = st.selectbox(
            "Model",
            ["gpt-3.5-turbo", "gpt-4"],
            index=0 if current_settings["model"] == "gpt-3.5-turbo" else 1,
            help="Select the OpenAI model to use"
        )
        
        # Temperature slider
        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=current_settings["temperature"],
            step=0.1,
            help="Higher values make the output more creative but less focused"
        )
        
        # System prompt
        system_prompt = st.text_area(
            "System Prompt",
            value=current_settings["system_prompt"],
            help="Customize the AI assistant's behavior"
        )
        
        # Theme toggle
        st.subheader("Appearance")
        theme = st.toggle(
            "Dark Mode",
            value=current_settings["theme"] == "dark",
            help="Switch between light and dark themes"
        )
        
        # Apply button for settings
        if st.button("Apply Settings", type="primary"):
            on_settings_change(
                model,
                temperature,
                system_prompt,
                theme
            )
    
    st.sidebar.divider()
    
    # Chat Management section
    st.sidebar.subheader("Chat Management")
    
    # New Chat and Save Chat buttons
    col1, col2 = st.sidebar.columns([1, 1])
    with col1:
        if st.button("🆕 New Chat", use_container_width=True):
            on_new_chat()
    with col2:
        if st.button("💾 Save Chat", use_container_width=True):
            on_save_chat()
    
    # List of saved chats
    if saved_chats:
        st.sidebar.subheader("Saved Chats")
        for chat in saved_chats:
            col1, col2 = st.sidebar.columns([6, 1])
            with col1:
                if st.button(chat["chat_name"], key=f"chat_{chat['chat_id']}", use_container_width=True):
                    on_load_chat(chat["chat_id"])
            with col2:
                if st.button("🗑️", key=f"delete_{chat['chat_id']}", help="Delete chat"):
                    on_delete_chat(chat["chat_id"]) 