# """
# Command parser cho Monopoly Client
# """

# def parse_cmd(cmd: str):
#     """
#     Parse command từ người dùng
#     Trả về: (message_dict, error_message)
#     """
#     if not cmd:
#         return None, "❌ Lệnh không được để trống"
    
#     parts = cmd.strip().split()
#     if not parts:
#         return None, "❌ Lệnh không hợp lệ"
    
#     action = parts[0].lower()
    
#     # Lệnh roll dice
#     if action == "/roll":
#         return {"action": "rollDice"}, None
    
#     # Lệnh buy property
#     elif action == "/buy":
#         return {"action": "buyProperty"}, None
    
#     # Lệnh sell property
#     elif action == "/sell" and len(parts) > 1:
#         return {
#             "action": "sellProperty",
#             "property": parts[1]
#         }, None
    
#     # Lệnh build house
#     elif action == "/build" and len(parts) > 1:
#         return {
#             "action": "buildHouse",
#             "property": parts[1]
#         }, None
    
#     # Lệnh trade
#     elif action == "/trade" and len(parts) > 3:
#         return {
#             "action": "trade",
#             "targetPlayer": parts[1],
#             "give": parts[2],
#             "receive": parts[3]
#         }, None
    
#     # Lệnh chat
#     elif action == "/chat" and len(parts) > 1:
#         message = " ".join(parts[1:])
#         return {
#             "action": "chat",
#             "message": message
#         }, None
    
#     # Lệnh state
#     elif action == "/state":
#         return {"action": "requestState"}, None
    
#     # Lệnh end turn
#     elif action == "/end":
#         return {"action": "endTurn"}, None
    
#     # Lệnh help
#     elif action == "/help":
#         return None, None  # Xử lý ở client
    
#     else:
#         return None, f"❌ Lệnh không hợp lệ: {cmd}\n📍 Gõ /help để xem danh sách lệnh"