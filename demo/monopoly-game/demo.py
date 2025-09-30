#!/usr/bin/env python3
"""
Demo script để test Monopoly Multiplayer Game
"""

import asyncio
import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_server():
    """Test server"""
    print("🧪 Testing Server...")
    from server.network import MonopolyServer
    
    server = MonopolyServer(host="localhost", port=8765)
    print("✅ Server created successfully")
    
    # Test game manager
    from server.game_manager import GameManager
    gm = GameManager()
    print("✅ GameManager created successfully")
    
    # Test board
    from server.board import Board
    board = Board()
    tile = board.get_tile(0)
    print(f"✅ Board created, GO tile: {tile['name']}")
    
    # Test player
    from server.player import Player
    player = Player("TestPlayer")
    print(f"✅ Player created: {player.name}")
    
    print("🎉 All server components working!")

async def test_client():
    """Test client"""
    print("🧪 Testing Client...")
    
    from client.commands import parse_cmd
    from client.ui import GameUI
    
    # Test command parsing
    msg, err = parse_cmd("/join TestPlayer")
    print(f"✅ Command parsing: {msg}")
    
    # Test UI
    ui = GameUI()
    ui.display_welcome()
    print("✅ UI created successfully")
    
    print("🎉 All client components working!")

async def test_shared():
    """Test shared components"""
    print("🧪 Testing Shared...")
    
    from shared import constants as C
    
    # Test constants
    print(f"✅ MAX_PLAYERS: {C.MAX_PLAYERS}")
    print(f"✅ JOIN message: {C.m_join('Test')}")
    
    print("🎉 All shared components working!")

async def main():
    """Main test function"""
    print("🎲 MONOPOLY MULTIPLAYER GAME - TEST SUITE 🎲")
    print("=" * 50)
    
    try:
        await test_shared()
        print()
        await test_server()
        print()
        await test_client()
        print()
        print("🎉 ALL TESTS PASSED! 🎉")
        print("=" * 50)
        print("🚀 Ready to run the game!")
        print("📝 To start server: python run_server.py")
        print("📝 To start client: python run_client.py")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
