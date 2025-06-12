from abc import ABC, abstractmethod
import numpy as np
from typing import List, Dict, Any, Tuple

class BaseCollaborativeFilter(ABC):
    """Base class for collaborative filtering implementations."""
    
    def __init__(self, n_factors: int = 100, learning_rate: float = 0.01):
        self.n_factors = n_factors
        self.learning_rate = learning_rate
        self.user_factors = None
        self.item_factors = None
        
    @abstractmethod
    def fit(self, user_item_matrix: np.ndarray) -> None:
        """Train the model on user-item interaction data."""
        pass
    
    @abstractmethod
    def predict(self, user_id: int, item_id: int) -> float:
        """Predict the rating for a user-item pair."""
        pass
    
    @abstractmethod
    def get_recommendations(self, user_id: int, n_recommendations: int = 10) -> List[Tuple[int, float]]:
        """Get top N recommendations for a user."""
        pass
    
    def _calculate_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
    
    def _normalize_features(self, features: np.ndarray) -> np.ndarray:
        """Normalize feature vectors to unit length."""
        return features / np.linalg.norm(features, axis=1, keepdims=True) 