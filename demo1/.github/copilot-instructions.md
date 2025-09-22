# Copilot Instructions for This Codebase

## Overview
This repository contains two main network programming demos:

- **Demo 1**: Simple multi-client chat system using raw sockets and threads.
  - `client.py`: Connects to a server, sends/receives plain text messages.
  - `server.py`: Accepts multiple clients, relays messages to all except sender.
- **Demo 2**: Basic turn-based Monopoly-like game server and client.
  - `Demo 2/server.py`: Manages game state, player turns, and communication using JSON over sockets.
  - `Demo 2/client.py`: Connects to the game server, sends commands (e.g., `roll`), receives game updates.

## Architecture & Data Flow
- All communication is over TCP sockets.
- **Demo 1** uses plain text messages; **Demo 2** uses JSON-encoded messages (newline-delimited).
- Servers are multi-threaded: each client connection is handled in a separate thread.
- In Demo 2, the server maintains game state and broadcasts updates to all clients.

## Developer Workflows
- **Run Demo 1:**
  1. Start `server.py` (`python server.py`)
  2. Start one or more `client.py` instances (`python client.py`)
- **Run Demo 2:**
  1. Start `Demo 2/server.py` (`python Demo 2/server.py`)
  2. Start one or more `Demo 2/client.py` instances (`python Demo 2/client.py`)
- No build step or external dependencies required (uses only Python standard library).

## Project Conventions
- Vietnamese is used for some log messages and variable names.
- All network code uses blocking sockets and threads (no async/await).
- Demo 2 uses JSON for structured communication; each message is a single line.
- Game logic in Demo 2 is minimal and can be extended (see `play_turn` in `Demo 2/server.py`).

## Integration Points
- No external services or databases are used.
- All state is in-memory and lost on server restart.

## Patterns & Examples
- **Broadcast pattern:** See `broadcast` in both servers for relaying messages to all clients.
- **Thread-per-client:** Each client connection spawns a new thread for handling communication.
- **JSON messaging:** In Demo 2, always send/receive JSON objects as single lines.

## Extending
- To add new commands or game logic, extend the message handling in `Demo 2/server.py` and update the client accordingly.
- For new message types, update both client and server to handle new JSON keys/actions.

---

For questions about conventions or architecture, see the code comments in each file for further guidance.
