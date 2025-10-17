
import json
from pathlib import Path

from .test_house_obj import Property,House,Hotel


MED_AVE_JSON = r"demo/monopoly-game/src/server/game/properties/properties_data.json"
json_path = Path(MED_AVE_JSON)
if not json_path.exists():
    raise FileNotFoundError(f"Không tìm thấy tệp cấu hình bàn cờ tại: {json_path}")
with open(json_path,'r',encoding='utf-8') as f :
    data= json.load(f)
print(data)






# 1. Load the property
med_ave = Property(data)
print(f"Property Loaded: {med_ave}")

# 2. Check rents
print(f"Rent Unimproved (No Monopoly): ${med_ave.calculate_rent()}") # Expected: $2
print(f"Rent Unimproved (Monopoly): ${med_ave.calculate_rent(is_monopoly=True)}") # Expected: $4

# 3. Build a house
House(med_ave)
print(f"Rent with 1 House: ${med_ave.calculate_rent()}") # Expected: $10

# 4. Build 3 more houses (to get to 4)
for _ in range(3):
    House(med_ave)

# 5. Build a hotel
Hotel(med_ave)
print(f"Rent with Hotel: ${med_ave.calculate_rent()}") # Expected: $250
print(f"Current State: {med_ave}")