# src/client/ui.py
from typing import Dict, List
from ..shared.board import Board


class ClientUI:
    def __init__(self):
        self.board = Board()
        self.state = {}

    # === Core Board Rendering ===
    def update_map(self, new_state: Dict) -> None:
        """
        Re-render the ASCII board using Board class.
        """
        self.state = new_state
        print(self.board.render_ascii(new_state))

    # === Commands Menu ===
    @staticmethod
    def commands_menu_render(available: List[str]) -> str:
        lines = ["Available Commands:"]
        for i, cmd in enumerate(available, 1):
            lines.append(f" [{i}] {cmd}")
        return "\n".join(lines)

    def display_commands(self, available: List[str]) -> None:
        print(self.commands_menu_render(available))

    # === Properties ===
    @staticmethod
    def property_list_render(properties: List[Dict]) -> str:
        if not properties:
            return "No properties owned."
        lines = ["Owned Properties:"]
        for prop in properties:
            name = prop.get("name", "Unknown")
            houses = prop.get("houses", 0)
            hotel = "Hotel" if prop.get("hotel", False) else ""
            lines.append(f"- {name} | Houses: {houses} {hotel}")
        return "\n".join(lines)

    def show_properties(self, properties: List[Dict]) -> None:
        print(self.property_list_render(properties))

    # === Player Status ===
    @staticmethod
    def update_player_status(player_id: str, status: Dict) -> None:
        money = status.get("money", 0)
        pos = status.get("pos", 0)
        print(f"[STATUS] {player_id}: Money={money}, Position={pos}")

    # === Customization ===
    @staticmethod
    def customize_ui(nick: str, symbol: str, color: str = "white") -> None:
        # For later: symbols/colors in rendering
        print(f"[UI] Customized {nick}: symbol={symbol}, color={color}")

    def ui_loop(self,players_state,Commands):
        '''
        demo_state = {
            "players": [
                {"nick": "A", "pos": 0},
                {"nick": "B", "pos": 10},
                {"nick": "C", "pos": 24},
                {"nick": "D", "pos": 39},
            ],
            "ownership": {1: "A", 3: "B", 6: "C", 8: "D", 39: "A"},
            "buildings": {1: {"houses": 2, "hotel": False}, 39: {"houses": 0, "hotel": True}},
        }

        ui.update_map(players_state)
        ui.display_commands(["ROLL", "BUY", "END TURN"])
        ui.show_properties([
            {"name": "Park Lane", "houses": 2, "hotel": False},
            {"name": "Mayfair", "houses": 0, "hotel": True},
        ])
        ui.update_player_status("Alice", {"money": 1400, "pos": 3})
        '''
        self.update_player_status(players_state);
        


# Demo run
if __name__ == "__main__":
    ui = ClientUI()

