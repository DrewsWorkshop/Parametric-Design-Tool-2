def vaseSliderConfig():
    """Get the slider configuration specific to pipeGeometry."""
    return [
        ("Segment Count", (2, 9), 5),
        ("Object Width", (2, 3), 2.5),
        ("Twist Angle", (0, 45), 20),
        ("Twist Groove Depth", (0, 8), 1),
        ("Vertical Wave Frequency", (0, 15), 3),
        ("Vertical Wave Depth", (0, 5), 1),
    ]

def vaseDefaults():
    """Default parameter values for Pipe object (matches previous main.py)."""
    return {
        "Segment Count": 9,
        "Object Width": 2.5,
        "Twist Angle": 20,
        "Twist Groove Depth": 1.0,
        "Vertical Wave Frequency": 3.0,
        "Vertical Wave Depth": 1.0,
    }

def vaseCameraConfig():
    """Get specialized camera configuration for vase objects."""
    import math
    return {
        "distance": 30.0,           # zoom distance - standard view
        "yaw": math.radians(0),   # left/right - original default
        "pitch": math.radians(20)   # up/down - original default
    }

def vaseSpacingConfig():
    """Get specialized spacing configuration for vase objects."""
    return {
        "spacing": 1.0,
    }