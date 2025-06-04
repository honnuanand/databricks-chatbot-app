"""Service for managing chat history and persistence."""

import json
import os
from pathlib import Path
from typing import List, Dict, Tuple
from langchain_core.messages import SystemMessage, HumanMessage

class ChatService:
    def __init__(self):
        """Initialize the chat service."""
        self.saved_chats_dir = "saved_chats"
        os.makedirs(self.saved_chats_dir, exist_ok=True)
    
    def save_chat(self, chat_id: str, chat_name: str, messages: List[Dict]) -> None:
        """Save chat history to a file."""
        chat_data = {
            "chat_id": chat_id,
            "chat_name": chat_name,
            "messages": messages
        }
        
        file_path = os.path.join(self.saved_chats_dir, f"{chat_id}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(chat_data, f, indent=2)
    
    def load_chat(self, chat_id: str) -> Tuple[str, List[Dict]]:
        """Load chat history from a file."""
        file_path = os.path.join(self.saved_chats_dir, f"{chat_id}.json")
        with open(file_path, "r", encoding="utf-8") as f:
            chat_data = json.load(f)
            return chat_data["chat_name"], chat_data["messages"]
    
    def get_saved_chats(self) -> List[Dict]:
        """Get list of saved chats."""
        chats = []
        for chat_file in os.listdir(self.saved_chats_dir):
            if chat_file.endswith(".json"):
                file_path = os.path.join(self.saved_chats_dir, chat_file)
                with open(file_path, "r", encoding="utf-8") as f:
                    chat_data = json.load(f)
                    chats.append({
                        "chat_id": chat_data["chat_id"],
                        "chat_name": chat_data["chat_name"]
                    })
        return chats
    
    def delete_chat(self, chat_id: str) -> None:
        """Delete a chat history file."""
        file_path = os.path.join(self.saved_chats_dir, f"{chat_id}.json")
        os.remove(file_path)
    
    def generate_chat_name(self, first_message: str, llm) -> str:
        """Generate a chat name using LLM."""
        system_prompt = """You are a helpful assistant that generates concise and meaningful titles for chat conversations.
        Given the first message of a chat, create a brief but descriptive title that captures the main topic or intent.
        The title should be 2-5 words, be properly capitalized, and not include any special characters or dates.
        Focus on the key subject matter or question being discussed."""
        
        user_prompt = f"Generate a concise title for a chat that starts with this message: '{first_message}'"
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        # Handle both string and AIMessage responses
        response = llm.invoke(messages)
        if isinstance(response, str):
            return response.strip()
        return response.content.strip() 