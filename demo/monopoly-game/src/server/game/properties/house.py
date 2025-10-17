class House:
    """Represents a House built on a Property."""

    def __init__(self, property_obj):
        # Validation and building logic goes here
        if property_obj.houses >= 4:
            raise ValueError(f"{property_obj.name} already has 4 houses.")

        print(f"Cost to build: ${property_obj.house_cost}")
        property_obj.houses += 1
