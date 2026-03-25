"""
Derei Authentication & User Management
Provides user registration, login, and session management
"""

import os
import json
import hashlib
import secrets
from datetime import datetime
from pathlib import Path

class UserManager:
    """Manages user accounts and authentication"""
    
    def __init__(self, data_dir=None):
        if data_dir is None:
            data_dir = os.path.join(os.path.dirname(__file__), "data")
        
        self.data_dir = data_dir
        self.users_file = os.path.join(data_dir, "users.json")
        self.sessions_file = os.path.join(data_dir, "sessions.json")
        self.ensure_files_exist()
    
    def ensure_files_exist(self):
        """Create necessary directories and files"""
        os.makedirs(self.data_dir, exist_ok=True)
        
        if not os.path.exists(self.users_file):
            with open(self.users_file, 'w') as f:
                json.dump({}, f)
        
        if not os.path.exists(self.sessions_file):
            with open(self.sessions_file, 'w') as f:
                json.dump({}, f)
    
    def hash_password(self, password):
        """Hash password with salt"""
        salt = secrets.token_hex(16)
        hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return f"{salt}${hashed.hex()}"
    
    def verify_password(self, password, hashed):
        """Verify password against hash"""
        try:
            salt, hash_hex = hashed.split('$')
            new_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            return new_hash.hex() == hash_hex
        except:
            return False
    
    def register_user(self, username, email, password):
        """Register a new user"""
        with open(self.users_file, 'r') as f:
            users = json.load(f)
        
        # Check if user exists
        if username in users:
            return False, "Username already exists"
        
        # Check if email is taken
        for user in users.values():
            if user.get('email') == email:
                return False, "Email already registered"
        
        # Create user
        users[username] = {
            'email': email,
            'password': self.hash_password(password),
            'created_at': datetime.now().isoformat(),
            'chats': []  # List of chat IDs
        }
        
        with open(self.users_file, 'w') as f:
            json.dump(users, f, indent=2)
        
        return True, "User registered successfully"
    
    def login_user(self, username, password):
        """Authenticate user and create session"""
        with open(self.users_file, 'r') as f:
            users = json.load(f)
        
        if username not in users:
            return None, "User not found"
        
        user = users[username]
        if not self.verify_password(password, user['password']):
            return None, "Invalid password"
        
        # Create session token
        session_token = secrets.token_hex(32)
        
        with open(self.sessions_file, 'r') as f:
            sessions = json.load(f)
        
        sessions[session_token] = {
            'username': username,
            'created_at': datetime.now().isoformat(),
            'expires_at': None  # Sessions don't expire for now
        }
        
        with open(self.sessions_file, 'w') as f:
            json.dump(sessions, f, indent=2)
        
        return session_token, "Login successful"
    
    def verify_session(self, session_token):
        """Verify session token and return username"""
        with open(self.sessions_file, 'r') as f:
            sessions = json.load(f)
        
        if session_token not in sessions:
            return None
        
        session = sessions[session_token]
        return session['username']
    
    def logout_user(self, session_token):
        """Logout user by removing session"""
        with open(self.sessions_file, 'r') as f:
            sessions = json.load(f)
        
        if session_token in sessions:
            del sessions[session_token]
        
        with open(self.sessions_file, 'w') as f:
            json.dump(sessions, f, indent=2)
        
        return True
    
    def get_user_chats(self, username):
        """Get all chats for a user"""
        with open(self.users_file, 'r') as f:
            users = json.load(f)
        
        if username not in users:
            return []
        
        return users[username].get('chats', [])
    
    def get_user_info(self, username):
        """Get user profile info"""
        with open(self.users_file, 'r') as f:
            users = json.load(f)
        
        if username not in users:
            return None
        
        user = users[username]
        # Don't return password hash
        return {
            'username': username,
            'email': user['email'],
            'created_at': user['created_at'],
            'chat_count': len(user.get('chats', []))
        }


class ChatManager:
    """Manages user chat sessions"""
    
    def __init__(self, data_dir=None):
        if data_dir is None:
            data_dir = os.path.join(os.path.dirname(__file__), "data")
        
        self.data_dir = data_dir
        self.chats_dir = os.path.join(data_dir, "user_chats")
        os.makedirs(self.chats_dir, exist_ok=True)
    
    def create_chat(self, username, title="New Chat"):
        """Create a new chat session for user"""
        import uuid
        chat_id = str(uuid.uuid4())[:8]
        
        chat_data = {
            'id': chat_id,
            'username': username,
            'title': title,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'messages': []
        }
        
        chat_file = os.path.join(self.chats_dir, f"{username}_{chat_id}.json")
        with open(chat_file, 'w') as f:
            json.dump(chat_data, f, indent=2)
        
        return chat_id
    
    def get_chat(self, username, chat_id):
        """Get chat data"""
        chat_file = os.path.join(self.chats_dir, f"{username}_{chat_id}.json")
        
        if not os.path.exists(chat_file):
            return None
        
        with open(chat_file, 'r') as f:
            return json.load(f)
    
    def save_chat(self, username, chat_id, chat_data):
        """Save chat data"""
        chat_data['updated_at'] = datetime.now().isoformat()
        chat_file = os.path.join(self.chats_dir, f"{username}_{chat_id}.json")
        
        with open(chat_file, 'w') as f:
            json.dump(chat_data, f, indent=2)
    
    def add_message(self, username, chat_id, role, content):
        """Add message to a chat"""
        chat = self.get_chat(username, chat_id)
        if not chat:
            return False
        
        chat['messages'].append({
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        })
        
        self.save_chat(username, chat_id, chat)
        return True
    
    def list_user_chats(self, username):
        """List all chats for a user (summary)"""
        chats = []
        for filename in os.listdir(self.chats_dir):
            if filename.startswith(f"{username}_"):
                chat_file = os.path.join(self.chats_dir, filename)
                with open(chat_file, 'r') as f:
                    chat_data = json.load(f)
                    chats.append({
                        'id': chat_data['id'],
                        'title': chat_data['title'],
                        'created_at': chat_data['created_at'],
                        'updated_at': chat_data['updated_at'],
                        'message_count': len(chat_data['messages'])
                    })
        
        # Sort by updated_at (most recent first)
        chats.sort(key=lambda x: x['updated_at'], reverse=True)
        return chats
    
    def delete_chat(self, username, chat_id):
        """Delete a chat"""
        chat_file = os.path.join(self.chats_dir, f"{username}_{chat_id}.json")
        if os.path.exists(chat_file):
            os.remove(chat_file)
            return True
        return False
    
    def update_chat_title(self, username, chat_id, new_title):
        """Update chat title"""
        chat = self.get_chat(username, chat_id)
        if not chat:
            return False
        
        chat['title'] = new_title
        self.save_chat(username, chat_id, chat)
        return True
