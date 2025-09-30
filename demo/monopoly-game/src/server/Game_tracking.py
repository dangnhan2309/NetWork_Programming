from .game_variable import GameVariable
import collections
from .player import Player

class Tracker:
   def __init__(self):

       self.game_variable = GameVariable()

       self.tiles = self.game_variable.tiles
       self.player_assets = self.game_variable.assets
       self.players = []
       self.current_turn = 0
       self._double_streak = {}  # name -> consecutive doubles count

       # Dictionary to store the owner of each buyable property
       self.player_position = {}  # {position:   player_name}  use to update position

       # Dictionary to store the number of houses/hotels on each property
       self.property_usage = collections.defaultdict(int)  # {position: num_of_houses}



   def check_properties_available(self, id_land) -> bool:

       name_tiles = self.tiles[id_land]
       name_owner = self.player_assets[name_tiles]["owner"]
       return name_owner

   def player_buy_lands(self,name,id_land) -> bool:
        owner = self.check_properties_available(id_land)
        if owner == "":
            self.player_assets[self.tiles[id_land]]["owner"] = name
            return True
        else :
            print(f"Property [{self.tiles[id_land]}] is owned by other player{owner}")
            return False
   def add_player(self,player:Player) -> bool:
       if self.players.__len__() < self.game_variable.player_num :
           self.players.append(player)
           return True
       else :
           print("[add_player]PLayer reach limits")
           return False
