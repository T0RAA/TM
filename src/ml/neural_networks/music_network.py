import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple, List

class MusicFeatureExtractor(nn.Module):
    """Neural network for extracting music features."""
    
    def __init__(self, input_dim: int, hidden_dims: List[int], output_dim: int):
        super().__init__()
        self.layers = nn.ModuleList()
        
        # Input layer
        prev_dim = input_dim
        for hidden_dim in hidden_dims:
            self.layers.append(nn.Linear(prev_dim, hidden_dim))
            prev_dim = hidden_dim
        
        # Output layer
        self.output_layer = nn.Linear(prev_dim, output_dim)
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass through the network."""
        for layer in self.layers:
            x = F.relu(layer(x))
        return self.output_layer(x)

class UserMusicMatcher(nn.Module):
    """Neural network for matching users with music preferences."""
    
    def __init__(self, user_dim: int, music_dim: int, hidden_dim: int):
        super().__init__()
        self.user_encoder = nn.Linear(user_dim, hidden_dim)
        self.music_encoder = nn.Linear(music_dim, hidden_dim)
        self.matcher = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),
            nn.Sigmoid()
        )
    
    def forward(self, user_features: torch.Tensor, music_features: torch.Tensor) -> torch.Tensor:
        """Forward pass computing compatibility score."""
        user_encoded = F.relu(self.user_encoder(user_features))
        music_encoded = F.relu(self.music_encoder(music_features))
        
        combined = torch.cat([user_encoded, music_encoded], dim=1)
        return self.matcher(combined)
    
    def get_embeddings(self, user_features: torch.Tensor, music_features: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """Get user and music embeddings."""
        user_encoded = F.relu(self.user_encoder(user_features))
        music_encoded = F.relu(self.music_encoder(music_features))
        return user_encoded, music_encoded 