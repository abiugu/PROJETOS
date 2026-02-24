import websocket
import json
import time
import threading
import requests
from collections import deque
import logging

# ======== 1) CONFIG ===========================================================
WS_URL = "wss://api-gaming.blaze.bet.br/replication/?EIO=3&transport=websocket"
ROOMS = ["double_room_1", "double_room", "double_v2"]  # Salas para monitorar
MAX_HISTORY = 100  # Número máximo de rodadas armazenadas
MAX_RECONNECT_ATTEMPTS = 5  # Número máximo de tentativas de reconexão

# Variáveis globais
_ws_cores = deque(maxlen=MAX_HISTORY)  # Fila para armazenar cores das últimas rodadas
_ws_numeros = deque(maxlen=MAX_HISTORY)  # Fila para armazenar números das últimas rodadas
_processed_rounds = set()  # Conjunto para armazenar os round_id das rodadas já processadas
_last_white_alarm_uid = None  # Para garantir que os alertas não sejam repetidos
_processed_patterns = set()  # Armazenar combinações de cores com os respectivos IDs processados
reconnect_attempts = 0  # Contador de tentativas de reconexão

# Define seu token de bot do Telegram e o ID do chat (substitua pelos seus dados)
TELEGRAM_TOKEN = "8426186947:AAFd4ZSTWfnffJGusY9CiOka0oblLpQvsgU"
CHAT_ID = "1139158385"

# ======== 2) FUNÇÕES DE SUPORTE ===========================================

def calcular_percentuais_ultimas_100():
    """Calcula os percentuais de Preto e Vermelho nas últimas 100 rodadas."""
    total = len(_ws_cores)
    if total == 0:
        return 0.0, 0.0  # Evitar divisão por zero, retornando 0 para ambos os percentuais

    count_preto = sum(1 for c in _ws_cores if c == 2)
    count_vermelho = sum(1 for c in _ws_cores if c == 1)

    perc_preto = (count_preto / total) * 100
    perc_vermelho = (count_vermelho / total) * 100

    return perc_preto, perc_vermelho

def enviar_telegram(mensagem):
    """Envia uma mensagem para o Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    params = {
        "chat_id": CHAT_ID,
        "text": mensagem,
        "parse_mode": "Markdown"
    }
    response = requests.get(url, params=params)
    return response.json()

def _ws_cor_nome(c):
    """Converte código da cor para nome"""
    return "BRANCO" if c == 0 else "VERMELHO" if c == 1 else "PRETO" if c == 2 else "DESCONHECIDO"

def _ws_find(obj, keys):
    """Busca uma chave dentro de um dicionário ou lista recursivamente."""
    if isinstance(obj, dict):
        for k in keys:
            if k in obj and obj[k] is not None:
                return obj[k]
        for v in obj.values():
            r = _ws_find(v, keys)
            if r is not None:
                return r
    elif isinstance(obj, list):
        for it in obj:
            r = _ws_find(it, keys)
            if r is not None:
                return r
    return None

def _ws_try_extract_full(body):
    """Tenta extrair as informações principais da resposta do WebSocket.""" 
    if not isinstance(body, dict): return None, None, None, None
    cor = _ws_find(body, ("color", "colour", "cor"))
    created_at = _ws_find(body, ("created_at", "createdAt", "time", "timestamp"))
    numero = _ws_find(body, ("roll", "number", "value", "result", "roll_number", "rolledNumber", "winning_number"))
    round_id = None
    payload = body.get("payload", body)
    if isinstance(payload, dict):
        rid = payload.get("id")
        if isinstance(rid, str) and not rid.startswith("double.") :
            round_id = rid  # Usa o ID da rodada se for válido

    return cor, numero, round_id

# ======== 3) FUNÇÕES DE WebSocket ===========================================
def _ws_on_message(ws, message):
    """Processa as mensagens recebidas do WebSocket e extrai as cores e números"""
    try:
        if isinstance(message, (bytes, bytearray)):
            message = message.decode("utf-8", "ignore")
        
        if message in ("2", "3"):  # Ignora mensagens de controle
            return

        # Extrai os pacotes JSON
        for raw in _ws_iter_json_packets(message) or []:
            try:
                data = json.loads(raw)
            except Exception:
                continue

            if not (isinstance(data, list) and len(data) >= 2):
                continue

            body = data[1]
            cor, numero, round_id = _ws_try_extract_full(body)
            
            if cor not in (0, 1, 2) or numero is None or round_id is None:
                continue

            # Verifica se o round_id já foi processado
            if round_id in _processed_rounds:
                continue  # Ignora a rodada se já foi processada

            # Se for uma nova rodada, processa e armazena o round_id
            _processed_rounds.add(round_id)

            # Armazena os resultados das rodadas nas filas
            _ws_cores.append(cor)
            _ws_numeros.append(numero)
            hora_atual = time.strftime("%H:%M:%S")
            # Exibe no terminal a rodada extraída
            print(f"Cor: {_ws_cor_nome(cor)} | Número: {numero} | Round ID: {round_id} | Hora: {hora_atual}")

            # Verifica as sequências de cores após armazenar a nova rodada
            verificar_sequencia_de_cores()

    except Exception as e:
        print(f"[WS] erro ao processar a mensagem: {e}")
        # Ignora erros e continua o processamento

def _ws_iter_json_packets(msg: str):
    """Itera pelas mensagens JSON recebidas.""" 
    packets, i = [], msg.find('[')
    while i != -1:
        depth = 0; in_str = False; esc = False; end = None
        for j, ch in enumerate(msg[i:], start=i):
            if in_str:
                if esc: esc = False
                elif ch == '\\': esc = True
                elif ch == '"': in_str = False
            else:
                if ch == '"': in_str = True
                elif ch == '[': depth += 1
                elif ch == ']':
                    depth -= 1
                    if depth == 0: end = j + 1; break
        if end is None: break
        packets.append(msg[i:end])
        i = msg.find('[', end)
    return packets

def _ws_on_open(ws):
    """Callback quando o WebSocket é aberto.""" 
    _ws_subscribe(ws)

def _ws_subscribe(ws):
    """Inscreve o WebSocket nas salas da lista `ROOMS`.""" 
    for room in ROOMS:
        frame = f'42["cmd",{{"id":"subscribe","payload":{{"room":"{room}"}}}}]'
        try:
            ws.send(frame)
        except Exception as e:
            print(f"[WS] Erro ao tentar se inscrever na sala {room}: {e}")

def _ws_on_error(ws, error):
    """Callback quando ocorre um erro no WebSocket.""" 
    global reconnect_attempts
    logging.error(f"[WS] Erro: {error}")
    print(f"[WS] Erro: {error}")
    
    if reconnect_attempts < MAX_RECONNECT_ATTEMPTS:
        reconnect_attempts += 1
        reconnect(ws)
    else:
        print("Número máximo de tentativas de reconexão alcançado. Encerrando.")

def _ws_on_close(ws, close_status_code, close_msg):
    """Callback quando o WebSocket é fechado.""" 
    global reconnect_attempts
    if reconnect_attempts < MAX_RECONNECT_ATTEMPTS:
        reconnect_attempts += 1
        reconnect(ws)
    else:
        print("Número máximo de tentativas de reconexão alcançado. Encerrando.")

def reconnect(ws):
    """Tenta reconectar o WebSocket após um erro ou desconexão"""
    global reconnect_attempts
    if reconnect_attempts >= MAX_RECONNECT_ATTEMPTS:
        print("Número máximo de reconexões atingido, não tentando mais.")
        return  # Evita nova tentativa de reconexão se o limite for atingido.

    time.sleep(1)  # Aguarda 1 segundo antes de tentar reconectar
    threading.Thread(target=iniciar_websocket).start()  # Usando thread para reconectar sem bloquear a execução

def iniciar_websocket():
    """Inicia a conexão WebSocket e a inscrição nas salas.""" 
    global reconnect_attempts
    reconnect_attempts = 0  # Resetando o contador de tentativas ao iniciar a conexão
    ws = websocket.WebSocketApp(
        WS_URL, 
        on_open=_ws_on_open, 
        on_message=_ws_on_message,
        on_error=_ws_on_error, 
        on_close=_ws_on_close
    )
    ws.run_forever(ping_interval=30, ping_timeout=10, reconnect=True)  # Habilita reconexão automática

def send_ping(ws):
    """Envia um ping manual para manter a conexão ativa"""
    while True:
        time.sleep(30)  # Intervalo para enviar pings
        try:
            ws.ping("ping")  # Envia o ping manualmente
        except Exception as e:
            print(f"[WS] Erro ao enviar ping: {e}")
            break  # Se falhar, interrompe o envio de pings

# ======== 4) FUNÇÕES DE VERIFICAÇÃO E ALERTA ===========================================
def verificar_sequencia_de_cores():
    """Verifica se as sequências especificadas foram detectadas:
    Sequências de 5 cores:
    1. BRANCO → PRETO → VERMELHO → VERMELHO → BRANCO
    2. VERMELHO → BRANCO → PRETO → BRANCO → PRETO
    3. PRETO → VERMELHO → VERMELHO → BRANCO → BRANCO
    4. BRANCO → VERMELHO → PRETO → BRANCO → PRETO
    
    Sequências de 6 cores:
    1. BRANCO → PRETO → VERMELHO → VERMELHO → BRANCO → VERMELHO
    2. PRETO → VERMELHO → VERMELHO → BRANCO → BRANCO → PRETO
    3. VERMELHO → PRETO → PRETO → BRANCO → VERMELHO → BRANCO
    4. PRETO → PRETO → BRANCO → VERMELHO → BRANCO → VERMELHO
    5. VERMELHO → VERMELHO → VERMELHO → BRANCO → BRANCO
    6. BRANCO → PRETO → BRANCO → PRETO → PRETO → PRETO
    """
    global _ws_cores, _processed_patterns

    # Sequências de 5 cores
    if len(_ws_cores) >= 5:
        # Sequência 1: BRANCO → PRETO → VERMELHO → VERMELHO → BRANCO
        if (_ws_cor_nome(_ws_cores[-5]) == "BRANCO" and 
            _ws_cor_nome(_ws_cores[-4]) == "PRETO" and 
            _ws_cor_nome(_ws_cores[-3]) == "VERMELHO" and 
            _ws_cor_nome(_ws_cores[-2]) == "VERMELHO" and 
            _ws_cor_nome(_ws_cores[-1]) == "BRANCO"):
            if ("BRANCO", "PRETO", "VERMELHO", "VERMELHO", "BRANCO") not in _processed_patterns:
                _processed_patterns.add(("BRANCO", "PRETO", "VERMELHO", "VERMELHO", "BRANCO"))
                print(f"⚫Sequência detectada (preto)⚫: BRANCO → PRETO → VERMELHO → VERMELHO → BRANCO")
                perc_preto, perc_vermelho = calcular_percentuais_ultimas_100()
                mensagem = (
                    f"🚨 Alerta: ⚫Sequência detectada (preto)⚫ - BRANCO → PRETO → VERMELHO → VERMELHO → BRANCO 🚨\n"
                    f"🕒 Hora: {time.strftime('%H:%M:%S')}\n"
                    f"⚫ Percentual de Preto nas últimas 100 rodadas: {perc_preto:.2f}%\n"
                    f"🔴 Percentual de Vermelho nas últimas 100 rodadas: {perc_vermelho:.2f}%"
                )
                enviar_telegram(mensagem)

        # Sequência 2: VERMELHO → BRANCO → PRETO → BRANCO → PRETO
        elif (_ws_cor_nome(_ws_cores[-5]) == "VERMELHO" and 
              _ws_cor_nome(_ws_cores[-4]) == "BRANCO" and 
              _ws_cor_nome(_ws_cores[-3]) == "PRETO" and 
              _ws_cor_nome(_ws_cores[-2]) == "BRANCO" and 
              _ws_cor_nome(_ws_cores[-1]) == "PRETO"):
            if ("VERMELHO", "BRANCO", "PRETO", "BRANCO", "PRETO") not in _processed_patterns:
                _processed_patterns.add(("VERMELHO", "BRANCO", "PRETO", "BRANCO", "PRETO"))
                print(f"⚫Sequência detectada (preto)⚫: VERMELHO → BRANCO → PRETO → BRANCO → PRETO")
                perc_preto, perc_vermelho = calcular_percentuais_ultimas_100()
                mensagem = (
                    f"🚨 Alerta: ⚫Sequência detectada (preto)⚫ - VERMELHO → BRANCO → PRETO → BRANCO → PRETO 🚨\n"
                    f"🕒 Hora: {time.strftime('%H:%M:%S')}\n"
                    f"⚫ Percentual de Preto nas últimas 100 rodadas: {perc_preto:.2f}%\n"
                    f"🔴 Percentual de Vermelho nas últimas 100 rodadas: {perc_vermelho:.2f}%"
                )
                enviar_telegram(mensagem)

        # Sequência 3: PRETO → VERMELHO → VERMELHO → BRANCO → BRANCO
        elif (_ws_cor_nome(_ws_cores[-5]) == "PRETO" and 
              _ws_cor_nome(_ws_cores[-4]) == "VERMELHO" and 
              _ws_cor_nome(_ws_cores[-3]) == "VERMELHO" and 
              _ws_cor_nome(_ws_cores[-2]) == "BRANCO" and 
              _ws_cor_nome(_ws_cores[-1]) == "BRANCO"):
            if ("PRETO", "VERMELHO", "VERMELHO", "BRANCO", "BRANCO") not in _processed_patterns:
                _processed_patterns.add(("PRETO", "VERMELHO", "VERMELHO", "BRANCO", "BRANCO"))
                print(f"⚫Sequência detectada (preto)⚫: PRETO → VERMELHO → VERMELHO → BRANCO → BRANCO")
                perc_preto, perc_vermelho = calcular_percentuais_ultimas_100()
                mensagem = (
                    f"🚨 Alerta: ⚫Sequência detectada (preto)⚫ - PRETO → VERMELHO → VERMELHO → BRANCO → BRANCO 🚨\n"
                    f"🕒 Hora: {time.strftime('%H:%M:%S')}\n"
                    f"⚫ Percentual de Preto nas últimas 100 rodadas: {perc_preto:.2f}%\n"
                    f"🔴 Percentual de Vermelho nas últimas 100 rodadas: {perc_vermelho:.2f}%"
                )
                enviar_telegram(mensagem)

        # Sequência 4: BRANCO → VERMELHO → PRETO → BRANCO → PRETO
        elif (_ws_cor_nome(_ws_cores[-5]) == "BRANCO" and 
              _ws_cor_nome(_ws_cores[-4]) == "VERMELHO" and 
              _ws_cor_nome(_ws_cores[-3]) == "PRETO" and 
              _ws_cor_nome(_ws_cores[-2]) == "BRANCO" and 
              _ws_cor_nome(_ws_cores[-1]) == "PRETO"):
            if ("BRANCO", "VERMELHO", "PRETO", "BRANCO", "PRETO") not in _processed_patterns:
                _processed_patterns.add(("BRANCO", "VERMELHO", "PRETO", "BRANCO", "PRETO"))
                print(f"🔴Sequência detectada (vermelho)🔴: BRANCO → VERMELHO → PRETO → BRANCO → PRETO")
                perc_preto, perc_vermelho = calcular_percentuais_ultimas_100()
                mensagem = (
                    f"🚨 Alerta: 🔴Sequência detectada (vermelho)🔴 - BRANCO → VERMELHO → PRETO → BRANCO → PRETO 🚨\n"
                    f"🕒 Hora: {time.strftime('%H:%M:%S')}\n"
                    f"⚫ Percentual de Preto nas últimas 100 rodadas: {perc_preto:.2f}%\n"
                    f"🔴 Percentual de Vermelho nas últimas 100 rodadas: {perc_vermelho:.2f}%"
                )
                enviar_telegram(mensagem)
        
                # Sequência 5: VERMELHO → VERMELHO → VERMELHO → BRANCO → BRANCO
        elif (_ws_cor_nome(_ws_cores[-5]) == "VERMELHO" and 
              _ws_cor_nome(_ws_cores[-4]) == "VERMELHO" and 
              _ws_cor_nome(_ws_cores[-3]) == "VERMELHO" and 
              _ws_cor_nome(_ws_cores[-2]) == "BRANCO" and 
              _ws_cor_nome(_ws_cores[-1]) == "BRANCO"):
            if ("VERMELHO", "VERMELHO", "VERMELHO", "BRANCO", "BRANCO") not in _processed_patterns:
                _processed_patterns.add(("VERMELHO", "VERMELHO", "VERMELHO", "BRANCO", "BRANCO"))
                print(f"🔴Sequência detectada (vermelho)🔴: VERMELHO → VERMELHO → VERMELHO → BRANCO → BRANCO")
                perc_preto, perc_vermelho = calcular_percentuais_ultimas_100()
                mensagem = (
                    f"🚨 Alerta: 🔴Sequência detectada (vermelho)🔴 - VERMELHO → VERMELHO → VERMELHO → BRANCO → BRANCO 🚨\n"
                    f"🕒 Hora: {time.strftime('%H:%M:%S')}\n"
                    f"⚫ Percentual de Preto nas últimas 100 rodadas: {perc_preto:.2f}%\n"
                    f"🔴 Percentual de Vermelho nas últimas 100 rodadas: {perc_vermelho:.2f}%"
                )
                enviar_telegram(mensagem)


    # Sequências de 6 cores
    if len(_ws_cores) >= 6:
        # Sequência 1: BRANCO → PRETO → VERMELHO → VERMELHO → BRANCO → VERMELHO
        if (_ws_cor_nome(_ws_cores[-6]) == "BRANCO" and 
            _ws_cor_nome(_ws_cores[-5]) == "PRETO" and 
            _ws_cor_nome(_ws_cores[-4]) == "VERMELHO" and 
            _ws_cor_nome(_ws_cores[-3]) == "VERMELHO" and 
            _ws_cor_nome(_ws_cores[-2]) == "BRANCO" and 
            _ws_cor_nome(_ws_cores[-1]) == "VERMELHO"):
            if ("BRANCO", "PRETO", "VERMELHO", "VERMELHO", "BRANCO", "VERMELHO") not in _processed_patterns:
                _processed_patterns.add(("BRANCO", "PRETO", "VERMELHO", "VERMELHO", "BRANCO", "VERMELHO"))
                print(f"⚫Sequência detectada (preto)⚫: BRANCO → PRETO → VERMELHO → VERMELHO → BRANCO → VERMELHO")
                perc_preto, perc_vermelho = calcular_percentuais_ultimas_100()
                mensagem = (
                    f"🚨 Alerta: ⚫Sequência detectada (preto)⚫ - BRANCO → PRETO → VERMELHO → VERMELHO → BRANCO → VERMELHO 🚨\n"
                    f"🕒 Hora: {time.strftime('%H:%M:%S')}\n"
                    f"⚫ Percentual de Preto nas últimas 100 rodadas: {perc_preto:.2f}%\n"
                    f"🔴 Percentual de Vermelho nas últimas 100 rodadas: {perc_vermelho:.2f}%"
                )
                enviar_telegram(mensagem)

        # Sequência 2: PRETO → VERMELHO → VERMELHO → BRANCO → BRANCO → PRETO
        elif (_ws_cor_nome(_ws_cores[-6]) == "PRETO" and 
              _ws_cor_nome(_ws_cores[-5]) == "VERMELHO" and 
              _ws_cor_nome(_ws_cores[-4]) == "VERMELHO" and 
              _ws_cor_nome(_ws_cores[-3]) == "BRANCO" and 
              _ws_cor_nome(_ws_cores[-2]) == "BRANCO" and 
              _ws_cor_nome(_ws_cores[-1]) == "PRETO"):
            if ("PRETO", "VERMELHO", "VERMELHO", "BRANCO", "BRANCO", "PRETO") not in _processed_patterns:
                _processed_patterns.add(("PRETO", "VERMELHO", "VERMELHO", "BRANCO", "BRANCO", "PRETO"))
                print(f"⚫Sequência detectada (preto)⚫: PRETO → VERMELHO → VERMELHO → BRANCO → BRANCO → PRETO")
                perc_preto, perc_vermelho = calcular_percentuais_ultimas_100()
                mensagem = (
                    f"🚨 Alerta: ⚫Sequência detectada (preto)⚫ - PRETO → VERMELHO → VERMELHO → BRANCO → BRANCO → PRETO 🚨\n"
                    f"🕒 Hora: {time.strftime('%H:%M:%S')}\n"
                    f"⚫ Percentual de Preto nas últimas 100 rodadas: {perc_preto:.2f}%\n"
                    f"🔴 Percentual de Vermelho nas últimas 100 rodadas: {perc_vermelho:.2f}%"
                )
                enviar_telegram(mensagem)

        # Sequência 3: PRETO → PRETO → BRANCO → VERMELHO → BRANCO → VERMELHO
        elif (_ws_cor_nome(_ws_cores[-6]) == "PRETO" and 
              _ws_cor_nome(_ws_cores[-5]) == "PRETO" and 
              _ws_cor_nome(_ws_cores[-4]) == "BRANCO" and 
              _ws_cor_nome(_ws_cores[-3]) == "VERMELHO" and 
              _ws_cor_nome(_ws_cores[-2]) == "BRANCO" and 
              _ws_cor_nome(_ws_cores[-1]) == "VERMELHO"):
            if ("PRETO", "PRETO", "BRANCO", "VERMELHO", "BRANCO", "VERMELHO") not in _processed_patterns:
                _processed_patterns.add(("PRETO", "PRETO", "BRANCO", "VERMELHO", "BRANCO", "VERMELHO"))
                print(f"⚫Sequência detectada (preto)⚫: PRETO → PRETO → BRANCO → VERMELHO → BRANCO → VERMELHO")
                perc_preto, perc_vermelho = calcular_percentuais_ultimas_100()
                mensagem = (
                    f"🚨 Alerta: ⚫Sequência detectada (preto)⚫ - PRETO → PRETO → BRANCO → VERMELHO → BRANCO → VERMELHO 🚨\n"
                    f"🕒 Hora: {time.strftime('%H:%M:%S')}\n"
                    f"⚫ Percentual de Preto nas últimas 100 rodadas: {perc_preto:.2f}%\n"
                    f"🔴 Percentual de Vermelho nas últimas 100 rodadas: {perc_vermelho:.2f}%"
                )
                enviar_telegram(mensagem)

        # Sequência 4: BRANCO → PRETO → BRANCO → PRETO → PRETO → PRETO
        elif (_ws_cor_nome(_ws_cores[-6]) == "BRANCO" and 
              _ws_cor_nome(_ws_cores[-5]) == "PRETO" and 
              _ws_cor_nome(_ws_cores[-4]) == "BRANCO" and 
              _ws_cor_nome(_ws_cores[-3]) == "PRETO" and 
              _ws_cor_nome(_ws_cores[-2]) == "PRETO" and 
              _ws_cor_nome(_ws_cores[-1]) == "PRETO"):
            if ("BRANCO", "PRETO", "BRANCO", "PRETO", "PRETO", "PRETO") not in _processed_patterns:
                _processed_patterns.add(("BRANCO", "PRETO", "BRANCO", "PRETO", "PRETO", "PRETO"))
                print(f"🔴Sequência detectada (vermelho)🔴: BRANCO → PRETO → BRANCO → PRETO → PRETO → PRETO")
                perc_preto, perc_vermelho = calcular_percentuais_ultimas_100()
                mensagem = (
                    f"🚨 Alerta: 🔴Sequência detectada (vermelho)🔴 - BRANCO → PRETO → BRANCO → PRETO → PRETO → PRETO 🚨\n"
                    f"🕒 Hora: {time.strftime('%H:%M:%S')}\n"
                    f"⚫ Percentual de Preto nas últimas 100 rodadas: {perc_preto:.2f}%\n"
                    f"🔴 Percentual de Vermelho nas últimas 100 rodadas: {perc_vermelho:.2f}%"
                )
                enviar_telegram(mensagem)

# Inicia o WebSocket
if __name__ == "__main__":
    iniciar_websocket()
