"""
Constants cho Monopoly Game
"""
MULTICAST_GROUP = "224.1.1.1" 
MULTICAST_PORT = 9999           
BUFFER_SIZE = 8192             

ENCODING = "utf-8"            

# Game constants
MIN_PLAYERS = 2
MAX_PLAYERS = 4
STARTING_MONEY = 1500

# Message types
TYPE_INFO = "info"
TYPE_ERROR = "error"
TYPE_WARNING = "warning"
TYPE_GAME = "game"
# Game states
STATE_EMPTY = "empty"
STATE_WAITING = "waiting"
STATE_PLAYING = "playing"
STATE_ENDED = "ended"

# Events
EVENT_PLAYER_JOINED = "playerJoined"
EVENT_PLAYER_LEFT = "playerLeft"
EVENT_GAME_STARTED = "gameStarted"
EVENT_GAME_OVER = "gameOver"
EVENT_UPDATE_BOARD = "updateBoard"
EVENT_DICE_ROLLED = "diceRolled"
# Actions
ACTION_CREATE_ROOM = "create_room"
ACTION_JOIN_RANDOM = "joinRandom"
ACTION_JOIN_ROOM = "joinRoom"
ACTION_ROLL_DICE = "rollDice"
ACTION_BUY = "buyProperty"
ACTION_END_TURN = "endTurn"
ACTION_CHAT = "chat"

# Tile types
TILE_PROPERTY = "property"
TILE_RAILROAD = "railroad"
TILE_UTILITY = "utility"
TILE_TAX = "tax"
TILE_CHANCE = "chance"
TILE_CHEST = "chest"
TILE_GO = "go"
TILE_JAIL = "jail"
TILE_PARKING = "parking"
TILE_GO_TO_JAIL = "go_to_jail"


# Message creation helpers
def m_join(name: str):
    return {"action": ACTION_JOIN_RANDOM, "playerName": name}

def m_chat(text: str):
    return {"action": ACTION_CHAT, "message": text}

def m_roll():
    return {"action": ACTION_ROLL_DICE}

def m_buy():
    return {"action": ACTION_BUY}

def m_pay(to: str, amount: int):
    return {"action": "pay", "to": to, "amount": amount}

def m_end_turn():
    return {"action": ACTION_END_TURN}

def m_exit():
    return {"action": ACTION_EXIT}