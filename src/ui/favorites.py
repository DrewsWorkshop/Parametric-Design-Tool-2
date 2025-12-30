"""
Favorites management system for the parametric design tool.
Handles saving, loading, and managing favorite object configurations.
"""

import json
import os
import builtins
from datetime import datetime
from direct.gui.OnscreenText import OnscreenText
from direct.gui.OnscreenImage import OnscreenImage
from direct.gui.DirectButton import DirectButton
from direct.gui import DirectGuiGlobals as DGG
from direct.task import Task


class FavoritesLabel:
    """Manages the favorites button functionality."""
    
    def __init__(self, save_callback, status_text):
        self.save_callback = save_callback
        self.status_text = status_text
        self.create_label()
    
    def create_label(self):
        """Create the Save to Favorites button."""
        self.button = DirectButton(
            text="Save to Favorites",
            pos=(-1.15, 0, -0.25), 
            scale=0.05,
            command=self._on_save_click,
            rolloverSound=None,
            clickSound=None,
            frameColor=(0.2, 0.8, 0.2, 1),  # Green frame
            text_fg=(1, 1, 1, 1),  # White text
            relief=2  # Raised relief
        )
    
    def _on_save_click(self, *args):
        """Called when the Save to Favorites button is clicked."""
        print("Save to Favorites button clicked!")
        # Save favorite with rating 5
        if callable(self.save_callback):
            self.save_callback(5)  # Always save with rating 5
    
    def show(self):
        """Show the button."""
        self.button.show()
    
    def hide(self):
        """Hide the button."""
        self.button.hide()


def save_favorite_to_file(filename: str = "src/tmp/favorites.txt", params: dict = None, object_type: str = None, rating: int = None) -> int:
    """
    Save a favorite configuration to file.
    If parameters match an existing favorite, update the rating instead of creating a duplicate.
    
    Args:
        filename: File to save to
        params: Parameter dictionary
        object_type: Type of object (Vase, Table, Stool)
        rating: Star rating (1-5)
        
    Returns:
        Total number of favorites
    """
    try:
        # Load existing favorites
        existing_favorites = []
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                content = f.read().strip()
                if content:
                    existing_favorites = json.loads(content)
        
        # Check if there's an existing favorite with the same parameters and object type
        existing_index = None
        for i, existing_favorite in enumerate(existing_favorites):
            if (existing_favorite.get("object_type") == object_type and 
                existing_favorite.get("parameters") == params):
                existing_index = i
                break
        
        if existing_index is not None:
            # Update existing favorite's rating and timestamp
            existing_favorites[existing_index]["Rating"] = rating
            existing_favorites[existing_index]["timestamp"] = datetime.now().isoformat()
            print(f"Updated existing favorite rating to {rating} stars")
        else:
            # Create new favorite entry
            favorite = {
                "timestamp": datetime.now().isoformat(),
                "object_type": object_type or "Unknown",
                "Rating": rating,
                "parameters": params
            }
            existing_favorites.append(favorite)
            print(f"Created new favorite with {rating} stars")
        
        # Save back to file
        with open(filename, 'w') as f:
            json.dump(existing_favorites, f, indent=2)
        
        return len(existing_favorites)
        
    except Exception as e:
        print(f"Error saving favorite: {e}")
        return 0


def load_favorites_from_file(filename: str) -> list:
    """Load favorites from file."""
    try:
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                content = f.read().strip()
                if content:
                    return json.loads(content)
        return []
    except Exception as e:
        print(f"Error loading favorites: {e}")
        return []