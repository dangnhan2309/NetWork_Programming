#!/usr/bin/env python3
"""
Script để chạy Monopoly Game trong CLI mode
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.server.cli_game import main

if __name__ == "__main__":
    main()
