import json


class Property:
    """Represents a Monopoly property that loads its data from a JSON structure."""

    def __init__(self, json_data):
        """
        Initializes the property by loading data from the provided JSON string or dictionary.
        """
        # Load JSON data if a string is provided
        if isinstance(json_data, str):
            data = json.loads(json_data)
        elif isinstance(json_data, dict):
            data = json_data
        else:
            raise TypeError("Input must be a JSON string or a dictionary.")

        # --- Property Identification ---
        self.name = data['name']
        self.color_group = data['color_group']

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


# --- Minimal House and Hotel Classes (now referencing the Property's cost) ---

class House:
    """Represents a House built on a Property."""

    def __init__(self, property_obj):
        # Validation and building logic goes here
        if property_obj.houses >= 4:
            raise ValueError(f"{property_obj.name} already has 4 houses.")

        print(f"Cost to build: ${property_obj.house_cost}")
        property_obj.houses += 1


class Hotel:
    """Represents a Hotel built on a Property."""

    def __init__(self, property_obj):
        # Validation and building logic goes here
        if property_obj.houses != 4:
            raise ValueError(f"Must have 4 houses on {property_obj.name} to build a Hotel.")


        # Total effective cost is hotel_cost + the 4 houses originally paid for
        print(f"Cost to build Hotel: ${property_obj.hotel_cost}")

        property_obj.houses = 0
        property_obj.has_hotel = True