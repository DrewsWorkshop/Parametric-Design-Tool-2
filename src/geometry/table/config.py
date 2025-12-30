import math


def tableSliderConfig():
    """Get the slider configuration specific to tableGeometry."""
    return [
        ("Segment Count", (2, 9), 5),
        ("Object Width", (1.5, 4.0), 3.0),
        ("Twist Angle", (0, 45), 20),
        ("Twist Groove Depth", (0, 5), 1),
        ("Vertical Wave Frequency", (0, 20), 3),
        ("Vertical Wave Depth", (0, 5), 1),
    ]

def tableDefaults():
    """Default parameter values for Table object."""
    return {
        "Segment Count": 9,
        "Object Width": 3,
        "Twist Angle": 20,
        "Twist Groove Depth": 1.0,
        "Vertical Wave Frequency": 3.0,
        "Vertical Wave Depth": 1.0,
    }

def tableCameraConfig():
    """Get specialized camera configuration for table objects."""
    return {
        "distance": 40.0,           # zoom distance - slightly further to see full table
        "yaw": math.radians(0),   # left/right - better angle to see table structure
        "pitch": math.radians(20)   # up/down - slightly lower to see table top
    }