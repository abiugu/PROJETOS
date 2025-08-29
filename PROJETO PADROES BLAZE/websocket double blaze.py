# -*- coding: utf-8 -*-
import json
import time
import threading
from datetime import datetime, timedelta
import websocket  # pip install websocket-client

# Opcional: usar API só quando o WSS não trouxer o número (deixe False para ficar limpo)
USE_API_FALLBACK = False
if USE_API_FALLBACK:
    import requests

WS_URL = "wss://api-gaming.blaze.bet.br/replication/?EIO=3&transport=websocket"
PING_EVERY = 20

ROOMS = ["double_room_1", "double_room", "double_v2"]

socketio_opened = False
room_idx = 0
last_round_ts = 0.0
ultimo_uid = None  # dedupe por created_at ou id de payload

def cor_nome(c):
    return "BRANCO" if c == 0 else "VERMELHO" if c == 1 else "PRETO" if c == 2 else str(c)

def _ping_loop(ws):
    while True:
        try:
            if not ws or not ws.sock or not ws.sock.connected:
                break
            ws.send("2")
        except Exception:
            break
        time.sleep(PING_EVERY)

def _subscribe(ws):
    room = ROOMS[room_idx % len(ROOMS)]
    frame = f'42["cmd",{{"id":"subscribe","payload":{{"room":"{room}"}}}}]'
    try:
        ws.send(frame)
    except Exception:
        try:
            ws.send(f'423["cmd",{{"id":"subscribe","payload":{{"room":"{room}"}}}}]')
        except Exception:
            pass

def _watchdog(ws):
    global room_idx, last_round_ts
    while True:
        time.sleep(10)
        if not ws or not ws.sock or not ws.sock.connected or not socketio_opened:
            break
        if time.time() - last_round_ts > 30:
            room_idx = (room_idx + 1) % len(ROOMS)
            _subscribe(ws)

def on_open(ws):
    global socketio_opened, last_round_ts
    socketio_opened = False
    last_round_ts = 0.0
    try:
        ws.send("40")  # abre namespace socket.io
        socketio_opened = True
    except Exception:
        pass
    threading.Thread(target=_ping_loop, args=(ws,), daemon=True).start()
    threading.Thread(target=_watchdog, args=(ws,), daemon=True).start()
    _subscribe(ws)

def _find(obj, keys):
    if isinstance(obj, dict):
        for k in keys:
            if k in obj and obj[k] is not None:
                return obj[k]
        for v in obj.values():
            r = _find(v, keys)
            if r is not None:
                return r
    elif isinstance(obj, list):
        for it in obj:
            r = _find(it, keys)
            if r is not None:
                return r
    return None

def _parse_horario(iso):
    if not iso:
        return datetime.now().strftime("%H:%M:%S")
    for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return (datetime.strptime(iso, fmt) - timedelta(hours=3)).strftime("%H:%M:%S")
        except Exception:
            continue
    return datetime.now().strftime("%H:%M:%S")

def _buscar_numero_api(created_at):
    if not (USE_API_FALLBACK and created_at):
        return None
    try:
        r = requests.get(
            "https://blaze.bet.br/api/singleplayer-originals/originals/roulette_games/recent/history/1",
            timeout=3
        )
        data = r.json()
        for rec in data.get("records", []):
            if rec.get("created_at") == created_at:
                for k in ("roll", "number", "roll_number", "result", "value"):
                    if rec.get(k) is not None:
                        return rec[k]
    except Exception:
        pass
    return None

def on_message(ws, message: str):
    global ultimo_uid, last_round_ts, socketio_opened
    try:
        if message in ("2", "3"):  # ping/pong
            return
        if message == "0":         # abre engine.io
            try:
                ws.send("40")
                socketio_opened = True
            except Exception:
                pass
            return
        if message == "40":        # ok socket.io
            socketio_opened = True
            return
        if not message.startswith("42"):
            return

        arr = json.loads(message[2:])  # [event, body]
        if not (isinstance(arr, list) and len(arr) >= 2):
            return
        body = arr[1]

        # busca profunda
        cor     = _find(body, ("color","colour","cor"))
        numero  = _find(body, ("roll","number","value","result","roll_number","rolledNumber","winning_number"))
        created = _find(body, ("created_at","createdAt","time","timestamp"))

        # id de rodada para dedupe (evita usar "double.tick")
        rid = None
        payload = body.get("payload", body) if isinstance(body, dict) else None
        if isinstance(payload, dict):
            rid = payload.get("id")
        if isinstance(rid, str) and rid.startswith("double."):
            rid = None
        uid = created or rid

        # só quando tiver cor válida
        if cor not in (0,1,2):
            return

        # tenta pegar número via API se faltou e fallback ligado
        if numero is None:
            numero = _buscar_numero_api(created)
            if numero is None:
                return  # queremos imprimir apenas quando já houver número

        # dedupe
        if uid and uid == ultimo_uid:
            return
        ultimo_uid = uid

        # imprime formato único
        print(f"{_parse_horario(created)} -> {cor_nome(cor)} ({numero})")
        last_round_ts = time.time()

    except Exception:
        pass

def on_error(ws, error): pass
def on_close(ws, code, msg): pass

def iniciar_ws():
    while True:
        try:
            ws = websocket.WebSocketApp(
                WS_URL,
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close,
            )
            ws.run_forever(ping_interval=30, ping_timeout=10)
        except Exception:
            pass
        time.sleep(5)

if __name__ == "__main__":
    iniciar_ws()
