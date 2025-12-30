import math


def vaseExploreCameraRound1Config():
    """Return camera config for Explore view (grid of 8 designs).

    Matches OrbitCamera.apply_config signature: keys distance, yaw, pitch (radians).
    """
    return {
        "distance": 27.0,              # pull back to see multiple items
        "yaw": math.radians(0.0),    # mimic favorites yaw
        "pitch": math.radians(20.0),   # mimic favorites pitch
    }


def vaseTournamentLayout():
    """Positions and scale for two side-by-side vases in tournament view."""
    return {
        "left": (-5.0, 0, 1),
        "right": (5.0, 0.0, 1),
        "scale": 1.0,
        "spin_speed": 0.5,  # degrees per frame
    }

