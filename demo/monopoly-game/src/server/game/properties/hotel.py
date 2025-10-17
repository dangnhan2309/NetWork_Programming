
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