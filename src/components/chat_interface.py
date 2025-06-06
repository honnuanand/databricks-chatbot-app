"""Chat interface component for the Streamlit app."""

import streamlit as st
from typing import List, Callable

def render_chat_interface(
    messages: List[dict],
    on_message: Callable[[str], None]
) -> None:
    """Render the chat interface with message history and input."""
    # Display main title and welcome message
    st.markdown("""
    <h1 style='margin-bottom: 0;'>Welcome to Databricks AI Assistant</h1>
    <p style='font-size: 1.2em; color: #4A90E2; margin-bottom: 2em;'>Your intelligent companion for Databricks expertise</p>
    """, unsafe_allow_html=True)
    
    # Display welcome message with key features
    st.markdown("""
    👋 Hi! I'm here to help you with:
    - Answering questions about Databricks
    - Finding up-to-date information
    - Providing technical guidance
    - Explaining Databricks concepts
    
    Feel free to ask anything!
    """)
    
    # Add a visual separator
    st.divider()
    
    # Create a container for chat messages
    chat_container = st.container()
    
    # Display chat history in the container
    with chat_container:
        for message in messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    
    # Chat input
    if user_input := st.chat_input("Type your message here...", key="chat_input"):
        # Process the message
        on_message(user_input) 