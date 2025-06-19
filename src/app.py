import requests
from pypresence import Presence
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import io
import webbrowser
import http.server
import socketserver
import urllib.parse
from user_profile import UserProfile, MusicPreference, UserProfileManager
from auth import AuthManager
from auth_window import AuthWindow
from profile_setup import ProfileSetupWindow
from search_dropdown import SpotifySearchDropdown
import json
import os
import threading
import time
from config import (
    SPOTIFY_CLIENT_ID,
    SPOTIFY_CLIENT_SECRET,
    REDIRECT_URI,
    SCOPE,
    DISCORD_CLIENT_ID
)
import tkinter.messagebox as messagebox
from tkinter import filedialog

# --- THEME SETUP ---
def create_vertical_gradient(width, height, color1, color2):
    from PIL import Image, ImageTk
    base = Image.new('RGB', (width, height), color1)
    top = Image.new('RGB', (width, height), color2)
    mask = Image.new('L', (width, height))
    for y in range(height):
        mask.putpixel((0, y), int(255 * (y / height)))
    mask = mask.resize((width, height))
    base.paste(top, (0, 0), mask)
    return ImageTk.PhotoImage(base)

def setup_theme(root):
    style = ttk.Style(root)
    root.configure(bg='#FFF0F6')
    style.theme_use('clam')
    # General
    style.configure('.', font=('Poppins', 11), background='#FFF0F6', foreground='#222')
    style.configure('TLabel', background='#FFF0F6', foreground='#222')
    style.configure('TFrame', background='#FFF0F6')
    style.configure('TNotebook', background='#FFF0F6', borderwidth=0)
    style.configure('TNotebook.Tab', background='#FFB6C1', foreground='#222', padding=10, font=('Poppins', 12, 'bold'))
    style.map('TNotebook.Tab', background=[('selected', '#39D353')], foreground=[('selected', '#FFF')])
    # Buttons
    style.configure('TButton',
        background='#39D353',
        foreground='#FFF',
        borderwidth=0,
        focusthickness=3,
        focuscolor='#FFB6C1',
        padding=8,
        font=('Poppins', 11, 'bold')
    )
    style.map('TButton',
        background=[('active', '#00E676')],
        foreground=[('active', '#FFF')]
    )
    # Entry fields
    style.configure('TEntry', fieldbackground='#FFF', bordercolor='#FFB6C1', relief='flat', padding=6)
    # LabelFrames
    style.configure('TLabelframe', background='#FFF0F6', bordercolor='#FFB6C1', borderwidth=2, relief='ridge')
    style.configure('TLabelframe.Label', background='#FFF0F6', foreground='#FF69B4', font=('Poppins', 12, 'bold'))

# --- BUBBLY BUTTON ---
class BubblyButton(tk.Canvas):
    def __init__(self, parent, text, command=None, width=200, height=54, color='#39D353', **kwargs):
        super().__init__(parent, width=width, height=height, bg='#FFE4EC', highlightthickness=0, bd=0, **kwargs)
        # Draw shadow
        self.create_oval(10, height-12, width-10, height+12, fill='#b2dfb2', outline='')
        # Draw pill button
        self.create_oval(0, 0, height, height, fill=color, outline='')
        self.create_oval(width-height, 0, width, height, fill=color, outline='')
        self.create_rectangle(height//2, 0, width-height//2, height, fill=color, outline='')
        # Draw text
        self.text_id = self.create_text(width//2, height//2, text=text, font=('Poppins', 16, 'bold'), fill='#fff')
        self.command = command
        self.bind('<Button-1>', lambda e: self.command() if self.command else None)
        self.bind('<Enter>', lambda e: self.itemconfig(self.text_id, fill='#222'))
        self.bind('<Leave>', lambda e: self.itemconfig(self.text_id, fill='#fff'))

# --- BUBBLY PROFILE CARD ---
def create_profile_card(parent, profile, image_size=100):
    card_w, card_h = 340, 220
    card = tk.Canvas(parent, width=card_w, height=card_h, bg='#FFE4EC', highlightthickness=0)
    # Draw shadow
    card.create_oval(20, card_h-30, card_w-20, card_h+20, fill='#e0bfcf', outline='')
    # Draw rounded rectangle (simulate with ovals + rectangles)
    card.create_oval(0, 0, 60, 60, fill='#fff', outline='')
    card.create_oval(card_w-60, 0, card_w, 60, fill='#fff', outline='')
    card.create_oval(0, card_h-60, 60, card_h, fill='#fff', outline='')
    card.create_oval(card_w-60, card_h-60, card_w, card_h, fill='#fff', outline='')
    card.create_rectangle(30, 0, card_w-30, card_h, fill='#fff', outline='')
    card.create_rectangle(0, 30, card_w, card_h-30, fill='#fff', outline='')
    # Profile image (circular)
    if profile and profile.profile_picture_path and os.path.exists(profile.profile_picture_path):
        try:
            from PIL import Image, ImageTk, ImageDraw
            img = Image.open(profile.profile_picture_path).convert('RGBA')
            img = img.resize((image_size, image_size), Image.LANCZOS)
            mask = Image.new('L', (image_size, image_size), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, image_size, image_size), fill=255)
            img.putalpha(mask)
            photo = ImageTk.PhotoImage(img)
            card.create_image(card_w//2, 60, image=photo)
            card.photo = photo  # Keep reference
        except Exception as e:
            card.create_oval(card_w//2-image_size//2, 20, card_w//2+image_size//2, 20+image_size, fill='#FFB6C1', outline='')
            card.create_text(card_w//2, 60, text='No Photo', fill='#fff', font=('Poppins', 10, 'bold'))
    else:
        card.create_oval(card_w//2-image_size//2, 20, card_w//2+image_size//2, 20+image_size, fill='#FFB6C1', outline='')
        card.create_text(card_w//2, 60, text='No Photo', fill='#fff', font=('Poppins', 10, 'bold'))
    # Name, age, artists
    name = f"{profile.first_name} {profile.last_name}" if profile and profile.first_name else "Your Name"
    age = f", {profile.age}" if profile and profile.age else ""
    card.create_text(card_w//2, 130, text=f"{name}{age}", font=('Poppins', 18, 'bold'), fill='#222')
    # Top Artists
    artists = ', '.join(profile.top_artists[:3]) if profile and profile.top_artists else "No artists yet"
    card.create_text(card_w//2, 165, text=f"Top Artists: {artists}", font=('Poppins', 12), fill='#39D353')
    return card

# --- HEADER WITH GRADIENT AND SHADOW ---
def create_header(parent, text):
    frame = tk.Frame(parent, bg='#FFF0F6')
    canvas = tk.Canvas(frame, width=340, height=50, bg='#FFF0F6', highlightthickness=0)
    grad_img = create_vertical_gradient(340, 40, '#FFB6C1', '#39D353')
    canvas.create_oval(10, 35, 330, 55, fill='#bbb', outline='')  # shadow
    canvas.create_image(0, 0, anchor='nw', image=grad_img)
    canvas.create_text(170, 25, text=text, font=('Poppins', 16, 'bold'), fill='#fff')
    canvas.pack()
    frame.pack(pady=10)
    frame.gradient_img = grad_img  # Keep reference
    return frame

# Initialize Discord Rich Presence
discord_rpc = Presence(DISCORD_CLIENT_ID)
discord_rpc.connect()

def get_spotify_token():
    auth_url = f'https://accounts.spotify.com/authorize?client_id={SPOTIFY_CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}&scope={SCOPE}'
    webbrowser.open(auth_url)

    # Start a local server to handle the redirect
    class MyHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'Authorization successful! You can close this window.')
            self.server.auth_code = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get('code', [None])[0]

    with socketserver.TCPServer(('', 3000), MyHandler) as httpd:
        print('Waiting for authorization...')
        httpd.handle_request()
        auth_code = httpd.auth_code

    # Exchange the authorization code for an access token
    token_url = 'https://accounts.spotify.com/api/token'
    data = {
        'grant_type': 'authorization_code',
        'code': auth_code,
        'redirect_uri': REDIRECT_URI,
        'client_id': SPOTIFY_CLIENT_ID,
        'client_secret': SPOTIFY_CLIENT_SECRET
    }
    response = requests.post(token_url, data=data)
    token_data = response.json()
    return token_data.get('access_token'), token_data.get('refresh_token')

def refresh_spotify_token(refresh_token):
    token_url = 'https://accounts.spotify.com/api/token'
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': SPOTIFY_CLIENT_ID,
        'client_secret': SPOTIFY_CLIENT_SECRET
    }
    response = requests.post(token_url, data=data)
    return response.json().get('access_token')

def get_current_playing(token):
    headers = {
        'Authorization': f'Bearer {token}'
    }
    response = requests.get('https://api.spotify.com/v1/me/player/currently-playing', headers=headers)
    
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 204:
        print("No track currently playing")
        return None
        
    if response.status_code != 200:
        print(f"Error: Received status code {response.status_code}")
        return None
        
    try:
        data = response.json()
        if not data.get('item'):
            print("No track information in response")
            return None
            
        track_info = {
            'id': data['item']['id'],
            'name': data['item']['name'],
            'artists': [artist['name'] for artist in data['item']['artists']],
            'album': {
                'name': data['item']['album']['name'],
                'images': data['item']['album']['images']
            }
        }
        print(f"Current track: {track_info['name']} by {', '.join(track_info['artists'])}")
        return track_info
    except (KeyError, requests.exceptions.JSONDecodeError) as e:
        print(f"Error processing track data: {e}")
        return None

def get_user_top_items(token, item_type='artists', limit=10, time_range='medium_term'):
    """
    Get user's top items from Spotify
    time_range options:
    - short_term: approximately last 4 weeks
    - medium_term: approximately last 6 months
    - long_term: calculated from several years of data
    """
    headers = {
        'Authorization': f'Bearer {token}'
    }
    response = requests.get(
        f'https://api.spotify.com/v1/me/top/{item_type}?limit={limit}&time_range={time_range}',
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"Error getting top {item_type}: {response.status_code}")
        return []
        
    data = response.json()
    if item_type == 'artists':
        return [artist['name'] for artist in data['items']]
    elif item_type == 'tracks':
        return [{
            'name': track['name'],
            'artist': track['artists'][0]['name'],
            'album': track['album']['name'],
            'album_art': track['album']['images'][0]['url'] if track['album']['images'] else None,
            'release_date': track['album']['release_date'],
            'popularity': track['popularity']
        } for track in data['items']]

def get_user_top_albums(token, limit=10, time_range='medium_term'):
    """
    Get user's top albums based on their top tracks
    """
    headers = {
        'Authorization': f'Bearer {token}'
    }
    response = requests.get(
        f'https://api.spotify.com/v1/me/top/tracks?limit=50&time_range={time_range}',
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"Error getting top tracks: {response.status_code}")
        return []
        
    data = response.json()
    album_data = {}
    
    # Count album occurrences and collect album data
    for track in data['items']:
        album = track['album']
        album_key = f"{album['name']} - {album['artists'][0]['name']}"
        if album_key not in album_data:
            album_data[album_key] = {
                'name': album['name'],
                'artist': album['artists'][0]['name'],
                'art_url': album['images'][0]['url'] if album['images'] else None,
                'release_date': album['release_date'],
                'count': 1
            }
        else:
            album_data[album_key]['count'] += 1
    
    # Sort albums by frequency and return top ones
    sorted_albums = sorted(album_data.items(), key=lambda x: x[1]['count'], reverse=True)
    return [album_data[album_key] for album_key, _ in sorted_albums[:limit]]

def get_artist_genres(token, artist_id):
    headers = {
        'Authorization': f'Bearer {token}'
    }
    response = requests.get(f'https://api.spotify.com/v1/artists/{artist_id}', headers=headers)
    
    if response.status_code != 200:
        print(f"Error getting artist genres: {response.status_code}")
        return []
        
    data = response.json()
    return data.get('genres', [])

def get_user_top_genres(token, limit=10, time_range='medium_term'):
    """
    Get user's top genres based on their top artists for a specific time range
    """
    headers = {
        'Authorization': f'Bearer {token}'
    }
    response = requests.get(
        f'https://api.spotify.com/v1/me/top/artists?limit={limit}&time_range={time_range}',
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"Error getting top artists: {response.status_code}")
        return []
        
    data = response.json()
    all_genres = []
    
    # Collect genres from top artists
    for artist in data['items']:
        all_genres.extend(artist.get('genres', []))
    
    # Count genre occurrences
    genre_count = {}
    for genre in all_genres:
        genre_count[genre] = genre_count.get(genre, 0) + 1
    
    # Sort genres by frequency and return top ones
    sorted_genres = sorted(genre_count.items(), key=lambda x: x[1], reverse=True)
    return [genre for genre, count in sorted_genres[:limit]]

def search_spotify_artists(token, query, limit=10):
    """Search for artists on Spotify"""
    headers = {
        'Authorization': f'Bearer {token}'
    }
    response = requests.get(
        f'https://api.spotify.com/v1/search?q={query}&type=artist&limit={limit}',
        headers=headers
    )
    
    if response.status_code != 200:
        return []
        
    data = response.json()
    artists = []
    for artist in data['artists']['items']:
        artists.append({
            'id': artist['id'],
            'name': artist['name'],
            'popularity': artist['popularity'],
            'genres': artist['genres'],
            'images': artist['images']
        })
    return artists

def search_spotify_tracks(token, query, limit=10):
    """Search for tracks on Spotify"""
    headers = {
        'Authorization': f'Bearer {token}'
    }
    response = requests.get(
        f'https://api.spotify.com/v1/search?q={query}&type=track&limit={limit}',
        headers=headers
    )
    
    if response.status_code != 200:
        return []
        
    data = response.json()
    tracks = []
    for track in data['tracks']['items']:
        tracks.append({
            'id': track['id'],
            'name': track['name'],
            'artist': track['artists'][0]['name'],
            'album': track['album']['name'],
            'album_art': track['album']['images'][0]['url'] if track['album']['images'] else None,
            'popularity': track['popularity'],
            'duration_ms': track['duration_ms']
        })
    return tracks

def search_spotify_albums(token, query, limit=10):
    """Search for albums on Spotify"""
    headers = {
        'Authorization': f'Bearer {token}'
    }
    response = requests.get(
        f'https://api.spotify.com/v1/search?q={query}&type=album&limit={limit}',
        headers=headers
    )
    
    if response.status_code != 200:
        return []
        
    data = response.json()
    albums = []
    for album in data['albums']['items']:
        albums.append({
            'id': album['id'],
            'name': album['name'],
            'artist': album['artists'][0]['name'],
            'release_date': album['release_date'],
            'art_url': album['images'][0]['url'] if album['images'] else None,
            'popularity': album.get('popularity', 0)
        })
    return albums

def search_spotify_genres(token, query, limit=10):
    """Search for genres by searching artists and extracting genres"""
    headers = {
        'Authorization': f'Bearer {token}'
    }
    response = requests.get(
        f'https://api.spotify.com/v1/search?q={query}&type=artist&limit=50',
        headers=headers
    )
    
    if response.status_code != 200:
        return []
        
    data = response.json()
    all_genres = []
    for artist in data['artists']['items']:
        all_genres.extend(artist.get('genres', []))
    
    # Filter genres that contain the query
    matching_genres = [genre for genre in all_genres if query.lower() in genre.lower()]
    
    # Remove duplicates and return unique genres
    unique_genres = list(set(matching_genres))
    return unique_genres[:limit]

def update_discord_presence(track_info):
    if not track_info:
        return
        
    artist_name = track_info['artists'][0] if track_info['artists'] else "Unknown Artist"
    album_art_url = track_info['album']['images'][0]['url'] if track_info['album']['images'] else None
    
    discord_rpc.update(
        state=f"Listening to {track_info['name']}",
        details=f"by {artist_name}",
        large_image=album_art_url,
        large_text=track_info['name']
    )

def get_recently_played(token, limit=10):
    """Fetch recently played tracks from Spotify API."""
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(f'https://api.spotify.com/v1/me/player/recently-played?limit={limit}', headers=headers)
    if response.status_code != 200:
        print(f"Error getting recently played: {response.status_code}")
        return []
    data = response.json()
    tracks = []
    for item in data.get('items', []):
        track = item['track']
        tracks.append({
            'name': track['name'],
            'artist': ', '.join([a['name'] for a in track['artists']]),
            'album': track['album']['name'],
            'album_art': track['album']['images'][0]['url'] if track['album']['images'] else None,
            'played_at': item['played_at']
        })
    return tracks

class SpotifyApp:
    def __init__(self, root):
        self.root = root
        setup_theme(self.root)
        # Gradient background
        self.bg_canvas = tk.Canvas(self.root, width=800, height=600, highlightthickness=0)
        self.bg_canvas.pack(fill='both', expand=True)
        self.gradient_img = create_vertical_gradient(800, 600, '#FFE4EC', '#39D353')
        self.bg_canvas.create_image(0, 0, anchor='nw', image=self.gradient_img)
        # Place main frame on top
        self.main_frame = tk.Frame(self.root, bg='#FFF0F6')
        self.main_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.root.title("🎵 TasteMate - Music Dating App 💚")
        self.root.geometry("800x600")
        
        # Initialize variables
        self.current_token = None
        self.refresh_token = None
        self.update_thread = None
        self.is_running = True
        self.last_track_id = None
        self.session_token = None
        self.preloaded_top_items = None  # Cache for preloaded data
        
        # Initialize auth manager
        self.auth_manager = AuthManager()
        
        # Show login/signup window first
        auth_window = AuthWindow(root)
        
        # Check if auto-login occurred
        if auth_window.user_id is None:
            # No remembered user, wait for manual login
            root.wait_window(auth_window.window)
            self.current_user_id = auth_window.get_user_id()
            self.session_token = auth_window.get_session_token()
        else:
            # Auto-login with remembered user
            self.current_user_id = auth_window.user_id
            self.session_token = auth_window.session_token
            
        if not self.current_user_id:
            root.destroy()
            return
            
        # Initialize the app after successful login
        self.initialize_app_after_login()

    def initialize_app_after_login(self):
        """Initialize the app after successful login"""
        # Initialize time range settings
        self.current_time_range = 'medium_term'  # Default to 6 months
        self.time_range_map = {
            'short_term': 'Past Month',
            'medium_term': 'Past 6 Months',
            'long_term': 'All Time'
        }
        
        # Initialize profile manager
        self.profile_manager = UserProfileManager()
        
        # Check if profile setup is needed
        self.check_profile_setup()
        
        # Clear any existing UI elements completely
        for widget in self.root.winfo_children():
            widget.destroy()
        # Destroy main_frame if it exists
        if hasattr(self, 'main_frame') and self.main_frame is not None:
            try:
                self.main_frame.destroy()
            except:
                pass
        # Recreate main_frame
        self.main_frame = tk.Frame(self.root, bg='#FFF0F6')
        self.main_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        # Recreate gradient background
        self.bg_canvas = tk.Canvas(self.root, width=800, height=600, highlightthickness=0)
        self.bg_canvas.pack(fill='both', expand=True)
        self.gradient_img = create_vertical_gradient(800, 600, '#FFE4EC', '#39D353')
        self.bg_canvas.create_image(0, 0, anchor='nw', image=self.gradient_img)
        self.main_frame.lift()
        self.root.title("🎵 TasteMate - Music Dating App 💚")
        self.root.geometry("800x600")
        
        # Create main notebook for tabs
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=5)
        
        # Create tabs
        self.now_playing_tab = ttk.Frame(self.notebook)
        self.profile_tab = ttk.Frame(self.notebook)
        self.matches_tab = ttk.Frame(self.notebook)
        self.taste_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.now_playing_tab, text='Now Playing')
        self.notebook.add(self.profile_tab, text='My Profile')
        self.notebook.add(self.matches_tab, text='Matches')
        self.notebook.add(self.taste_tab, text='My Taste')
        
        self.setup_now_playing_tab()
        self.setup_profile_tab()
        self.setup_matches_tab()
        self.setup_taste_tab()
        
        # Load existing profile if available
        profile = self.profile_manager.load_profile(self.current_user_id)
        if profile:
            self.update_profile_display(profile)
        
        # Get Spotify token and user info
        self.setup_spotify()

    def check_profile_setup(self):
        """Check if user needs to complete profile setup"""
        profile = self.profile_manager.load_profile(self.current_user_id)
        
        # Check if profile is incomplete (missing basic info)
        if not profile or not profile.first_name or not profile.last_name:
            # Show profile setup window
            setup_window = ProfileSetupWindow(self.root, self.current_user_id, self.profile_manager)
            self.root.wait_window(setup_window.window)
            
            # Reload profile after setup
            profile = self.profile_manager.load_profile(self.current_user_id)

    def setup_spotify(self):
        """Setup Spotify connection"""
        try:
            # Clear any existing tokens first
            self.current_token = None
            self.refresh_token = None
            
            # Reconnect Discord RPC for new user
            try:
                discord_rpc.close()
                discord_rpc.connect()
            except:
                pass  # Ignore Discord connection errors
            
            # Get new tokens
            token, refresh_token = get_spotify_token()
            self.current_token = token
            self.refresh_token = refresh_token

            # Preload top items for short_term (most recent)
            self.preloaded_top_items = self.preload_top_items(token)

            # Update search functions with new token
            self.update_search_functions()
            
            # Get user profile
            headers = {'Authorization': f'Bearer {token}'}
            response = requests.get('https://api.spotify.com/v1/me', headers=headers)
            if response.status_code == 200:
                user_data = response.json()
                # Update profile with Spotify username if not set
                profile = self.profile_manager.load_profile(self.current_user_id)
                if profile and not profile.username:
                    profile.username = user_data['display_name']
                    self.profile_manager.save_profile(profile)
                    self.update_profile_display(profile)
            
            # Start the update thread
            self.start_update_thread()
            
            # Test search functionality
            self.test_search_functionality()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to connect to Spotify: {str(e)}")
            self.root.destroy()

    def preload_top_items(self, token):
        """Preload top songs, artists, genres, and albums for short_term."""
        return {
            'top_artists': get_user_top_items(token, 'artists', time_range='short_term'),
            'top_genres': get_user_top_genres(token, time_range='short_term'),
            'top_songs': get_user_top_items(token, 'tracks', time_range='short_term'),
            'top_albums': get_user_top_albums(token, time_range='short_term')
        }

    def test_search_functionality(self):
        """Test if search functionality is working"""
        try:
            if self.current_token:
                # Test a simple search
                test_results = search_spotify_artists(self.current_token, "test")
                print(f"Search functionality test: {len(test_results)} results for 'test'")
            else:
                print("No token available for search test")
        except Exception as e:
            print(f"Search functionality test failed: {e}")

    def update_search_functions(self):
        """Update search functions with current token"""
        if not self.current_token:
            return
            
        try:
            # Update search functions for each dropdown
            search_functions = {
                'artists': lambda query: search_spotify_artists(self.current_token, query),
                'songs': lambda query: search_spotify_tracks(self.current_token, query),
                'genres': lambda query: search_spotify_genres(self.current_token, query),
                'albums': lambda query: search_spotify_albums(self.current_token, query)
            }
            
            # Update each search dropdown
            for favorite_type, search_func in search_functions.items():
                search_dropdown = getattr(self, f"{favorite_type}_search", None)
                if search_dropdown:
                    search_dropdown.search_function = search_func
                    print(f"Updated {favorite_type} search function")
        except Exception as e:
            print(f"Error updating search functions: {e}")

    def setup_now_playing_tab(self):
        # Now Playing tab content
        for widget in self.now_playing_tab.winfo_children():
            widget.destroy()
        # Bubbly header
        header = tk.Label(self.now_playing_tab, text="🎧 Now Playing", font=('Poppins', 22, 'bold'), bg='#FFE4EC', fg='#39D353')
        header.pack(pady=(30, 10))
        # Bubbly profile card for user
        profile = self.profile_manager.load_profile(self.current_user_id)
        card = create_profile_card(self.now_playing_tab, profile)
        card.pack(pady=10)
        # Track info area
        self.track_label = tk.Label(self.now_playing_tab, text="Current Track", font=('Poppins', 16, 'bold'), bg='#FFE4EC', fg='#222')
        self.track_label.pack(pady=10)
        self.canvas = tk.Canvas(self.now_playing_tab, width=220, height=220, bg='#FFE4EC', highlightthickness=0)
        self.canvas.pack(pady=10)
        # Rating area
        self.rating_frame = tk.Frame(self.now_playing_tab, bg='#FFE4EC')
        self.rating_frame.pack(pady=10)
        self.rating_label = tk.Label(self.rating_frame, text="Rate this track:", bg='#FFE4EC', font=('Poppins', 12))
        self.rating_label.pack(side=tk.LEFT)
        self.rating_var = tk.DoubleVar(value=0.5)
        self.rating_scale = tk.Scale(self.rating_frame, from_=0, to=1, resolution=0.1,
                                   orient=tk.HORIZONTAL, variable=self.rating_var, bg='#FFE4EC', highlightthickness=0, length=120)
        self.rating_scale.pack(side=tk.LEFT, padx=5)
        # Bubbly Save Rating button
        self.save_rating_btn = BubblyButton(self.rating_frame, text="💾 Save Rating", command=self.save_track_rating)
        self.save_rating_btn.pack(side=tk.LEFT, padx=10)

    def setup_profile_tab(self):
        # Profile tab content
        for widget in self.profile_tab.winfo_children():
            widget.destroy()
        header = tk.Label(self.profile_tab, text="🎵 My Music Profile", font=('Poppins', 22, 'bold'), bg='#FFE4EC', fg='#39D353')
        header.pack(pady=(30, 10))
        # Bubbly profile card
        profile = self.profile_manager.load_profile(self.current_user_id)
        card = create_profile_card(self.profile_tab, profile)
        card.pack(pady=10)
        # ... (rest of the profile tab UI as before, but with more padding and rounded frames if possible)

    def setup_matches_tab(self):
        # Matches tab content
        self.matches_frame = ttk.Frame(self.matches_tab)
        self.matches_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.matches_list = tk.Listbox(self.matches_frame)
        self.matches_list.pack(fill='both', expand=True)
        
        self.refresh_matches_btn = tk.Button(self.matches_frame, text="Refresh Matches",
                                           command=self.refresh_matches)
        self.refresh_matches_btn.pack(pady=5)

    def setup_taste_tab(self):
        # Create main frame
        header = create_header(self.taste_tab, "💚 My Taste")
        taste_frame = ttk.Frame(self.taste_tab)
        taste_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Create scrollable frame
        canvas = tk.Canvas(taste_frame)
        scrollbar = ttk.Scrollbar(taste_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Create sections for different types of favorites
        sections = [
            ("Favorite Artists (your picks)", "artists", self.get_artist_search_function()),
            ("Favorite Songs (your picks)", "songs", self.get_song_search_function()),
            ("Favorite Genres (your picks)", "genres", self.get_genre_search_function()),
            ("Favorite Albums (your picks)", "albums", self.get_album_search_function())
        ]
        
        for title, section_type, search_func in sections:
            section_frame = ttk.LabelFrame(scrollable_frame, text=title)
            section_frame.pack(fill='x', pady=5, padx=5)
            
            # Create input frame
            input_frame = ttk.Frame(section_frame)
            input_frame.pack(fill='x', padx=5, pady=5)
            
            # Create search dropdown
            search_dropdown = SpotifySearchDropdown(input_frame, search_func, placeholder=f"Search {title.lower()}...", width=35)
            search_dropdown.frame.pack(side=tk.LEFT, fill='x', expand=True, padx=(0, 5))
            
            # Add button
            add_btn = ttk.Button(
                input_frame,
                text="Add",
                command=lambda sd=search_dropdown, t=section_type: self.add_favorite_from_search(sd, t)
            )
            add_btn.pack(side=tk.LEFT)
            
            # Create listbox for favorites, use different attribute names
            listbox = tk.Listbox(section_frame, height=4)
            listbox.pack(fill='x', padx=5, pady=5)
            
            # Add remove button
            remove_btn = ttk.Button(
                section_frame,
                text="Remove Selected",
                command=lambda l=listbox, t=section_type: self.remove_favorite(l, t)
            )
            remove_btn.pack(pady=5)
            
            # Store references for favorites with different names
            setattr(self, f"favorite_{section_type}_search", search_dropdown)
            setattr(self, f"favorite_{section_type}_list", listbox)
        
        # Add save button
        save_btn = ttk.Button(
            scrollable_frame,
            text="Save Preferences",
            command=self.save_preferences
        )
        save_btn.pack(pady=10)
        
        # Load existing preferences after a short delay to ensure UI is ready
        self.root.after(100, self.load_preferences)

    def get_artist_search_function(self):
        """Get artist search function"""
        def search_artists(query):
            if self.current_token:
                try:
                    results = search_spotify_artists(self.current_token, query)
                    print(f"Artist search for '{query}': {len(results)} results")
                    return results
                except Exception as e:
                    print(f"Artist search error: {e}")
                    return []
            else:
                print("No Spotify token available for artist search")
                return []
        return search_artists

    def get_song_search_function(self):
        """Get song search function"""
        def search_songs(query):
            if self.current_token:
                try:
                    results = search_spotify_tracks(self.current_token, query)
                    print(f"Song search for '{query}': {len(results)} results")
                    return results
                except Exception as e:
                    print(f"Song search error: {e}")
                    return []
            else:
                print("No Spotify token available for song search")
                return []
        return search_songs

    def get_genre_search_function(self):
        """Get genre search function"""
        def search_genres(query):
            if self.current_token:
                try:
                    results = search_spotify_genres(self.current_token, query)
                    print(f"Genre search for '{query}': {len(results)} results")
                    return results
                except Exception as e:
                    print(f"Genre search error: {e}")
                    return []
            else:
                print("No Spotify token available for genre search")
                return []
        return search_genres

    def get_album_search_function(self):
        """Get album search function"""
        def search_albums(query):
            if self.current_token:
                try:
                    results = search_spotify_albums(self.current_token, query)
                    print(f"Album search for '{query}': {len(results)} results")
                    return results
                except Exception as e:
                    print(f"Album search error: {e}")
                    return []
            else:
                print("No Spotify token available for album search")
                return []
        return search_albums

    def on_time_range_change(self, selected_range):
        """Handle time range selection change"""
        # Find the key for the selected range
        for key, value in self.time_range_map.items():
            if value == selected_range:
                self.current_time_range = key
                break
        
        # Update the profile display with new time range
        if self.current_token and self.current_user_id:
            profile = self.profile_manager.load_profile(self.current_user_id)
            if profile:
                # Update top items with new time range
                profile.top_artists = get_user_top_items(
                    self.current_token,
                    'artists',
                    time_range=self.current_time_range
                )
                profile.top_genres = get_user_top_genres(
                    self.current_token,
                    time_range=self.current_time_range
                )
                profile.top_songs = get_user_top_items(
                    self.current_token,
                    'tracks',
                    time_range=self.current_time_range
                )
                profile.top_albums = get_user_top_albums(
                    self.current_token,
                    time_range=self.current_time_range
                )
                self.update_profile_display(profile)

    def save_track_rating(self):
        if not self.current_token or not self.current_user_id:
            return
            
        track_info = get_current_playing(self.current_token)
        if not track_info:
            return
            
        # Create or load user profile
        profile = self.profile_manager.load_profile(self.current_user_id)
        if not profile:
            profile = UserProfile(
                user_id=self.current_user_id,
                username="T0RA",
                music_preferences=[],
                top_artists=[],
                top_genres=[],
                top_songs=[],
                top_albums=[]
            )
        
        # Add or update track rating
        track_preference = MusicPreference(
            track_id=track_info.get('id', ''),
            name=track_info['name'],
            artists=track_info['artists'],
            album=track_info['album']['name'],
            rating=self.rating_var.get()
        )
        
        # Update or add preference
        for i, pref in enumerate(profile.music_preferences):
            if pref.track_id == track_preference.track_id:
                profile.music_preferences[i] = track_preference
                break
        else:
            profile.music_preferences.append(track_preference)
        
        # Update top items with current time range
        profile.top_artists = get_user_top_items(
            self.current_token,
            'artists',
            time_range=self.current_time_range
        )
        profile.top_genres = get_user_top_genres(
            self.current_token,
            time_range=self.current_time_range
        )
        profile.top_songs = get_user_top_items(
            self.current_token,
            'tracks',
            time_range=self.current_time_range
        )
        profile.top_albums = get_user_top_albums(
            self.current_token,
            time_range=self.current_time_range
        )
        
        # Save profile
        self.profile_manager.save_profile(profile)
        self.update_profile_display(profile)

    def update_profile_display(self, profile):
        # Only update bubbly card and lists, not old personal info widgets
        # (self.update_personal_info_display is no longer needed)
        # If you want to update other UI elements, do so here
        pass

    def refresh_matches(self):
        if not self.current_user_id:
            return
            
        matches = self.profile_manager.find_matches(self.current_user_id)
        self.matches_list.delete(0, tk.END)
        
        for profile, score in matches:
            self.matches_list.insert(tk.END, f"{profile.username} - Compatibility: {score:.1%}")

    def update_ui(self, track_info):
        if not track_info:
            self.track_label.config(text="No track currently playing")
            return
            
        artist_name = track_info['artists'][0] if track_info['artists'] else "Unknown Artist"
        self.track_label.config(text=f"{track_info['name']} by {artist_name}")
        
        if track_info['album']['images']:
            try:
                print(f"Loading album art from: {track_info['album']['images'][0]['url']}")
                response = requests.get(track_info['album']['images'][0]['url'])
                img_data = response.content
                img = Image.open(io.BytesIO(img_data))
                img = img.resize((300, 300), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.canvas.create_image(0, 0, anchor=tk.NW, image=photo)
                self.canvas.image = photo  # Keep a reference
                print("Album art loaded successfully")
            except Exception as e:
                print(f"Error loading album art: {e}")
                print(f"Response content: {response.content[:100]}")  # Print first 100 bytes of response

    def start_update_thread(self):
        """Start the background thread for updating current playing track"""
        self.update_thread = threading.Thread(target=self.update_current_playing)
        self.update_thread.daemon = True  # Thread will exit when main program exits
        self.update_thread.start()

    def stop_update_thread(self):
        """Stop the background thread"""
        self.is_running = False
        if self.update_thread:
            self.update_thread.join()

    def update_current_playing(self):
        """Background thread function to continuously update current playing track"""
        while self.is_running:
            if self.current_token:
                try:
                    track_info = get_current_playing(self.current_token)
                    if track_info:
                        # Only update if the track has changed
                        current_track_id = track_info.get('id')
                        if current_track_id != self.last_track_id:
                            self.last_track_id = current_track_id
                            # Use after() to safely update UI from the main thread
                            self.root.after(0, lambda: self.update_ui(track_info))
                            self.root.after(0, lambda: update_discord_presence(track_info))
                except Exception as e:
                    print(f"Error in update_current_playing: {e}")
                    # Try to refresh the token
                    if self.refresh_token:
                        try:
                            self.current_token = refresh_spotify_token(self.refresh_token)
                            print("Token refreshed successfully")
                        except Exception as refresh_error:
                            print(f"Error refreshing token: {refresh_error}")
            time.sleep(2)  # Check every 2 seconds

    def __del__(self):
        """Cleanup when the app is closed"""
        self.stop_update_thread()

    def load_album_art(self, url, size=(50, 50)):
        """Load and resize album art from URL"""
        try:
            response = requests.get(url)
            img = Image.open(io.BytesIO(response.content))
            img = img.resize(size, Image.LANCZOS)
            return ImageTk.PhotoImage(img)
        except Exception as e:
            print(f"Error loading album art: {e}")
            return None

    def add_favorite_from_search(self, search_dropdown, favorite_type):
        """Add a favorite from the search dropdown"""
        value = search_dropdown.get_value()
        if not value:
            return
            
        listbox = getattr(self, f"favorite_{favorite_type}_list")
        
        # Check if already exists
        existing_items = list(listbox.get(0, tk.END))
        if value in existing_items:
            messagebox.showwarning("Warning", f"This {favorite_type[:-1]} is already in your favorites!")
            return
            
        listbox.insert(tk.END, value)
        search_dropdown.clear()
        
        # Auto-save preferences
        self.save_preferences()

    def remove_favorite(self, listbox, favorite_type):
        """Remove selected favorite item"""
        selection = listbox.curselection()
        if selection:
            listbox.delete(selection)
            # Auto-save preferences
            self.save_preferences()

    def save_preferences(self):
        """Save all favorite preferences"""
        if not self.current_user_id:
            return
        profile = self.profile_manager.load_profile(self.current_user_id)
        if not profile:
            return
        try:
            profile.favorite_artists = list(self.favorite_artists_list.get(0, tk.END))
            profile.favorite_songs = list(self.favorite_songs_list.get(0, tk.END))
            profile.favorite_genres = list(self.favorite_genres_list.get(0, tk.END))
            profile.favorite_albums = list(self.favorite_albums_list.get(0, tk.END))
            self.profile_manager.save_profile(profile)
            messagebox.showinfo("Success", "Preferences saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save preferences: {str(e)}")

    def load_preferences(self):
        """Load saved preferences"""
        if not self.current_user_id:
            return
        profile = self.profile_manager.load_profile(self.current_user_id)
        if not profile:
            return
        try:
            for item in profile.favorite_artists:
                self.favorite_artists_list.insert(tk.END, item)
            for item in profile.favorite_songs:
                self.favorite_songs_list.insert(tk.END, item)
            for item in profile.favorite_genres:
                self.favorite_genres_list.insert(tk.END, item)
            for item in profile.favorite_albums:
                self.favorite_albums_list.insert(tk.END, item)
        except Exception as e:
            print(f"Error loading preferences: {e}")

    def logout(self):
        """Logout current user and show login window again"""
        # Stop the update thread
        self.stop_update_thread()
        
        # Clear Discord presence
        try:
            discord_rpc.clear()
        except:
            pass  # Ignore errors if Discord RPC is not connected
        
        # Delete current session
        if self.session_token:
            self.auth_manager.delete_session(self.session_token)
        
        # Clear current user data
        self.current_user_id = None
        self.current_token = None
        self.refresh_token = None
        self.session_token = None
        
        # Clear the main window
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Reset all instance variables
        self.reset_app_state()
        
        # Show login window again
        auth_window = AuthWindow(self.root)
        
        # Check if auto-login occurred
        if auth_window.user_id is None:
            # No remembered user, wait for manual login
            self.root.wait_window(auth_window.window)
            new_user_id = auth_window.get_user_id()
            new_session_token = auth_window.get_session_token()
        else:
            # Auto-login with remembered user
            new_user_id = auth_window.user_id
            new_session_token = auth_window.session_token
            
        if not new_user_id:
            self.root.destroy()
            return
        
        # Reinitialize the app with new user
        self.current_user_id = new_user_id
        self.session_token = new_session_token
        self.initialize_app_after_login()

    def forget_me(self):
        """Forget the current user and clear all sessions"""
        # Stop the update thread
        self.stop_update_thread()
        
        # Clear Discord presence
        try:
            discord_rpc.clear()
        except:
            pass  # Ignore errors if Discord RPC is not connected
        
        # Delete all sessions for current user
        if self.session_token:
            self.auth_manager.delete_session(self.session_token)
        
        # Clear current user data
        self.current_user_id = None
        self.current_token = None
        self.refresh_token = None
        self.session_token = None
        
        # Clear the main window
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Reset all instance variables
        self.reset_app_state()
        
        # Show login window again (will not auto-login)
        auth_window = AuthWindow(self.root)
        self.root.wait_window(auth_window.window)
        
        new_user_id = auth_window.get_user_id()
        new_session_token = auth_window.get_session_token()
        
        if not new_user_id:
            self.root.destroy()
            return
        
        # Reinitialize the app with new user
        self.current_user_id = new_user_id
        self.session_token = new_session_token
        self.initialize_app_after_login()

    def reset_app_state(self):
        """Reset all application state variables"""
        # Reset Spotify-related variables
        self.current_token = None
        self.refresh_token = None
        self.last_track_id = None
        
        # Reset UI-related variables
        self.current_time_range = 'medium_term'
        self.time_range_map = {
            'short_term': 'Past Month',
            'medium_term': 'Past 6 Months',
            'long_term': 'All Time'
        }
        
        # Reset profile manager
        self.profile_manager = UserProfileManager()
        
        # Reset thread state
        self.is_running = True
        self.update_thread = None
        
        # Clear any existing UI elements
        self.track_label = None
        self.canvas = None
        self.rating_frame = None
        self.rating_label = None
        self.rating_scale = None
        self.save_rating_btn = None
        self.notebook = None
        self.now_playing_tab = None
        self.profile_tab = None
        self.matches_tab = None
        self.taste_tab = None
        
        # Clear search dropdowns
        self.artists_search = None
        self.songs_search = None
        self.genres_search = None
        self.albums_search = None
        self.favorite_artists_list = None
        self.favorite_songs_list = None
        self.favorite_genres_list = None
        self.favorite_albums_list = None

    def edit_profile(self):
        """Open profile setup window for editing"""
        setup_window = ProfileSetupWindow(self.root, self.current_user_id, self.profile_manager)
        self.root.wait_window(setup_window.window)
        
        # Reload and update profile display after editing
        profile = self.profile_manager.load_profile(self.current_user_id)
        if profile:
            self.update_profile_display(profile)

    def open_account_settings(self):
        from account_settings import AccountSettingsWindow
        AccountSettingsWindow(self.root, self.current_user_id, self.auth_manager, app=self)

    def import_spotify_data(self):
        """Open file dialog to import Spotify account/listening history JSON and update user profile. Supports selecting a folder of JSON files."""
        # Ask user to select files or a folder
        file_paths = filedialog.askopenfilenames(
            title="Select Spotify Data JSON Files",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        # Optionally, allow folder selection
        folder_path = filedialog.askdirectory(title="Or select a folder of JSON files (optional)")
        all_json_files = list(file_paths)
        if folder_path:
            for fname in os.listdir(folder_path):
                if fname.lower().endswith('.json'):
                    all_json_files.append(os.path.join(folder_path, fname))
        if not all_json_files:
            return
        
        # Load and parse all selected files
        all_history = []
        for file_path in all_json_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                # Try to extract listening history from known Spotify formats
                if isinstance(data, list):
                    # Extended listening history (array of play events)
                    all_history.extend(data)
                elif isinstance(data, dict):
                    # Account data or technical log
                    if 'listening_history' in data:
                        all_history.extend(data['listening_history'])
                    elif 'plays' in data:
                        all_history.extend(data['plays'])
                    elif 'events' in data:
                        all_history.extend(data['events'])
                    elif 'track_playback' in data:
                        all_history.extend(data['track_playback'])
                    # Add more keys as needed for other Spotify export formats
            except Exception as e:
                messagebox.showerror("Error", f"Failed to parse {os.path.basename(file_path)}: {e}")
                return
        if not all_history:
            messagebox.showwarning("No Data", "No listening history found in the selected files or folder.")
            return
        # Merge into user profile
        profile = self.profile_manager.load_profile(self.current_user_id)
        if not profile:
            messagebox.showerror("Error", "User profile not found.")
            return
        # Parse and add to music_preferences, top_artists, top_songs, top_albums, top_genres
        track_counts = {}
        artist_counts = {}
        album_counts = {}
        genre_counts = {}
        # Helper: get or create MusicPreference
        def get_pref(track_id, name, artists, album):
            for p in profile.music_preferences:
                if p.track_id == track_id:
                    return p
            return MusicPreference(track_id=track_id, name=name, artists=artists, album=album, rating=0.5)
        for event in all_history:
            # Try to extract fields from various Spotify formats
            track_name = event.get('trackName') or event.get('track_name') or event.get('songName') or event.get('name')
            artist_name = event.get('artistName') or event.get('artist_name') or event.get('artist')
            album_name = event.get('albumName') or event.get('album_name') or event.get('album')
            track_id = event.get('spotifyTrackUri') or event.get('trackId') or event.get('track_id') or event.get('spotify_track_uri') or ''
            genres = event.get('genres', [])
            if not track_name or not artist_name:
                continue
            # Update counts
            track_key = (track_id, track_name, artist_name, album_name)
            track_counts[track_key] = track_counts.get(track_key, 0) + 1
            artist_counts[artist_name] = artist_counts.get(artist_name, 0) + 1
            if album_name:
                album_counts[album_name] = album_counts.get(album_name, 0) + 1
            for genre in genres:
                genre_counts[genre] = genre_counts.get(genre, 0) + 1
            # Add to music_preferences if not present
            pref = get_pref(track_id, track_name, [artist_name], album_name or "")
            if pref not in profile.music_preferences:
                profile.music_preferences.append(pref)
        # Update top lists
        profile.top_artists = [a for a, _ in sorted(artist_counts.items(), key=lambda x: x[1], reverse=True)[:10]]
        profile.top_songs = [{
            'name': t[1],
            'artist': t[2],
            'album': t[3],
            'album_art': None,
            'release_date': None,
            'popularity': None
        } for t, _ in sorted(track_counts.items(), key=lambda x: x[1], reverse=True)[:10]]
        profile.top_albums = [{
            'name': a,
            'artist': None,
            'art_url': None,
            'release_date': None,
            'count': c
        } for a, c in sorted(album_counts.items(), key=lambda x: x[1], reverse=True)[:10]]
        profile.top_genres = [g for g, _ in sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:10]]
        # Save and reload
        self.profile_manager.save_profile(profile)
        self.update_profile_display(profile)
        messagebox.showinfo("Success", "Spotify data imported and profile updated!")

if __name__ == "__main__":
    root = tk.Tk()
    app = SpotifyApp(root)
    root.mainloop() 