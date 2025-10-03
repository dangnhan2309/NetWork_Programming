"""
Constants cho Monopoly Game (Shared between client and server)
"""

# Game States
STATE_EMPTY = "EMPTY"
STATE_WAITING = "WAITING" 
STATE_PLAYING = "PLAYING"
STATE_ENDED = "ENDED"

# Client Actions
ACTION_JOIN = "join"
ACTION_CREATE_ROOM = "createRoom"
ACTION_JOIN_RANDOM = "joinRandom"
ACTION_ROLL_DICE = "rollDice"
ACTION_BUY = "buy"
ACTION_END_TURN = "endTurn"
ACTION_CHAT = "chat"

# Server Events
EVENT_UPDATE_BOARD = "updateBoard"
EVENT_GAME_OVER = "gameOver"
EVENT_PLAYER_JOINED = "playerJoined"
EVENT_PLAYER_LEFT = "playerLeft"
EVENT_ROOM_STATUS = "roomStatus"

# Message Types
TYPE_INFO = "info"
TYPE_ERROR = "error"

# Game Config
MAX_PLAYERS = 4
MIN_PLAYERS = 2
STARTING_MONEY = 1500
BOARD_SIZE = 40