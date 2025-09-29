import json
import time
import threading
from datetime import datetime, timedelta
import websocket  # pip install websocket-client
import pandas as pd
import os

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

# Criando um dataframe pandas para armazenar os dados
columns = ['Horário', 'Cor', 'Número', 'Criado em', 'Total Apostado BRANCO', 'Total Apostado VERMELHO', 
           'Total Apostado PRETO', 'Percentual BRANCO', 'Percentual VERMELHO', 'Percentual PRETO', 
           'MAIOR PERCENTUAL', 'GANHADOR']
df = pd.DataFrame(columns=columns)

# Caminho para o JSON (na raiz do script)
json_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "resultados_acumulados.json")

# Caminho para salvar o arquivo Excel na área de trabalho
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
excel_file_path = os.path.join(desktop_path, "resultados_completos_jogadas.xlsx")

# Função para salvar os dados no Excel a cada 1 minuto
def save_to_excel():
    while True:
        try:
            time.sleep(60)  # Aguarda 1 minuto
            if not df.empty:
                # Salvando no Excel
                df.to_excel(excel_file_path, index=False)
                print(f"Arquivo Excel atualizado com sucesso! Salvo em {excel_file_path}")
        except Exception as e:
            print(f"Erro ao tentar salvar o arquivo Excel: {e}. Tentando novamente em 1 minuto.")
            time.sleep(60)  # Se ocorrer erro, tenta novamente após 1 minuto

# Função para carregar dados acumulados do JSON
def load_json_data():
    if os.path.exists(json_file_path):
        try:
            with open(json_file_path, 'r') as f:
                data = json.load(f)
                return pd.DataFrame(data)
        except Exception as e:
            print(f"Erro ao carregar os dados do arquivo JSON: {e}")
    return pd.DataFrame(columns=columns)

# Função para salvar dados acumulados no JSON
def save_json_data():
    while True:
        try:
            time.sleep(60)  # Aguarda 1 minuto
            if not df.empty:
                with open(json_file_path, 'w') as f:
                    json.dump(df.to_dict(orient="records"), f, indent=4)
                print(f"Dados acumulados salvos no arquivo JSON: {json_file_path}")
        except Exception as e:
            print(f"Erro ao tentar salvar o arquivo JSON: {e}. Tentando novamente em 1 minuto.")
            time.sleep(60)  # Se ocorrer erro, tenta novamente após 1 minuto

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

# Variáveis para controlar o fim da rodada
is_round_complete = False
current_round_id = None

def on_message(ws, message: str):
    global ultimo_uid, last_round_ts, socketio_opened, is_round_complete, current_round_id
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

        # Verifica se a rodada está finalizada
        if "end" in body:
            is_round_complete = True
            current_round_id = body.get("round_id")
            print(f"Rodada {current_round_id} finalizada, aguardando 3 segundos para processar as apostas.")

        # Buscar cor, número e apostas de maneira profunda
        cor     = _find(body, ("color","colour","cor"))
        numero  = _find(body, ("roll","number","value","result","roll_number","rolledNumber","winning_number"))
        apostas = _find(body, ("bets", "stake", "wager", "player_bet"))
        created = _find(body, ("created_at","createdAt","time","timestamp"))

        # id de rodada para dedupe (evita usar "double.tick")
        rid = None
        payload = body.get("payload", body) if isinstance(body, dict) else None
        if isinstance(payload, dict):
            rid = payload.get("id")
        if isinstance(rid, str) and rid.startswith("double.") :
            rid = None
        uid = created or rid

        # Só quando tiver cor válida
        if cor not in (0,1,2):
            return

        # Tenta pegar número via API se faltou e fallback ligado
        if numero is None:
            numero = _buscar_numero_api(created)
            if numero is None:
                return  # Queremos imprimir apenas quando já houver número

        # Deduplicação
        if uid and uid == ultimo_uid:
            return
        ultimo_uid = uid

        # Aguarda 3 segundos se a rodada estiver finalizada
        if is_round_complete:
            time.sleep(3)

        # Calcular o total apostado por cor
        total_apostado = {0: 0, 1: 0, 2: 0}  # Inicializa o total de apostas por cor (branco, vermelho, preto)
        
        if apostas:
            for aposta in apostas:
                color = aposta.get("color")
                amount = float(aposta.get("amount", 0))
                if color in total_apostado:
                    total_apostado[color] += amount

        # Calcular os percentuais
        total_geral = sum(total_apostado.values())
        if total_geral > 0:
            percentual_branco = round((total_apostado[0] / total_geral) * 100, 2)
            percentual_vermelho = round((total_apostado[1] / total_geral) * 100, 2)
            percentual_preto = round((total_apostado[2] / total_geral) * 100, 2)
        else:
            percentual_branco = percentual_vermelho = percentual_preto = 0.0

        # Determinar o maior percentual entre vermelho e preto
        maior_percentual_rp = max(percentual_vermelho, percentual_preto)

        # Determinar ganhador
        if cor == 0:  # Branco
            ganhador = "CORINGA"
        elif cor == 1:  # Vermelho
            ganhador = "PLAYER" if percentual_vermelho == maior_percentual_rp else "CASA"
        else:  # Preto
            ganhador = "PLAYER" if percentual_preto == maior_percentual_rp else "CASA"

        # Extrair todos os dados da mensagem para salvar no Excel
        horario = _parse_horario(created)
        cor_nome_str = cor_nome(cor)

        # Salva no dataframe pandas com arredondamento
        df.loc[len(df)] = [
            horario,
            cor_nome_str,
            numero,
            created,
            round(total_apostado[0], 2),  # Total apostado para BRANCO (2 casas decimais)
            round(total_apostado[1], 2),  # Total apostado para VERMELHO (2 casas decimais)
            round(total_apostado[2], 2),  # Total apostado para PRETO (2 casas decimais)
            round(percentual_branco, 2),  # Percentual BRANCO (2 casas decimais)
            round(percentual_vermelho, 2),  # Percentual VERMELHO (2 casas decimais)
            round(percentual_preto, 2),  # Percentual PRETO (2 casas decimais)
            maior_percentual_rp,  # Maior percentual
            ganhador  # Ganhador
        ]
        last_round_ts = time.time()

        # Imprime formato único no terminal
        print(f"{horario} -> {cor_nome_str} ({numero}) - Total Apostado BRANCO: {round(total_apostado[0], 2)}, VERMELHO: {round(total_apostado[1], 2)}, PRETO: {round(total_apostado[2], 2)}")
        print(f"Percentual BRANCO: {round(percentual_branco, 2)}%, VERMELHO: {round(percentual_vermelho, 2)}%, PRETO: {round(percentual_preto, 2)}%")

        # Resetar o status da rodada após processar
        is_round_complete = False

    except Exception as e:
        print(f"Erro ao processar a mensagem: {e}")

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
    # Carregar os dados acumulados do JSON ao iniciar
    df = load_json_data()

    # Iniciar os threads de salvamento a cada 1 minuto
    threading.Thread(target=save_to_excel, daemon=True).start()
    threading.Thread(target=save_json_data, daemon=True).start()
    
    # Iniciar WebSocket
    iniciar_ws()
