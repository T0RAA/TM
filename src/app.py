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
import json
import os

# Spotify API credentials
SPOTIFY_CLIENT_ID = '893fee84072b49e7965093e7d51e4498'
SPOTIFY_CLIENT_SECRET = '4071824527c042febfe123e742e0fb8a'
REDIRECT_URI = 'http://localhost:3000/callback'
SCOPE = 'user-read-playback-state user-read-currently-playing user-top-read'

# Discord Rich Presence
DISCORD_CLIENT_ID = '1378317622713647114'
discord_rpc = Presence(1378317622713647114)
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
            'name': data['item']['name'],
            'artists': [artist['name'] for artist in data['item']['artists']],
            'album': {
                'name': data['item']['album']['name'],
                'images': data['item']['album']['images']
            }
        }
        return track_info
    except (KeyError, requests.exceptions.JSONDecodeError) as e:
        print(f"Error processing track data: {e}")
        return None

def get_user_top_items(token, item_type='artists', limit=10):
    headers = {
        'Authorization': f'Bearer {token}'
    }
    response = requests.get(f'https://api.spotify.com/v1/me/top/{item_type}?limit={limit}', headers=headers)
    
    if response.status_code != 200:
        print(f"Error getting top {item_type}: {response.status_code}")
        return []
        
    data = response.json()
    if item_type == 'artists':
        return [artist['name'] for artist in data['items']]
    elif item_type == 'tracks':
        return [track['id'] for track in data['items']]

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
        
        # Initialize profile manager
        self.profile_manager = UserProfileManager()
        
        # Create main notebook for tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=5)
        
        # Create tabs
        self.now_playing_tab = ttk.Frame(self.notebook)
        self.profile_tab = ttk.Frame(self.notebook)
        self.matches_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.now_playing_tab, text='Now Playing')
        self.notebook.add(self.profile_tab, text='My Profile')
        self.notebook.add(self.matches_tab, text='Matches')
        
        self.setup_now_playing_tab()
        self.setup_profile_tab()
        self.setup_matches_tab()
        
        self.current_token = None
        self.current_user_id = None

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
        
        # Top Artists
        self.artists_frame = ttk.LabelFrame(self.profile_frame, text="Top Artists")
        self.artists_frame.pack(fill='x', padx=5, pady=5)
        self.artists_list = tk.Listbox(self.artists_frame, height=5)
        self.artists_list.pack(fill='x', padx=5, pady=5)
        
        # Top Genres
        self.genres_frame = ttk.LabelFrame(self.profile_frame, text="Top Genres")
        self.genres_frame.pack(fill='x', padx=5, pady=5)
        self.genres_list = tk.Listbox(self.genres_frame, height=5)
        self.genres_list.pack(fill='x', padx=5, pady=5)
        
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
                username="User",  # TODO: Get actual username
                music_preferences=[],
                top_artists=[],
                top_genres=[]
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
        
        # Update top artists and genres
        profile.top_artists = get_user_top_items(self.current_token, 'artists')
        profile.top_genres = get_user_top_items(self.current_token, 'tracks')  # TODO: Get actual genres
        
        # Save profile
        self.profile_manager.save_profile(profile)
        self.update_profile_display(profile)

    def update_profile_display(self, profile):
        # Update artists list
        self.artists_list.delete(0, tk.END)
        for artist in profile.top_artists:
            self.artists_list.insert(tk.END, artist)
        
        # Update genres list
        self.genres_list.delete(0, tk.END)
        for genre in profile.top_genres:
            self.genres_list.insert(tk.END, genre)
        
        # Update ratings list
        self.ratings_list.delete(0, tk.END)
        for pref in profile.music_preferences:
            self.ratings_list.insert(tk.END, f"{pref.name} by {', '.join(pref.artists)} - Rating: {pref.rating:.1f}")

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
                response = requests.get(track_info['album']['images'][0]['url'])
                img_data = response.content
                img = Image.open(io.BytesIO(img_data))
                img = img.resize((300, 300), Image.ANTIALIAS)
                photo = ImageTk.PhotoImage(img)
                self.canvas.create_image(0, 0, anchor=tk.NW, image=photo)
                self.canvas.image = photo  # Keep a reference
            except Exception as e:
                print(f"Error loading album art: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = SpotifyApp(root)
    
    # Get Spotify token and user info
    token = get_spotify_token()
    app.current_token = token
    
    # Get user profile
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get('https://api.spotify.com/v1/me', headers=headers)
    if response.status_code == 200:
        user_data = response.json()
        app.current_user_id = user_data['id']
        
        # Load existing profile if available
        profile = app.profile_manager.load_profile(app.current_user_id)
        if profile:
            app.update_profile_display(profile)
    
    # Start tracking current playing
    track_info = get_current_playing(token)
    if track_info:
        update_discord_presence(track_info)
        app.update_ui(track_info)
    
    root.mainloop() 