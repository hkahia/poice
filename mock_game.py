import asyncio
import json
import random
import websockets

clients = set()
players = {}


def snapshot(phase, multiplier=1.0, countdown=5):
    return {
        "type": "state_snapshot",
        "state": {
            "phase": phase,
            "countdown": countdown,
            "multiplier": multiplier,
            "crashPoint": 2.8,
            "activePlayers": list(players.values()),
            "playersTotal": len(players),
            "botsCount": 0,
            "viewersCount": len(clients),
            "crashHistory": []
        }
    }


async def broadcast(message):
    if clients:
        await asyncio.gather(*(client.send(json.dumps(message)) for client in clients), return_exceptions=True)


async def game_loop():
    while True:
        for countdown in range(5, 0, -1):
            await broadcast(snapshot("countdown", 1.0, countdown))
            await asyncio.sleep(1)
        await broadcast({"type": "phase_change", "phase": "flying", "multiplier": 1.0, "activePlayers": list(players.values()), "playersTotal": len(players)})
        for step in range(1, 30):
            multiplier = round(1 + step * 0.06, 2)
            await broadcast({"type": "multiplier_update", "multiplier": multiplier})
            await asyncio.sleep(0.35)
        await broadcast({"type": "crash", "crashPoint": 2.8, "activePlayers": list(players.values()), "playersTotal": len(players)})
        players.clear()
        await asyncio.sleep(2)


async def handle(websocket):
    clients.add(websocket)
    await websocket.send(json.dumps(snapshot("countdown")))
    try:
        async for raw in websocket:
            try:
                message = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if message.get("type") == "ping":
                await websocket.send(json.dumps({"type": "pong"}))
            elif message.get("type") == "place_bet":
                chat_id = str(message.get("chatId", "demo"))
                player = {"chatId": chat_id, "name": "Demo Player", "betAmount": float(message.get("betAmount", 1) or 1), "cashedOut": False, "isPending": False}
                players[chat_id] = player
                await websocket.send(json.dumps({"type": "bet_response", "success": True}))
                await websocket.send(json.dumps({"type": "pending_bet_added", "player": player}))
                await websocket.send(json.dumps({"type": "self_roster_entry", "player": player}))
            elif message.get("type") == "cancel_bet":
                players.pop(str(message.get("chatId", "demo")), None)
                await websocket.send(json.dumps({"type": "bet_cancelled"}))
            elif message.get("type") == "cash_out":
                chat_id = str(message.get("chatId", "demo"))
                player = players.get(chat_id)
                if player:
                    player["cashedOut"] = True
                    player["cashOutMultiplier"] = float(message.get("multiplier", 1))
                await websocket.send(json.dumps({"type": "player_cashed_out", "chatId": chat_id, "multiplier": message.get("multiplier", 1), "winAmount": player.get("betAmount", 1) if player else 0}))
    finally:
        clients.discard(websocket)


async def main():
    async with websockets.serve(handle, "localhost", 8765):
        await game_loop()


asyncio.run(main())
