from dataclasses import dataclass
from typing import List, Dict, Optional
import json
import os

@dataclass
class MusicPreference:
    track_id: str
    name: str
    artists: List[str]
    album: str
    rating: float  # 0-1 scale indicating how much the user likes this track

@dataclass
class UserProfile:
    user_id: str
    username: str
    music_preferences: List[MusicPreference]
    top_artists: List[str]
    top_genres: List[str]
    top_songs: List[dict] = None
    top_albums: List[dict] = None
    favorite_artists: List[str] = None
    favorite_songs: List[str] = None
    favorite_genres: List[str] = None
    favorite_albums: List[str] = None
    # Personal information fields
    first_name: str = ""
    last_name: str = ""
    age: Optional[int] = None
    gender: str = ""
    location: str = ""
    bio: str = ""
    profile_picture_path: str = ""
    
    def __post_init__(self):
        # Initialize empty lists for favorites if None
        if self.favorite_artists is None:
            self.favorite_artists = []
        if self.favorite_songs is None:
            self.favorite_songs = []
        if self.favorite_genres is None:
            self.favorite_genres = []
        if self.favorite_albums is None:
            self.favorite_albums = []
        if self.top_songs is None:
            self.top_songs = []
        if self.top_albums is None:
            self.top_albums = []
    
    def to_dict(self) -> Dict:
        return {
            'user_id': self.user_id,
            'username': self.username,
            'music_preferences': [
                {
                    'track_id': p.track_id,
                    'name': p.name,
                    'artists': p.artists,
                    'album': p.album,
                    'rating': p.rating
                } for p in self.music_preferences
            ],
            'top_artists': self.top_artists,
            'top_genres': self.top_genres,
            'top_songs': self.top_songs,
            'top_albums': self.top_albums,
            'favorite_artists': self.favorite_artists,
            'favorite_songs': self.favorite_songs,
            'favorite_genres': self.favorite_genres,
            'favorite_albums': self.favorite_albums,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'age': self.age,
            'gender': self.gender,
            'location': self.location,
            'bio': self.bio,
            'profile_picture_path': self.profile_picture_path
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'UserProfile':
        return cls(
            user_id=data['user_id'],
            username=data['username'],
            music_preferences=[
                MusicPreference(
                    track_id=p['track_id'],
                    name=p['name'],
                    artists=p['artists'],
                    album=p['album'],
                    rating=p['rating']
                ) for p in data['music_preferences']
            ],
            top_artists=data['top_artists'],
            top_genres=data['top_genres'],
            top_songs=data.get('top_songs', []),
            top_albums=data.get('top_albums', []),
            favorite_artists=data.get('favorite_artists', []),
            favorite_songs=data.get('favorite_songs', []),
            favorite_genres=data.get('favorite_genres', []),
            favorite_albums=data.get('favorite_albums', []),
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            age=data.get('age'),
            gender=data.get('gender', ''),
            location=data.get('location', ''),
            bio=data.get('bio', ''),
            profile_picture_path=data.get('profile_picture_path', '')
        )

class UserProfileManager:
    def __init__(self, storage_dir: str = 'data/profiles', pictures_dir: str = 'data/profile_pictures'):
        self.storage_dir = storage_dir
        self.pictures_dir = pictures_dir
        os.makedirs(storage_dir, exist_ok=True)
        os.makedirs(pictures_dir, exist_ok=True)
    
    def save_profile(self, profile: UserProfile):
        file_path = os.path.join(self.storage_dir, f"{profile.user_id}.json")
        with open(file_path, 'w') as f:
            json.dump(profile.to_dict(), f, indent=2)
    
    def load_profile(self, user_id: str) -> UserProfile:
        file_path = os.path.join(self.storage_dir, f"{user_id}.json")
        if not os.path.exists(file_path):
            return None
        with open(file_path, 'r') as f:
            return UserProfile.from_dict(json.load(f))
    
    def save_profile_picture(self, user_id: str, image_path: str) -> str:
        """Save a profile picture and return the saved path"""
        import shutil
        from PIL import Image
        
        # Get file extension
        file_ext = os.path.splitext(image_path)[1].lower()
        if file_ext not in ['.jpg', '.jpeg', '.png', '.gif']:
            raise ValueError("Unsupported image format. Please use JPG, PNG, or GIF.")
        
        # Create new filename
        new_filename = f"{user_id}{file_ext}"
        new_path = os.path.join(self.pictures_dir, new_filename)
        
        # Resize and save image
        with Image.open(image_path) as img:
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize to 300x300 while maintaining aspect ratio
            img.thumbnail((300, 300), Image.LANCZOS)
            
            # Save the resized image
            img.save(new_path, quality=85, optimize=True)
        
        return new_path
    
    def get_profile_picture_path(self, user_id: str) -> Optional[str]:
        """Get the profile picture path for a user"""
        profile = self.load_profile(user_id)
        if profile and profile.profile_picture_path and os.path.exists(profile.profile_picture_path):
            return profile.profile_picture_path
        return None
    
    def calculate_compatibility(self, profile1: UserProfile, profile2: UserProfile) -> float:
        """
        Calculate compatibility score between two users based on their music preferences.
        Returns a score between 0 and 1.
        """
        # Calculate artist overlap
        artist_scores = []
        for artist1 in profile1.top_artists:
            for artist2 in profile2.top_artists:
                if artist1.lower() == artist2.lower():
                    artist_scores.append(1.0)
        
        # Calculate genre overlap
        genre_scores = []
        for genre1 in profile1.top_genres:
            for genre2 in profile2.top_genres:
                if genre1.lower() == genre2.lower():
                    genre_scores.append(1.0)
        
        # Calculate track preference similarity
        track_scores = []
        for pref1 in profile1.music_preferences:
            for pref2 in profile2.music_preferences:
                if pref1.track_id == pref2.track_id:
                    # Calculate how similar their ratings are
                    rating_diff = abs(pref1.rating - pref2.rating)
                    track_scores.append(1.0 - rating_diff)
        
        # Weight the different factors
        artist_weight = 0.4
        genre_weight = 0.3
        track_weight = 0.3
        
        artist_score = sum(artist_scores) / max(len(profile1.top_artists), len(profile2.top_artists)) if artist_scores else 0
        genre_score = sum(genre_scores) / max(len(profile1.top_genres), len(profile2.top_genres)) if genre_scores else 0
        track_score = sum(track_scores) / max(len(profile1.music_preferences), len(profile2.music_preferences)) if track_scores else 0
        
        final_score = (
            artist_score * artist_weight +
            genre_score * genre_weight +
            track_score * track_weight
        )
        
        return min(max(final_score, 0), 1)  # Ensure score is between 0 and 1
    
    def find_matches(self, user_id: str, min_compatibility: float = 0.5) -> List[tuple[UserProfile, float]]:
        """
        Find potential matches for a user based on music compatibility.
        Returns a list of tuples containing (profile, compatibility_score).
        """
        user_profile = self.load_profile(user_id)
        if not user_profile:
            return []
        
        matches = []
        for filename in os.listdir(self.storage_dir):
            if filename.endswith('.json') and filename != f"{user_id}.json":
                other_profile = self.load_profile(filename[:-5])  # Remove .json extension
                if other_profile:
                    compatibility = self.calculate_compatibility(user_profile, other_profile)
                    if compatibility >= min_compatibility:
                        matches.append((other_profile, compatibility))
        
        # Sort matches by compatibility score
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches 