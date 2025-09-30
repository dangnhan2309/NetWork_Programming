#!/usr/bin/env python3
"""
Script để chạy Monopoly Server
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from server.main import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())
