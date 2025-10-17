

class Property:
    """Represents a Monopoly property that loads its data from a JSON structure."""

    def __init__(self,data):
        """
        Initializes the property by loading data from the provided JSON string or dictionary.
        """
        # --- Property Identification ---
        self.name = data['name']
        self.color_group = data['color_group']
        self.purchase_price = data['purchase_price']
        # --- Rent Data ---
        self.base_rent = data['base_rent']
        self.rents = data['rents']

        # --- Building and Financials ---
        self.mortgage_value = data['mortgage_value']
        self.house_cost = data['building_costs']['house_cost']
        self.hotel_cost = data['building_costs']['hotel_cost']

        # --- Current State ---
        self.houses = 0  # Number of houses (0-4)
        self.has_hotel = False
        self.is_mortgaged = False
        self.owner = None  # Placeholder for Player object

    def calculate_rent(self, is_monopoly=False):
        """Calculates the rent based on the current number of houses/hotel and monopoly status."""

        if self.is_mortgaged:
            return 0

        if self.has_hotel:
            return self.rents['hotel']
        if self.houses > 0 and self.houses ==1:
            # Map house count to the correct rent key
            rent_key = f"{self.houses}_house"
            return self.rents[rent_key]
        if self.houses > 1:
            # Map house count to the correct rent key
            rent_key = f"{self.houses}_houses"
            return self.rents[rent_key]

        # Unimproved Lot
        base_rent = self.base_rent
        if is_monopoly:
            # Monopoly rule: Rent is doubled on unimproved lots
            return base_rent * 2
        else:
            return base_rent

    def __str__(self):
        return f"{self.name} ({self.color_group}) | Houses: {self.houses} | Hotel: {self.has_hotel}"

