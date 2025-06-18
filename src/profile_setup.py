import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import os
from user_profile import UserProfile, UserProfileManager

class ProfileSetupWindow:
    def __init__(self, parent, user_id, profile_manager):
        self.parent = parent
        self.user_id = user_id
        self.profile_manager = profile_manager
        self.selected_image_path = None
        self.profile_picture_photo = None
        
        # Create main window
        self.window = tk.Toplevel(parent)
        self.window.title("Complete Your Profile")
        self.window.geometry("600x700")
        self.window.resizable(False, False)
        
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
        
        self.setup_ui()
        self.load_existing_profile()
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.pack(fill='both', expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Complete Your Profile", font=('Arial', 18, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Create scrollable frame
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Profile Picture Section
        self.setup_profile_picture_section(scrollable_frame)
        
        # Personal Information Section
        self.setup_personal_info_section(scrollable_frame)
        
        # Bio Section
        self.setup_bio_section(scrollable_frame)
        
        # Buttons
        self.setup_buttons(scrollable_frame)
        
    def setup_profile_picture_section(self, parent):
        # Profile Picture Frame
        pic_frame = ttk.LabelFrame(parent, text="Profile Picture", padding="10")
        pic_frame.pack(fill='x', pady=10)
        
        # Picture display
        self.pic_display = tk.Canvas(pic_frame, width=200, height=200, bg='lightgray')
        self.pic_display.pack(pady=10)
        
        # Default text
        self.pic_display.create_text(100, 100, text="No image selected", fill='gray')
        
        # Upload button
        upload_btn = ttk.Button(pic_frame, text="Upload Picture", command=self.upload_picture)
        upload_btn.pack(pady=5)
        
        # Remove button
        self.remove_pic_btn = ttk.Button(pic_frame, text="Remove Picture", command=self.remove_picture, state='disabled')
        self.remove_pic_btn.pack(pady=5)
        
    def setup_personal_info_section(self, parent):
        # Personal Information Frame
        info_frame = ttk.LabelFrame(parent, text="Personal Information", padding="10")
        info_frame.pack(fill='x', pady=10)
        
        # First Name
        ttk.Label(info_frame, text="First Name:").pack(anchor='w')
        self.first_name_entry = ttk.Entry(info_frame, width=40)
        self.first_name_entry.pack(fill='x', pady=(0, 10))
        
        # Last Name
        ttk.Label(info_frame, text="Last Name:").pack(anchor='w')
        self.last_name_entry = ttk.Entry(info_frame, width=40)
        self.last_name_entry.pack(fill='x', pady=(0, 10))
        
        # Age
        ttk.Label(info_frame, text="Age:").pack(anchor='w')
        self.age_entry = ttk.Entry(info_frame, width=40)
        self.age_entry.pack(fill='x', pady=(0, 10))
        
        # Gender
        ttk.Label(info_frame, text="Gender:").pack(anchor='w')
        self.gender_var = tk.StringVar()
        gender_frame = ttk.Frame(info_frame)
        gender_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Radiobutton(gender_frame, text="Male", variable=self.gender_var, value="Male").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(gender_frame, text="Female", variable=self.gender_var, value="Female").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(gender_frame, text="Other", variable=self.gender_var, value="Other").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(gender_frame, text="Prefer not to say", variable=self.gender_var, value="Prefer not to say").pack(side=tk.LEFT)
        
        # Location
        ttk.Label(info_frame, text="Location (City, Country):").pack(anchor='w')
        self.location_entry = ttk.Entry(info_frame, width=40)
        self.location_entry.pack(fill='x', pady=(0, 10))
        
    def setup_bio_section(self, parent):
        # Bio Frame
        bio_frame = ttk.LabelFrame(parent, text="About Me", padding="10")
        bio_frame.pack(fill='x', pady=10)
        
        ttk.Label(bio_frame, text="Tell us about yourself:").pack(anchor='w')
        self.bio_text = tk.Text(bio_frame, height=4, width=50)
        self.bio_text.pack(fill='x', pady=(0, 10))
        
    def setup_buttons(self, parent):
        # Buttons Frame
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill='x', pady=20)
        
        ttk.Button(button_frame, text="Save Profile", command=self.save_profile).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Skip for Now", command=self.skip_setup).pack(side=tk.RIGHT, padx=5)
        
    def upload_picture(self):
        """Handle profile picture upload"""
        file_path = filedialog.askopenfilename(
            title="Select Profile Picture",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.gif"),
                ("JPEG files", "*.jpg *.jpeg"),
                ("PNG files", "*.png"),
                ("GIF files", "*.gif"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            try:
                # Validate and process image
                self.selected_image_path = file_path
                self.display_profile_picture(file_path)
                self.remove_pic_btn.config(state='normal')
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load image: {str(e)}")
                
    def display_profile_picture(self, image_path):
        """Display the selected profile picture"""
        try:
            # Load and resize image
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize to fit canvas (200x200)
                img.thumbnail((200, 200), Image.LANCZOS)
                
                # Convert to PhotoImage
                self.profile_picture_photo = ImageTk.PhotoImage(img)
                
                # Clear canvas and display image
                self.pic_display.delete("all")
                self.pic_display.create_image(100, 100, image=self.profile_picture_photo)
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to display image: {str(e)}")
            
    def remove_picture(self):
        """Remove the selected profile picture"""
        self.selected_image_path = None
        self.profile_picture_photo = None
        self.pic_display.delete("all")
        self.pic_display.create_text(100, 100, text="No image selected", fill='gray')
        self.remove_pic_btn.config(state='disabled')
        
    def load_existing_profile(self):
        """Load existing profile data if available"""
        profile = self.profile_manager.load_profile(self.user_id)
        if profile:
            # Load personal information
            self.first_name_entry.insert(0, profile.first_name)
            self.last_name_entry.insert(0, profile.last_name)
            if profile.age:
                self.age_entry.insert(0, str(profile.age))
            self.gender_var.set(profile.gender)
            self.location_entry.insert(0, profile.location)
            self.bio_text.insert('1.0', profile.bio)
            
            # Load profile picture
            if profile.profile_picture_path and os.path.exists(profile.profile_picture_path):
                self.selected_image_path = profile.profile_picture_path
                self.display_profile_picture(profile.profile_picture_path)
                self.remove_pic_btn.config(state='normal')
                
    def validate_input(self):
        """Validate user input"""
        # Validate age
        age_text = self.age_entry.get().strip()
        if age_text:
            try:
                age = int(age_text)
                if age < 13 or age > 120:
                    messagebox.showerror("Error", "Age must be between 13 and 120")
                    return False
            except ValueError:
                messagebox.showerror("Error", "Age must be a valid number")
                return False
                
        return True
        
    def save_profile(self):
        """Save the profile information"""
        if not self.validate_input():
            return
            
        try:
            # Load existing profile or create new one
            profile = self.profile_manager.load_profile(self.user_id)
            if not profile:
                # Create new profile with basic info
                profile = UserProfile(
                    user_id=self.user_id,
                    username="",  # Will be filled from auth data
                    music_preferences=[],
                    top_artists=[],
                    top_genres=[],
                    top_songs=[],
                    top_albums=[]
                )
            
            # Update profile with new information
            profile.first_name = self.first_name_entry.get().strip()
            profile.last_name = self.last_name_entry.get().strip()
            
            age_text = self.age_entry.get().strip()
            profile.age = int(age_text) if age_text else None
            
            profile.gender = self.gender_var.get()
            profile.location = self.location_entry.get().strip()
            profile.bio = self.bio_text.get('1.0', tk.END).strip()
            
            # Handle profile picture
            if self.selected_image_path:
                try:
                    profile.profile_picture_path = self.profile_manager.save_profile_picture(
                        self.user_id, self.selected_image_path
                    )
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to save profile picture: {str(e)}")
                    return
            
            # Save profile
            self.profile_manager.save_profile(profile)
            
            messagebox.showinfo("Success", "Profile saved successfully!")
            self.window.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save profile: {str(e)}")
            
    def skip_setup(self):
        """Skip profile setup for now"""
        self.window.destroy() 