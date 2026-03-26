"""
Derei Authentication & User Management - Supabase Edition
Uses PostgreSQL via Supabase for persistent storage
"""

import os
import hashlib
import secrets
from datetime import datetime, timedelta
from supabase import create_client, Client

class SupabaseAuthManager:
    """Manages user accounts using Supabase PostgreSQL"""
    
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY environment variables")
        
        self.client: Client = create_client(self.supabase_url, self.supabase_key)
    
    def hash_password(self, password):
        """Hash password with salt (PBKDF2-SHA256)"""
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
        """Register new user"""
        try:
            # Check if username or email already exists
            existing_user = self.client.table('users').select('id').eq('username', username).execute()
            if existing_user.data:
                return {'success': False, 'error': 'Username already exists'}
            
            existing_email = self.client.table('users').select('id').eq('email', email).execute()
            if existing_email.data:
                return {'success': False, 'error': 'Email already exists'}
            
            # Insert new user
            response = self.client.table('users').insert({
                'username': username,
                'email': email,
                'password_hash': self.hash_password(password)
            }).execute()
            
            if response.data:
                return {'success': True, 'user_id': response.data[0]['id']}
            else:
                return {'success': False, 'error': 'Registration failed'}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def login_user(self, username, password):
        """Login user and create session"""
        try:
            # Get user
            response = self.client.table('users').select('*').eq('username', username).execute()
            if not response.data:
                return {'success': False, 'error': 'Invalid username or password'}
            
            user = response.data[0]
            
            # Verify password
            if not self.verify_password(password, user['password_hash']):
                return {'success': False, 'error': 'Invalid username or password'}
            
            # Create session token
            session_token = secrets.token_hex(32)
            expires_at = (datetime.utcnow() + timedelta(days=30)).isoformat()
            
            # Store session in database
            self.client.table('sessions').insert({
                'user_id': user['id'],
                'session_token': session_token,
                'expires_at': expires_at
            }).execute()
            
            return {
                'success': True,
                'session_token': session_token,
                'user': {'id': user['id'], 'username': user['username'], 'email': user['email']}
            }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def verify_session(self, session_token):
        """Verify session token and get user"""
        try:
            # Get session
            response = self.client.table('sessions').select('*').eq('session_token', session_token).execute()
            if not response.data:
                return {'valid': False, 'error': 'Invalid session'}
            
            session = response.data[0]
            
            # Check expiration
            if datetime.fromisoformat(session['expires_at']) < datetime.utcnow():
                return {'valid': False, 'error': 'Session expired'}
            
            # Get user
            user_response = self.client.table('users').select('*').eq('id', session['user_id']).execute()
            if not user_response.data:
                return {'valid': False, 'error': 'User not found'}
            
            user = user_response.data[0]
            return {
                'valid': True,
                'user': {'id': user['id'], 'username': user['username'], 'email': user['email']}
            }
        
        except Exception as e:
            return {'valid': False, 'error': str(e)}
    
    def logout_user(self, session_token):
        """Logout user by deleting session"""
        try:
            self.client.table('sessions').delete().eq('session_token', session_token).execute()
            return {'success': True}
        except:
            return {'success': False}


class SupabaseChatManager:
    """Manages chats and messages using Supabase"""
    
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY environment variables")
        
        self.client: Client = create_client(self.supabase_url, self.supabase_key)
    
    def create_chat(self, user_id, title):
        """Create new chat"""
        try:
            response = self.client.table('chats').insert({
                'user_id': user_id,
                'title': title
            }).execute()
            
            if response.data:
                chat = response.data[0]
                return {
                    'success': True,
                    'chat_id': chat['id'],
                    'title': chat['title'],
                    'created_at': chat['created_at']
                }
            return {'success': False, 'error': 'Failed to create chat'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_user_chats(self, user_id):
        """Get all chats for user"""
        try:
            response = self.client.table('chats').select('*').eq('user_id', user_id).order('created_at', desc=True).execute()
            
            chats = []
            for chat in response.data:
                # Count messages
                msg_response = self.client.table('messages').select('id', count='exact').eq('chat_id', chat['id']).execute()
                message_count = len(msg_response.data)
                
                chats.append({
                    'id': chat['id'],
                    'title': chat['title'],
                    'message_count': message_count,
                    'created_at': chat['created_at']
                })
            
            return {'success': True, 'chats': chats}
        except Exception as e:
            return {'success': False, 'error': str(e), 'chats': []}
    
    def get_chat(self, chat_id, user_id):
        """Get specific chat with messages"""
        try:
            # Verify ownership
            chat_response = self.client.table('chats').select('*').eq('id', chat_id).eq('user_id', user_id).execute()
            if not chat_response.data:
                return {'success': False, 'error': 'Chat not found or access denied'}
            
            chat = chat_response.data[0]
            
            # Get messages
            msg_response = self.client.table('messages').select('*').eq('chat_id', chat_id).order('created_at').execute()
            
            messages = []
            for msg in msg_response.data:
                messages.append({
                    'id': msg['id'],
                    'role': msg['role'],
                    'content': msg['content'],
                    'timestamp': msg['created_at']
                })
            
            return {
                'success': True,
                'id': chat['id'],
                'title': chat['title'],
                'messages': messages,
                'created_at': chat['created_at']
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def add_message(self, chat_id, user_id, role, content):
        """Add message to chat"""
        try:
            # Verify ownership
            chat_response = self.client.table('chats').select('id').eq('id', chat_id).eq('user_id', user_id).execute()
            if not chat_response.data:
                return {'success': False, 'error': 'Chat not found or access denied'}
            
            # Insert message
            response = self.client.table('messages').insert({
                'chat_id': chat_id,
                'role': role,
                'content': content
            }).execute()
            
            if response.data:
                msg = response.data[0]
                return {
                    'success': True,
                    'message_id': msg['id'],
                    'timestamp': msg['created_at']
                }
            return {'success': False, 'error': 'Failed to add message'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def delete_chat(self, chat_id, user_id):
        """Delete chat and all messages"""
        try:
            # Verify ownership
            chat_response = self.client.table('chats').select('id').eq('id', chat_id).eq('user_id', user_id).execute()
            if not chat_response.data:
                return {'success': False, 'error': 'Chat not found or access denied'}
            
            # Delete chat (messages deleted automatically via foreign key)
            self.client.table('chats').delete().eq('id', chat_id).execute()
            
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
