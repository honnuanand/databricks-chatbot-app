"""Chat management service for handling chat operations."""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

class ChatService:
    def __init__(self, chat_dir: str = "./chat_history"):
        """Initialize chat service with directory for storing chat history."""
        self.chat_dir = Path(chat_dir)
        self.chat_dir.mkdir(exist_ok=True)
    
    def save_chat(self, chat_id: str, chat_name: str, messages: List[dict]) -> None:
        """Save chat history to a JSON file."""
        chat_file = self.chat_dir / f"{chat_id}.json"
        
        # Convert messages to the correct format
        formatted_messages = []
        for m in messages:
            if isinstance(m, dict):
                formatted_messages.append({
                    "role": m["role"],
                    "content": m["content"]
                })
            else:
                formatted_messages.append({
                    "role": m.type,
                    "content": m.content
                })
        
        chat_data = {
            "id": chat_id,
            "name": chat_name,
            "messages": formatted_messages,
            "timestamp": datetime.now().isoformat()
        }
        
        with open(chat_file, "w") as f:
            json.dump(chat_data, f)
    
    def load_chat(self, chat_id: str) -> Tuple[Optional[str], List]:
        """Load chat history from a JSON file."""
        chat_file = self.chat_dir / f"{chat_id}.json"
        if chat_file.exists():
            with open(chat_file, "r") as f:
                chat_data = json.load(f)
                messages = []
                for m in chat_data["messages"]:
                    if m["role"] == "system":
                        messages.append(SystemMessage(content=m["content"]))
                    elif m["role"] == "human":
                        messages.append(HumanMessage(content=m["content"]))
                    elif m["role"] == "ai":
                        messages.append(AIMessage(content=m["content"]))
                return chat_data["name"], messages
        return None, []
    
    def get_saved_chats(self) -> List[Dict]:
        """Get list of saved chats."""
        chats = []
        for chat_file in self.chat_dir.glob("*.json"):
            with open(chat_file, "r") as f:
                chat_data = json.load(f)
                chats.append({
                    "id": chat_data["id"],
                    "name": chat_data["name"],
                    "timestamp": chat_data["timestamp"]
                })
        return sorted(chats, key=lambda x: x["timestamp"], reverse=True)
    
    def delete_chat(self, chat_id: str) -> None:
        """Delete a chat history file."""
        chat_file = self.chat_dir / f"{chat_id}.json"
        if chat_file.exists():
            chat_file.unlink()
    
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
        
        response = llm.invoke(messages)
        title = response.content.strip()
        
        # Add timestamp to the title
        now = datetime.now()
        date_str = now.strftime("%d-%b-%Y")
        time_str = now.strftime("%I:%M %p")
        return f"{title} {date_str} @ {time_str}" 