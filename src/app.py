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

class SpotifyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Music Dating App")
        self.root.geometry("800x600")
        
        # Initialize variables
        self.current_token = None
        self.refresh_token = None
        self.update_thread = None
        self.is_running = True
        self.last_track_id = None
        self.session_token = None
        
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
        
        # Create main notebook for tabs
        self.notebook = ttk.Notebook(self.root)
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
        self.track_label = tk.Label(self.now_playing_tab, text="Current Track", font=('Arial', 14))
        self.track_label.pack(pady=10)
        
        self.canvas = tk.Canvas(self.now_playing_tab, width=300, height=300)
        self.canvas.pack(pady=10)
        
        self.rating_frame = tk.Frame(self.now_playing_tab)
        self.rating_frame.pack(pady=10)
        
        self.rating_label = tk.Label(self.rating_frame, text="Rate this track:")
        self.rating_label.pack(side=tk.LEFT)
        
        self.rating_var = tk.DoubleVar(value=0.5)
        self.rating_scale = tk.Scale(self.rating_frame, from_=0, to=1, resolution=0.1,
                                   orient=tk.HORIZONTAL, variable=self.rating_var)
        self.rating_scale.pack(side=tk.LEFT, padx=5)
        
        self.save_rating_btn = tk.Button(self.rating_frame, text="Save Rating",
                                       command=self.save_track_rating)
        self.save_rating_btn.pack(side=tk.LEFT, padx=5)

    def setup_profile_tab(self):
        # Profile tab content
        self.profile_frame = ttk.LabelFrame(self.profile_tab, text="My Music Profile")
        self.profile_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Add logout button and welcome message at the top
        logout_frame = ttk.Frame(self.profile_frame)
        logout_frame.pack(fill='x', padx=5, pady=5)
        
        # Get user data for welcome message
        user_data = self.auth_manager.get_user_data(self.current_user_id)
        if user_data:
            welcome_label = ttk.Label(logout_frame, text=f"Welcome, {user_data['username']}!", 
                                    font=('Arial', 12, 'bold'))
            welcome_label.pack(side=tk.LEFT, padx=5)
        
        # Add buttons on the right
        button_frame = ttk.Frame(logout_frame)
        button_frame.pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(button_frame, text="Edit Profile", command=self.edit_profile).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Forget Me", command=self.forget_me).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Logout", command=self.logout).pack(side=tk.LEFT, padx=2)
        
        # Personal Information Section
        self.personal_info_frame = ttk.LabelFrame(self.profile_frame, text="Personal Information")
        self.personal_info_frame.pack(fill='x', padx=5, pady=5)
        
        # Profile picture and basic info
        basic_info_frame = ttk.Frame(self.personal_info_frame)
        basic_info_frame.pack(fill='x', padx=5, pady=5)
        
        # Profile picture
        self.profile_pic_canvas = tk.Canvas(basic_info_frame, width=100, height=100, bg='lightgray')
        self.profile_pic_canvas.pack(side=tk.LEFT, padx=5)
        self.profile_pic_canvas.create_text(50, 50, text="No photo", fill='gray')
        
        # Basic info
        self.basic_info_frame = ttk.Frame(basic_info_frame)
        self.basic_info_frame.pack(side=tk.LEFT, fill='x', expand=True, padx=10)
        
        self.name_label = ttk.Label(self.basic_info_frame, text="Name: Not set", font=('Arial', 10, 'bold'))
        self.name_label.pack(anchor='w')
        
        self.age_gender_label = ttk.Label(self.basic_info_frame, text="Age & Gender: Not set")
        self.age_gender_label.pack(anchor='w')
        
        self.location_label = ttk.Label(self.basic_info_frame, text="Location: Not set")
        self.location_label.pack(anchor='w')
        
        # Bio section
        bio_frame = ttk.Frame(self.personal_info_frame)
        bio_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(bio_frame, text="About me:", font=('Arial', 9, 'bold')).pack(anchor='w')
        self.bio_label = ttk.Label(bio_frame, text="No bio set", wraplength=400)
        self.bio_label.pack(anchor='w', pady=2)
        
        # Time range selection
        self.time_range_frame = ttk.Frame(self.profile_frame)
        self.time_range_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(self.time_range_frame, text="Time Range:").pack(side=tk.LEFT, padx=5)
        self.time_range_var = tk.StringVar(value=self.time_range_map[self.current_time_range])
        self.time_range_menu = ttk.OptionMenu(
            self.time_range_frame,
            self.time_range_var,
            self.time_range_map[self.current_time_range],
            *self.time_range_map.values(),
            command=self.on_time_range_change
        )
        self.time_range_menu.pack(side=tk.LEFT, padx=5)
        
        # Create a frame for the top items
        top_items_frame = ttk.Frame(self.profile_frame)
        top_items_frame.pack(fill='x', padx=5, pady=5)
        
        # Left column
        left_column = ttk.Frame(top_items_frame)
        left_column.pack(side=tk.LEFT, fill='both', expand=True, padx=5)
        
        # Top Artists
        self.artists_frame = ttk.LabelFrame(left_column, text="Top Artists")
        self.artists_frame.pack(fill='x', pady=5)
        self.artists_list = tk.Listbox(self.artists_frame, height=5)
        self.artists_list.pack(fill='x', padx=5, pady=5)
        
        # Top Genres
        self.genres_frame = ttk.LabelFrame(left_column, text="Top Genres")
        self.genres_frame.pack(fill='x', pady=5)
        self.genres_list = tk.Listbox(self.genres_frame, height=5)
        self.genres_list.pack(fill='x', padx=5, pady=5)
        
        # Right column
        right_column = ttk.Frame(top_items_frame)
        right_column.pack(side=tk.LEFT, fill='both', expand=True, padx=5)
        
        # Top Songs
        self.songs_frame = ttk.LabelFrame(right_column, text="Top Songs")
        self.songs_frame.pack(fill='x', pady=5)
        self.songs_canvas = tk.Canvas(self.songs_frame)
        self.songs_scrollbar = ttk.Scrollbar(self.songs_frame, orient="vertical", command=self.songs_canvas.yview)
        self.songs_scrollable_frame = ttk.Frame(self.songs_canvas)
        
        self.songs_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.songs_canvas.configure(scrollregion=self.songs_canvas.bbox("all"))
        )
        
        self.songs_canvas.create_window((0, 0), window=self.songs_scrollable_frame, anchor="nw")
        self.songs_canvas.configure(yscrollcommand=self.songs_scrollbar.set)
        
        self.songs_canvas.pack(side="left", fill="both", expand=True)
        self.songs_scrollbar.pack(side="right", fill="y")
        
        # Top Albums
        self.albums_frame = ttk.LabelFrame(right_column, text="Top Albums")
        self.albums_frame.pack(fill='x', pady=5)
        self.albums_canvas = tk.Canvas(self.albums_frame)
        self.albums_scrollbar = ttk.Scrollbar(self.albums_frame, orient="vertical", command=self.albums_canvas.yview)
        self.albums_scrollable_frame = ttk.Frame(self.albums_canvas)
        
        self.albums_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.albums_canvas.configure(scrollregion=self.albums_canvas.bbox("all"))
        )
        
        self.albums_canvas.create_window((0, 0), window=self.albums_scrollable_frame, anchor="nw")
        self.albums_canvas.configure(yscrollcommand=self.albums_scrollbar.set)
        
        self.albums_canvas.pack(side="left", fill="both", expand=True)
        self.albums_scrollbar.pack(side="right", fill="y")
        
        # Recent Ratings
        self.ratings_frame = ttk.LabelFrame(self.profile_frame, text="Recent Ratings")
        self.ratings_frame.pack(fill='both', expand=True, padx=5, pady=5)
        self.ratings_list = tk.Listbox(self.ratings_frame)
        self.ratings_list.pack(fill='both', expand=True, padx=5, pady=5)

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
            ("Favorite Artists", "artists", self.get_artist_search_function()),
            ("Favorite Songs", "songs", self.get_song_search_function()),
            ("Favorite Genres", "genres", self.get_genre_search_function()),
            ("Favorite Albums", "albums", self.get_album_search_function())
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
            
            # Create listbox for favorites
            listbox = tk.Listbox(section_frame, height=4)
            listbox.pack(fill='x', padx=5, pady=5)
            
            # Add remove button
            remove_btn = ttk.Button(
                section_frame,
                text="Remove Selected",
                command=lambda l=listbox, t=section_type: self.remove_favorite(l, t)
            )
            remove_btn.pack(pady=5)
            
            # Store references
            setattr(self, f"{section_type}_search", search_dropdown)
            setattr(self, f"{section_type}_list", listbox)
        
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
        # Update personal information
        self.update_personal_info_display(profile)
        
        # Update artists list
        self.artists_list.delete(0, tk.END)
        for artist in profile.top_artists:
            self.artists_list.insert(tk.END, artist)
        
        # Update genres list
        self.genres_list.delete(0, tk.END)
        for genre in profile.top_genres:
            self.genres_list.insert(tk.END, genre)
        
        # Clear existing song widgets
        for widget in self.songs_scrollable_frame.winfo_children():
            widget.destroy()
        
        # Update songs list with album art and details
        for song in profile.top_songs:
            song_frame = ttk.Frame(self.songs_scrollable_frame)
            song_frame.pack(fill='x', pady=2)
            
            if song['album_art']:
                art_img = self.load_album_art(song['album_art'])
                if art_img:
                    art_label = ttk.Label(song_frame, image=art_img)
                    art_label.image = art_img
                    art_label.pack(side=tk.LEFT, padx=5)
            
            info_frame = ttk.Frame(song_frame)
            info_frame.pack(side=tk.LEFT, fill='x', expand=True)
            
            ttk.Label(info_frame, text=f"{song['name']} - {song['artist']}", 
                     font=('Arial', 9, 'bold')).pack(anchor='w')
            ttk.Label(info_frame, text=f"Album: {song['album']} • Released: {song['release_date']} • Popularity: {song['popularity']}%",
                     font=('Arial', 8)).pack(anchor='w')
        
        # Clear existing album widgets
        for widget in self.albums_scrollable_frame.winfo_children():
            widget.destroy()
        
        # Update albums list with album art and details
        for album in profile.top_albums:
            album_frame = ttk.Frame(self.albums_scrollable_frame)
            album_frame.pack(fill='x', pady=2)
            
            if album['art_url']:
                art_img = self.load_album_art(album['art_url'])
                if art_img:
                    art_label = ttk.Label(album_frame, image=art_img)
                    art_label.image = art_img
                    art_label.pack(side=tk.LEFT, padx=5)
            
            info_frame = ttk.Frame(album_frame)
            info_frame.pack(side=tk.LEFT, fill='x', expand=True)
            
            ttk.Label(info_frame, text=f"{album['name']} - {album['artist']}", 
                     font=('Arial', 9, 'bold')).pack(anchor='w')
            ttk.Label(info_frame, text=f"Released: {album['release_date']} • Play Count: {album['count']}",
                     font=('Arial', 8)).pack(anchor='w')
        
        # Update ratings list
        self.ratings_list.delete(0, tk.END)
        for pref in profile.music_preferences:
            self.ratings_list.insert(tk.END, f"{pref.name} by {', '.join(pref.artists)} - Rating: {pref.rating:.1f}")

    def update_personal_info_display(self, profile):
        """Update the personal information display"""
        # Update profile picture
        if profile.profile_picture_path and os.path.exists(profile.profile_picture_path):
            try:
                with Image.open(profile.profile_picture_path) as img:
                    # Resize to 100x100
                    img.thumbnail((100, 100), Image.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    self.profile_pic_canvas.delete("all")
                    self.profile_pic_canvas.create_image(50, 50, image=photo)
                    self.profile_pic_canvas.image = photo  # Keep reference
            except Exception as e:
                print(f"Error loading profile picture: {e}")
                self.profile_pic_canvas.delete("all")
                self.profile_pic_canvas.create_text(50, 50, text="Error loading photo", fill='red')
        else:
            self.profile_pic_canvas.delete("all")
            self.profile_pic_canvas.create_text(50, 50, text="No photo", fill='gray')
        
        # Update name
        if profile.first_name and profile.last_name:
            self.name_label.config(text=f"Name: {profile.first_name} {profile.last_name}")
        elif profile.first_name:
            self.name_label.config(text=f"Name: {profile.first_name}")
        else:
            self.name_label.config(text="Name: Not set")
        
        # Update age and gender
        age_gender_parts = []
        if profile.age:
            age_gender_parts.append(f"Age: {profile.age}")
        if profile.gender:
            age_gender_parts.append(f"Gender: {profile.gender}")
        
        if age_gender_parts:
            self.age_gender_label.config(text=" • ".join(age_gender_parts))
        else:
            self.age_gender_label.config(text="Age & Gender: Not set")
        
        # Update location
        if profile.location:
            self.location_label.config(text=f"Location: {profile.location}")
        else:
            self.location_label.config(text="Location: Not set")
        
        # Update bio
        if profile.bio:
            self.bio_label.config(text=profile.bio)
        else:
            self.bio_label.config(text="No bio set")

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
            
        listbox = getattr(self, f"{favorite_type}_list")
        
        # Check if already exists
        existing_items = list(listbox.get(0, tk.END))
        if value in existing_items:
            messagebox.showwarning("Warning", f"This {favorite_type[:-1]} is already in your favorites!")
            return
            
        listbox.insert(tk.END, value)
        search_dropdown.clear()
        
        # Auto-save preferences
        self.save_preferences()

    def add_favorite(self, entry, favorite_type):
        """Add a new favorite item (legacy method)"""
        value = entry.get().strip()
        if not value:
            return
            
        listbox = getattr(self, f"{favorite_type}_list")
        
        # Check if already exists
        existing_items = list(listbox.get(0, tk.END))
        if value in existing_items:
            messagebox.showwarning("Warning", f"This {favorite_type[:-1]} is already in your favorites!")
            return
            
        listbox.insert(tk.END, value)
        entry.delete(0, tk.END)
        
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
            
        # Get all favorites from listboxes
        try:
            profile.favorite_artists = list(self.artists_list.get(0, tk.END))
            profile.favorite_songs = list(self.songs_list.get(0, tk.END))
            profile.favorite_genres = list(self.genres_list.get(0, tk.END))
            profile.favorite_albums = list(self.albums_list.get(0, tk.END))
            
            # Save profile
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
            # Load all favorites into listboxes
            for item in profile.favorite_artists:
                self.artists_list.insert(tk.END, item)
            for item in profile.favorite_songs:
                self.songs_list.insert(tk.END, item)
            for item in profile.favorite_genres:
                self.genres_list.insert(tk.END, item)
            for item in profile.favorite_albums:
                self.albums_list.insert(tk.END, item)
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
        self.artists_list = None
        self.songs_list = None
        self.genres_list = None
        self.albums_list = None

    def edit_profile(self):
        """Open profile setup window for editing"""
        setup_window = ProfileSetupWindow(self.root, self.current_user_id, self.profile_manager)
        self.root.wait_window(setup_window.window)
        
        # Reload and update profile display after editing
        profile = self.profile_manager.load_profile(self.current_user_id)
        if profile:
            self.update_profile_display(profile)

if __name__ == "__main__":
    root = tk.Tk()
    app = SpotifyApp(root)
    root.mainloop() 