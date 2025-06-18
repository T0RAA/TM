import tkinter as tk
from tkinter import ttk, messagebox
from auth import AuthManager
import re

class AuthWindow:
    def __init__(self, parent):
        self.parent = parent
        self.auth_manager = AuthManager()
        self.user_id = None
        self.session_token = None
        
        # Check for remembered user
        remembered_user = self.auth_manager.get_remembered_user()
        if remembered_user:
            self.user_id = remembered_user['user_id']
            self.session_token = remembered_user['session_token']
            return  # Skip showing login window
        
        # Create main window
        self.window = tk.Toplevel(parent)
        self.window.title("Music Dating App - Login/Signup")
        self.window.geometry("400x550")
        self.window.resizable(False, False)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=5)
        
        # Create login and signup tabs
        self.login_tab = ttk.Frame(self.notebook)
        self.signup_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.login_tab, text='Login')
        self.notebook.add(self.signup_tab, text='Sign Up')
        
        self.setup_login_tab()
        self.setup_signup_tab()
        
        # Center window
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')
        
        # Make window modal
        self.window.transient(parent)
        self.window.grab_set()
        
    def setup_login_tab(self):
        # Login form
        login_frame = ttk.Frame(self.login_tab, padding="20")
        login_frame.pack(fill='both', expand=True)
        
        ttk.Label(login_frame, text="Login", font=('Arial', 16, 'bold')).pack(pady=(0, 20))
        
        # Username
        ttk.Label(login_frame, text="Username:").pack(anchor='w')
        self.login_username = ttk.Entry(login_frame, width=30)
        self.login_username.pack(pady=(0, 10))
        
        # Password
        ttk.Label(login_frame, text="Password:").pack(anchor='w')
        self.login_password = ttk.Entry(login_frame, width=30, show="*")
        self.login_password.pack(pady=(0, 10))
        
        # Remember me checkbox
        self.remember_me_var = tk.BooleanVar()
        remember_frame = ttk.Frame(login_frame)
        remember_frame.pack(fill='x', pady=(0, 20))
        ttk.Checkbutton(remember_frame, text="Remember me", variable=self.remember_me_var).pack(side=tk.LEFT)
        
        # Login button
        ttk.Button(login_frame, text="Login", command=self.login).pack(pady=10)
        
    def setup_signup_tab(self):
        # Signup form
        signup_frame = ttk.Frame(self.signup_tab, padding="20")
        signup_frame.pack(fill='both', expand=True)
        
        ttk.Label(signup_frame, text="Create Account", font=('Arial', 16, 'bold')).pack(pady=(0, 20))
        
        # Username
        ttk.Label(signup_frame, text="Username:").pack(anchor='w')
        self.signup_username = ttk.Entry(signup_frame, width=30)
        self.signup_username.pack(pady=(0, 10))
        
        # Email
        ttk.Label(signup_frame, text="Email:").pack(anchor='w')
        self.signup_email = ttk.Entry(signup_frame, width=30)
        self.signup_email.pack(pady=(0, 10))
        
        # Password
        ttk.Label(signup_frame, text="Password:").pack(anchor='w')
        self.signup_password = ttk.Entry(signup_frame, width=30, show="*")
        self.signup_password.pack(pady=(0, 10))
        
        # Confirm Password
        ttk.Label(signup_frame, text="Confirm Password:").pack(anchor='w')
        self.signup_confirm_password = ttk.Entry(signup_frame, width=30, show="*")
        self.signup_confirm_password.pack(pady=(0, 10))
        
        # Remember me checkbox
        self.signup_remember_me_var = tk.BooleanVar()
        signup_remember_frame = ttk.Frame(signup_frame)
        signup_remember_frame.pack(fill='x', pady=(0, 20))
        ttk.Checkbutton(signup_remember_frame, text="Remember me", variable=self.signup_remember_me_var).pack(side=tk.LEFT)
        
        # Signup button
        ttk.Button(signup_frame, text="Sign Up", command=self.signup).pack(pady=10)
        
    def validate_email(self, email):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
        
    def login(self):
        username = self.login_username.get().strip()
        password = self.login_password.get()
        remember_me = self.remember_me_var.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please fill in all fields")
            return
            
        user_id = self.auth_manager.authenticate_user(username, password)
        if user_id:
            # Create session
            session_token = self.auth_manager.create_session(user_id, remember_me)
            self.user_id = user_id
            self.session_token = session_token
            self.window.destroy()
        else:
            messagebox.showerror("Error", "Invalid username or password")
            
    def signup(self):
        username = self.signup_username.get().strip()
        email = self.signup_email.get().strip()
        password = self.signup_password.get()
        confirm_password = self.signup_confirm_password.get()
        remember_me = self.signup_remember_me_var.get()
        
        # Validate input
        if not username or not email or not password or not confirm_password:
            messagebox.showerror("Error", "Please fill in all fields")
            return
            
        if not self.validate_email(email):
            messagebox.showerror("Error", "Invalid email format")
            return
            
        if password != confirm_password:
            messagebox.showerror("Error", "Passwords do not match")
            return
            
        if len(password) < 8:
            messagebox.showerror("Error", "Password must be at least 8 characters long")
            return
            
        # Register user
        user_id = self.auth_manager.register_user(username, password, email)
        if user_id:
            # Create session
            session_token = self.auth_manager.create_session(user_id, remember_me)
            self.user_id = user_id
            self.session_token = session_token
            messagebox.showinfo("Success", "Account created successfully!")
            self.window.destroy()
        else:
            messagebox.showerror("Error", "Username or email already exists")
            
    def get_user_id(self):
        """Return the user_id after successful authentication"""
        return self.user_id
        
    def get_session_token(self):
        """Return the session token after successful authentication"""
        return self.session_token 