# Parametric Design Tool

A 3D parametric design tool built with Panda3D that allows users to create and manipulate 3D objects with real-time parameter controls.

## Features

- **Real-time 3D visualization** with interactive camera controls
- **Parametric object generation** for Vace and Table objects
- **Interactive UI controls** with sliders for real-time parameter adjustment
- **Favorites system** to save and recall object configurations
- **Multiple object types** with different geometric properties

## Project Structure

```
project_root/
├── src/                          # Source code
│   ├── core/                     # Core application logic
│   │   ├── app.py               # MainApp class
│   ├── geometry/                 # Geometry modules
│   │   ├── vace/                # Vace object geometry
│   │   │   ├── geometry.py      # Vace geometry generation
│   │   │   └── config.py        # Vace parameter configuration
│   │   └── table/               # Table object geometry
│   │       ├── geometry.py      # Table geometry generation
│   │       └── config.py        # Table parameter configuration
│   ├── ui/                      # User interface
│   │   └── controls.py          # ParametricControls class
│   ├── camera/                  # Camera system
│   │   └── controller.py        # OrbitCamera class
│   ├── rendering/               # Rendering system
│   │   └── lighting.py          # Lighting setup
│   └── utils/                   # Utilities
│       └── ui_utils.py          # UI utility functions
├── tests/                       # Test files
├── docs/                        # Documentation
├── requirements.txt             # Dependencies
├── run.py                      # Entry point
└── README.md                   # This file
```

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

Run the application using:
```bash
python run.py
```

## Controls

- **Mouse drag**: Rotate camera around the object
- **Mouse wheel**: Zoom in/out
- **UI sliders**: Adjust object parameters in real-time
- **Object type dropdown**: Switch between Vace and Table objects
- **Favorites buttons**: Save and recall object configurations

## Development

The project is organized using a modular structure:

- **Core**: Main application logic and coordination
- **Geometry**: Object-specific geometry generation and configuration
- **UI**: User interface components and controls
- **Camera**: Camera control and navigation
- **Rendering**: Lighting and visual effects
- **Utils**: Helper functions and utilities

Each module is self-contained with clear interfaces, making it easy to add new features or modify existing functionality.
