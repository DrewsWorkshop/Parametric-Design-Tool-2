"""
Utilities for the favorites tab functionality.
Contains helper functions for managing favorites display and layout.
"""


def format_favorite_header(favorite: dict) -> str:
    """Return a compact header like "Vase - (Rating 4/5)".

    Args:
        favorite: A dict entry from favorites list with keys 'object_type' and 'rating'.

    Returns:
        A single-line string suitable for a header label.
    """
    object_type = favorite.get("object_type", "Unknown") or "Unknown"
    rating = favorite.get("Rating")
    if isinstance(rating, (int, float)):
        rating = int(rating)
    else:
        rating = None

    if rating is None or rating < 0 or rating > 5:
        return f"{object_type}"

    return f"{object_type} - (Rating {rating}/5)"


def calculate_object_spacing(favorites_list, base_spacing=8.0):
    """
    Calculate spacing between favorite objects.
    
    Args:
        favorites_list: List of favorite objects
        base_spacing: Base spacing value between objects
        
    Returns:
        float: Calculated spacing value
    """
    return base_spacing


def get_favorite_object_positions(favorites_list, spacing=8.0):
    """
    Calculate positions for all favorite objects in a horizontal line.
    
    Args:
        favorites_list: List of favorite objects
        spacing: Space between objects
        
    Returns:
        list: List of (x, y, z) positions for each object
    """
    if not favorites_list:
        return []
    
    total_favorites = len(favorites_list)
    start_x = -(total_favorites - 1) * spacing / 2
    
    positions = []
    for i in range(total_favorites):
        x = start_x + i * spacing
        positions.append((x, 0, 0))  # y=0, z=0 for horizontal line
    
    return positions


def get_camera_target_position(favorite_index, favorites_list, spacing=8.0):
    """
    Calculate camera target position for a specific favorite object.
    
    Args:
        favorite_index: Index of the favorite to focus on
        favorites_list: List of favorite objects
        spacing: Space between objects
        
    Returns:
        tuple: (x, y, z) position for camera target
    """
    if not favorites_list or favorite_index >= len(favorites_list):
        return (0, 0, 0)
    
    total_favorites = len(favorites_list)
    start_x = -(total_favorites - 1) * spacing / 2
    target_x = start_x + favorite_index * spacing
    
    return (target_x, 0, 0)


def create_remove_button(command=None):
    """Create a 'Remove' button for the favorites tab.

    The button is styled but not wired to any behavior by default.
    Callers can pass a command callback or attach one later via
    `button['command'] = your_handler`.

    Returns:
        DirectButton: The created button instance (initially visible).
    """
    from direct.gui.DirectButton import DirectButton

    return DirectButton(
        text="Remove",
        pos=(0, 0, -0.85),
        scale=0.06,
        frameColor=(0.8, 0.2, 0.2, 1),
        text_fg=(1, 1, 1, 1),
        relief="flat",
        command=command if command else (lambda: None)
    )


def create_edit_button(command=None):
    """Create an 'Edit' button for the favorites tab (no functionality yet)."""
    from direct.gui.DirectButton import DirectButton

    return DirectButton(
        text="Edit",
        pos=(0, 0, -0.75),
        scale=0.06,
        frameColor=(0.3, 0.6, 0.9, 1),
        text_fg=(1, 1, 1, 1),
        relief="flat",
        frameSize=(-2.5, 2.5, -0.5, 0.5),  # Left, Right, Bottom, Top
        command=command if command else (lambda: None)
    )


def create_similar_designs_button(command=None):
    """Create a 'See similar designs...' button for the favorites tab."""
    from direct.gui.DirectButton import DirectButton

    return DirectButton(
        text="See similar designs...",
        pos=(1.3, 0, -0.85),
        scale=0.05,
        frameColor=(0.2, 0.8, 0.2, 1),  # Green frame
        text_fg=(1, 1, 1, 1),
        relief="flat",
        command=command if command else (lambda: None)
    )


def create_back_to_favorites_button(command=None):
    """Create a 'Back to your favorites' button."""
    from direct.gui.DirectButton import DirectButton

    return DirectButton(
        text="Back to your favorites",
        pos=(1.3, 0, -0.85),
        scale=0.05,
        frameColor=(0.6, 0.3, 0.8, 1),  # Purple frame
        text_fg=(1, 1, 1, 1),
        relief="flat",
        command=command if command else (lambda: None)
    )


def create_save_generated_design_button(command=None):
    """Create a 'Save to Favorites' button for generated designs."""
    from direct.gui.DirectButton import DirectButton

    return DirectButton(
        text="Save to Favorites",
        pos=(0, 0, -0.75),  # Same position as original button
        scale=0.05,
        frameColor=(0.2, 0.8, 0.2, 1),  # Green frame
        text_fg=(1, 1, 1, 1),  # White text
        relief=2,  # Raised relief
        command=command if command else (lambda: None)
    )