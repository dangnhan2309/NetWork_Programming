# game/tiles/base_tile.py
class BaseTile:
    def __init__(self, tile_id, name, position, tile_type):
        self.tile_id = tile_id
        self.name = name
        self.position = position
        self.tile_type = tile_type
    def on_land(self, player, board):
        """Gọi khi người chơi dừng ở ô này."""
        return {
            "event": "none",
            "message": f"{player.name} landed on {self.name}."
        }

    def to_dict(self):
        """Serialize tile info để gửi về client."""
        return {
            "id": self.tile_id,
            "name": self.name,
            "position": self.position,
            "type": self.tile_type
        }
