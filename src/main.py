#!/usr/bin/env python3
"""
Main entry point for the Parametric Design Tool.
This file simply imports and runs the main application.
"""

from core.app import MainApp

if __name__ == "__main__":
    app = MainApp()
    app.run()
