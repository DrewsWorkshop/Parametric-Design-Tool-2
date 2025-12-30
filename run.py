#!/usr/bin/env python3


import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from main import MainApp

if __name__ == "__main__":
    app = MainApp()
    app.run()
