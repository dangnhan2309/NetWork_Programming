# src/client/command_list.py

command_dic = {
    # Connect & Game Setup
    "JOIN": {"action": "JOIN", "data": {"name": "Alice"}},
    "LEAVE": {"action": "LEAVE", "data": {}},
    "READY": {"action": "READY", "data": {}},
    "START_GAME": {"action": "START_GAME", "data": {}},

    # Player Actions
    "ROLL_DICE": {"action": "ROLL_DICE", "data": {}},
    "MOVE": {"action": "MOVE", "data": {"steps": 5}},
    "BUY_PROPERTY": {"action": "BUY_PROPERTY", "data": {"property_id": 12}},
    "PAY_RENT": {"action": "PAY_RENT", "data": {"property_id": 12, "amount": 200}},
    "BUILD_HOUSE": {"action": "BUILD_HOUSE", "data": {"property_id": 12}},
    "END_TURN": {"action": "END_TURN", "data": {}},

    # Trading
    "TRADE_REQUEST": {
        "action": "TRADE_REQUEST",
        "data": {"to_player": "Bob", "offer": {"cash": 300}, "request": {"property_id": 7}}
    },
    "TRADE_RESPONSE": {"action": "TRADE_RESPONSE", "data": {"accepted": True}},

    # Game Updates
    "GAME_STATE": {"action": "GAME_STATE", "data": {}},
    "CHAT": {"action": "CHAT", "data": {"message": "Good luck!"}}
}
message_dic =
    {
        "INIT_GAME": {"action": "JOIN", "data": {"name": "Alice"}},
        "SYNC_STATE ": {"action": "JOIN", "data": {"name": "Alice"}},
        "SPAWN_OBJECT": {"action": "JOIN", "data": {"name": "Alice"}},
        "DESPAWN_OBJECT": {"action": "JOIN", "data": {"name": "Alice"}},
        "PLAYER_MOVE": {"action": "JOIN", "data": {"name": "Alice"}},
        "PLAYER_ACTION": {"action": "JOIN", "data": {"name": "Alice"}},
        "UPDATE_STATS": {"action": "JOIN", "data": {"name": "Alice"}},
        "GAME_OVER": {"action": "JOIN", "data": {"name": "Alice"}},
        "CHAT_MESSAGE": {"action": "JOIN", "data": {"name": "Alice"}},
        "ERROR": {"action": "JOIN", "data": {"name": "Alice"}},
        "ERROR": {"action": "JOIN", "data": {"name": "Alice"}},
        "ERROR": {"action": "JOIN", "data": {"name": "Alice"}},

    }