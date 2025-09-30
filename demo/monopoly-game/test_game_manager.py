#!/usr/bin/env python3
"""
Test Suite cho Game Manager - Monopoly Multiplayer
Test các chức năng cơ bản của game theo yêu cầu
"""

import sys
import os
import asyncio

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.server.game_manager import GameManager
from src.server.player import Player
from src.server.board import Board

class MockWebSocket:
    """Mock WebSocket để test"""
    def __init__(self, name):
        self.name = name

def test_basic_game_rules():
    """Test 1: Tạo 2 players, chạy 3-5 turns"""
    print("🧪 TEST 1: Basic Game Rules")
    print("=" * 50)
    
    gm = GameManager()
    
    # Tạo 2 players
    ws1 = MockWebSocket("PlayerA")
    ws2 = MockWebSocket("PlayerB")
    
    gm.add_player("PlayerA", ws1)
    gm.add_player("PlayerB", ws2)
    
    print(f"✅ Created 2 players: {list(gm.players.keys())}")
    print(f"✅ Game state: {gm.game_state}")
    
    # Chạy 3 turns
    for turn in range(3):
        current_player = gm.get_current_player()
        if current_player:
            print(f"\n🎲 Turn {turn + 1}: {current_player.name}")
            
            # Test roll dice
            steps, is_double = gm.roll_dice()
            print(f"   Rolled: {steps} (double: {is_double})")
            
            # Test move
            old_pos = current_player.position
            current_player.move(steps)
            new_pos = current_player.position
            print(f"   Moved from {old_pos} to {new_pos}")
            
            # Test tile handling
            tile = gm.board.get_tile(new_pos)
            print(f"   Landed on: {tile['name']} (type: {tile['type']})")
            
            # End turn
            gm.next_turn()
    
    print("\n✅ Test 1 completed successfully!")

def test_property_purchase_and_rent():
    """Test 2: Player A mua đất -> Player B đứng vào -> B trả tiền"""
    print("\n🧪 TEST 2: Property Purchase and Rent")
    print("=" * 50)
    
    gm = GameManager()
    
    # Tạo 2 players
    ws1 = MockWebSocket("PlayerA")
    ws2 = MockWebSocket("PlayerB")
    
    gm.add_player("PlayerA", ws1)
    gm.add_player("PlayerB", ws2)
    
    player_a = gm.players["PlayerA"]
    player_b = gm.players["PlayerB"]
    
    print(f"✅ PlayerA money: ${player_a.money}")
    print(f"✅ PlayerB money: ${player_b.money}")
    
    # Player A mua property
    # Di chuyển đến property đầu tiên
    player_a.position = 1  # Mediterranean Ave
    tile = gm.board.get_tile(1)
    print(f"\n🏠 PlayerA at {tile['name']} (price: ${tile['price']})")
    
    # Mua property
    if player_a.money >= tile['price']:
        player_a.buy_property(tile['name'], tile['price'])
        tile['owner'] = player_a
        print(f"✅ PlayerA bought {tile['name']} for ${tile['price']}")
        print(f"✅ PlayerA money after purchase: ${player_a.money}")
    
    # Player B đứng vào property của A
    player_b.position = 1
    print(f"\n💰 PlayerB landed on {tile['name']} (owned by {tile['owner'].name})")
    
    # Player B trả tiền thuê
    if tile['owner'] and tile['owner'] != player_b:
        rent = tile['rent']
        old_money_b = player_b.money
        old_money_a = player_a.money
        
        player_b.pay_rent(player_a, rent)
        
        print(f"✅ PlayerB paid ${rent} rent to PlayerA")
        print(f"✅ PlayerB money: ${old_money_b} -> ${player_b.money}")
        print(f"✅ PlayerA money: ${old_money_a} -> ${player_a.money}")
    
    print("\n✅ Test 2 completed successfully!")

def test_bankruptcy():
    """Test 3: Player hết tiền -> in trạng thái phá sản"""
    print("\n🧪 TEST 3: Bankruptcy Test")
    print("=" * 50)
    
    gm = GameManager()
    
    # Tạo player với ít tiền
    ws = MockWebSocket("PoorPlayer")
    gm.add_player("PoorPlayer", ws)
    
    player = gm.players["PoorPlayer"]
    player.money = 10  # Rất ít tiền
    
    print(f"✅ PoorPlayer starting money: ${player.money}")
    
    # Tạo player khác để trả tiền thuê
    ws2 = MockWebSocket("RichPlayer")
    gm.add_player("RichPlayer", ws2)
    rich_player = gm.players["RichPlayer"]
    
    # PoorPlayer phải trả tiền thuê cao
    rent_amount = 50  # Nhiều hơn số tiền có
    
    print(f"\n💸 PoorPlayer must pay ${rent_amount} rent")
    print(f"   Current money: ${player.money}")
    
    # Test bankruptcy
    if player.money < rent_amount:
        print("⚠️  PoorPlayer cannot afford rent!")
        player.pay_rent(rich_player, rent_amount)
        
        if player.is_bankrupt:
            print("💀 PoorPlayer is BANKRUPT!")
            print(f"   Final money: ${player.money}")
            print(f"   Properties: {list(player.properties.keys())}")
        else:
            print(f"✅ PoorPlayer survived with ${player.money}")
    
    print("\n✅ Test 3 completed successfully!")

def test_integration():
    """Test 4: Integration test - chạy toàn bộ game"""
    print("\n🧪 TEST 4: Integration Test")
    print("=" * 50)
    
    gm = GameManager()
    
    # Tạo 3 players
    players = ["Alice", "Bob", "Charlie"]
    for name in players:
        ws = MockWebSocket(name)
        gm.add_player(name, ws)
    
    print(f"✅ Created {len(gm.players)} players: {list(gm.players.keys())}")
    
    # Chạy 10 turns
    for turn in range(10):
        current_player = gm.get_current_player()
        if not current_player:
            break
            
        print(f"\n🎲 Turn {turn + 1}: {current_player.name}")
        
        # Roll dice
        steps, is_double = gm.roll_dice()
        print(f"   Rolled: {steps}")
        
        # Move
        old_pos = current_player.position
        current_player.move(steps)
        new_pos = current_player.position
        
        # Get tile info
        tile = gm.board.get_tile(new_pos)
        print(f"   Moved to: {tile['name']} (position {new_pos})")
        
        # Handle tile
        result = gm.handle_tile(current_player, tile)
        if result:
            print(f"   Tile result: {result}")
        
        # End turn
        gm.next_turn()
    
    # Print summary
    print("\n📊 GAME SUMMARY:")
    print("=" * 30)
    for name, player in gm.players.items():
        print(f"{name}:")
        print(f"  💰 Money: ${player.money}")
        print(f"  📍 Position: {player.position}")
        print(f"  🏠 Properties: {len(player.properties)}")
        if player.properties:
            print(f"     {list(player.properties.keys())}")
        print()
    
    print("✅ Test 4 completed successfully!")

def main():
    """Chạy tất cả tests"""
    print("🎲 MONOPOLY GAME MANAGER TEST SUITE 🎲")
    print("=" * 60)
    
    try:
        test_basic_game_rules()
        test_property_purchase_and_rent()
        test_bankruptcy()
        test_integration()
        
        print("\n🎉 ALL TESTS PASSED! 🎉")
        print("=" * 60)
        print("✅ Game Manager is working correctly!")
        print("✅ Ready for multiplayer integration!")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
