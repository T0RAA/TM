from dataclasses import dataclass
from typing import List, Dict
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
            'top_genres': self.top_genres
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
            top_genres=data['top_genres']
        )

class UserProfileManager:
    def __init__(self, storage_dir: str = 'data/profiles'):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
    
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