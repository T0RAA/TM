import json
import os
import hashlib
import secrets
import time
from typing import Optional, Tuple
from user_profile import UserProfile, UserProfileManager

class AuthManager:
    def __init__(self, auth_file: str = 'data/auth.json', session_file: str = 'data/session.json'):
        self.auth_file = auth_file
        self.session_file = session_file
        self.profile_manager = UserProfileManager()
        os.makedirs(os.path.dirname(auth_file), exist_ok=True)
        self._load_auth_data()
        self._load_session_data()

    def _load_auth_data(self):
        """Load authentication data from file"""
        if os.path.exists(self.auth_file):
            with open(self.auth_file, 'r') as f:
                self.auth_data = json.load(f)
        else:
            self.auth_data = {}
            self._save_auth_data()

    def _save_auth_data(self):
        """Save authentication data to file"""
        with open(self.auth_file, 'w') as f:
            json.dump(self.auth_data, f, indent=2)

    def _load_session_data(self):
        """Load session data from file"""
        if os.path.exists(self.session_file):
            with open(self.session_file, 'r') as f:
                self.session_data = json.load(f)
        else:
            self.session_data = {}
            self._save_session_data()

    def _save_session_data(self):
        """Save session data to file"""
        with open(self.session_file, 'w') as f:
            json.dump(self.session_data, f, indent=2)

    def _hash_password(self, password: str, salt: Optional[str] = None) -> Tuple[str, str]:
        """Hash password with salt"""
        if salt is None:
            salt = secrets.token_hex(16)
        hashed = hashlib.sha256((password + salt).encode()).hexdigest()
        return hashed, salt

    def create_session(self, user_id: str, remember_me: bool = False) -> str:
        """Create a new session for a user"""
        session_token = secrets.token_hex(32)
        current_time = time.time()
        
        # Session expires in 30 days if remember me is checked, otherwise 24 hours
        expiry_time = current_time + (30 * 24 * 3600 if remember_me else 24 * 3600)
        
        self.session_data[session_token] = {
            'user_id': user_id,
            'created_at': current_time,
            'expires_at': expiry_time,
            'remember_me': remember_me
        }
        
        self._save_session_data()
        return session_token

    def validate_session(self, session_token: str) -> Optional[str]:
        """Validate a session token and return user_id if valid"""
        if session_token not in self.session_data:
            return None
            
        session = self.session_data[session_token]
        current_time = time.time()
        
        # Check if session has expired
        if current_time > session['expires_at']:
            del self.session_data[session_token]
            self._save_session_data()
            return None
            
        # Extend session if remember me is enabled
        if session['remember_me']:
            session['expires_at'] = current_time + (30 * 24 * 3600)  # Extend by 30 days
            self._save_session_data()
            
        return session['user_id']

    def delete_session(self, session_token: str):
        """Delete a session"""
        if session_token in self.session_data:
            del self.session_data[session_token]
            self._save_session_data()

    def get_remembered_user(self) -> Optional[dict]:
        """Get the remembered user's data if available"""
        for session_token, session in self.session_data.items():
            if session['remember_me'] and time.time() <= session['expires_at']:
                user_id = session['user_id']
                user_data = self.get_user_data(user_id)
                if user_data:
                    return {
                        'user_id': user_id,
                        'username': user_data['username'],
                        'session_token': session_token
                    }
        return None

    def register_user(self, username: str, password: str, email: str) -> Optional[str]:
        """Register a new user"""
        # Check if username or email already exists
        for user_id, data in self.auth_data.items():
            if data['username'] == username or data['email'] == email:
                return None

        # Generate user ID
        user_id = secrets.token_hex(8)
        
        # Hash password
        hashed_password, salt = self._hash_password(password)
        
        # Store user data
        self.auth_data[user_id] = {
            'username': username,
            'password': hashed_password,
            'salt': salt,
            'email': email
        }
        
        # Create initial profile
        profile = UserProfile(
            user_id=user_id,
            username=username,
            music_preferences=[],
            top_artists=[],
            top_genres=[],
            top_songs=[],
            top_albums=[]
        )
        self.profile_manager.save_profile(profile)
        
        self._save_auth_data()
        return user_id

    def authenticate_user(self, username: str, password: str) -> Optional[str]:
        """Authenticate a user and return their user_id if successful"""
        for user_id, data in self.auth_data.items():
            if data['username'] == username:
                hashed_password, _ = self._hash_password(password, data['salt'])
                if hashed_password == data['password']:
                    return user_id
        return None

    def get_user_data(self, user_id: str) -> Optional[dict]:
        """Get user data by user_id"""
        return self.auth_data.get(user_id)

    def update_user_data(self, user_id: str, data: dict):
        """Update user data"""
        if user_id in self.auth_data:
            self.auth_data[user_id].update(data)
            self._save_auth_data()

    def delete_user(self, user_id: str):
        """Delete a user and their profile"""
        if user_id in self.auth_data:
            del self.auth_data[user_id]
            self._save_auth_data()
            # Delete profile file
            profile_file = os.path.join(self.profile_manager.storage_dir, f"{user_id}.json")
            if os.path.exists(profile_file):
                os.remove(profile_file)
            # Delete all sessions for this user
            session_tokens_to_delete = []
            for session_token, session in self.session_data.items():
                if session['user_id'] == user_id:
                    session_tokens_to_delete.append(session_token)
            for token in session_tokens_to_delete:
                del self.session_data[token]
            self._save_session_data() 