from flask import Flask, render_template_string, url_for
import requests, json, os, threading, time, pandas as pd
from datetime import datetime, timedelta, date
from collections import Counter, deque
import atexit, websocket
from alarms import ALARM_PROB100, ALARM_PROB50, ALARM_PROB100_PROB50

# ======== 1) CONFIG ===========================================================
API_HISTORY_URL = "https://blaze.bet.br/api/singleplayer-originals/originals/roulette_games/recent/history"
WS_URL = "wss://api-gaming.blaze.bet.br/replication/?EIO=3&transport=websocket"

BOT_TOKEN = '8426186947:AAFd4ZSTWfnffJGusY9CiOka0oblLpQvsgU'
CHAT_ID   = '1139158385'

ENGINEIO_PING_EVERY = 20             # seg
ROOMS = ["double_room_1", "double_room", "double_v2"]
TG_MIN_INTERVAL = 6                  # anti-flood no TG
SEND_FAST_TG_EVERY_ROUND = False
SEND_FAST_TG_ON_CHANGE   = True
MIN_RODADAS_PARA_ALARME  = 100       # gating
ARQUIVO_JSON = f"estatisticas_{date.today()}.json"


# ======== 3) ESTADO GLOBAL ====================================================
app = Flask(__name__)

_ws_lock = threading.RLock()
_ws_cores = deque(maxlen=100)
_ws_horarios = deque(maxlen=100)
_ws_numeros = deque(maxlen=100)
_ws_last_uid = None
_printed_uid = None
_room_idx = 0
_socketio_opened = False
_last_round_ts = 0.0
_ultimo_uid = None
WS_RENDER_CACHE = {}

# WSS -> Telegram fast
_tg_last_combo = None
_tg_last_ts = 0.0
_tg_last_uid = None
ciclos100_preto = 0
ciclos100_vermelhos = 0
ciclos50_pretos = 0
ciclos50_vermelhos = 0
contador_acertos_alarm = {"Prob100": 0, "Prob50": 0, "Prob100 & Prob50": 0}
contador_erros_alarm = {"Prob100": 0, "Prob50": 0, "Prob100 & Prob50": 0}
sequencia_alerta_ativa = False
estrategia_disparada = False  # Variável global para controlar se a estratégia foi disparada

# ======== 4) UTILS: STATS JSON, LABELS, AUX ==================================

def preencher_json_diario_minimo_api(minimo=100, timeout=(4, 8)):
    """
    Baixa as últimas `minimo` rodadas da API e adiciona ao JSON do dia
    """
    try:
        # 1) Buscar da API
        resp = requests.get(f"{API_HISTORY_URL}/1", timeout=timeout)
        data = resp.json()
        
        # Verifique quantos registros foram retornados
        print(f"[API] Registros retornados: {len(data.get('records', []))}")
        
        records = data.get("records") or []
        if not records:
            print("[API] Nenhum record retornado.")
            return False
 
        # Normalizar e ordenar (antigo -> novo)
        norm = []
        for r0 in records:
            cor = r0.get("color")
            if cor not in (0, 1, 2):
                continue
            numero = r0.get("roll")
            created = r0.get("created_at")
            if numero is not None and created:
                norm.append({"color": cor, "created_at": created, "numero": numero})

        if len(norm) < minimo:
            print(f"[API] Menos de {minimo} rodadas retornadas.")
            return False
        
        norm.sort(key=lambda x: (x["created_at"] or ""))  # mais antigo -> mais novo
        
        # Atualiza o histórico local
        stats = load_stats()
        for r in norm:
            processar_resultado_ws_fast(
                r["color"],
                created_at_iso=r.get("created_at"),
                numero=r.get("numero"),
                round_id=r.get("id"),
                bootstrap=True
            )
        
        print(f"[BOOT/API] JSON preenchido com {len(norm)} rodadas.")
        save_stats(stats)
        return True
    except Exception as e:
        print(f"[BOOT/API] Falha ao preencher JSON via API: {e}")
        return False

# Função que salva as estatísticas no arquivo JSON
def save_stats(stats):
    """Salva as estatísticas no arquivo JSON"""
    try:
        tmp = ARQUIVO_JSON + ".tmp"
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=4)
        os.replace(tmp, ARQUIVO_JSON)
        print("[INFO] Dados salvos no JSON com sucesso.")
    except Exception as e:
        print(f"[ERRO] Falha ao salvar no JSON: {e}")

def salvar_em_json(alarme_tipo, previsao_cor, prob100, prob50, horario):
    stats = load_stats()  # Carrega as estatísticas atuais

    # Adiciona a nova jogada ao histórico
    stats['historico_entradas'].insert(0, previsao_cor)
    stats['historico_resultados'].insert(0, alarme_tipo)
    stats['historico_horarios'].insert(0, horario)
    stats['historico_probabilidade_100'].insert(0, prob100)
    stats['historico_probabilidade_50'].insert(0, prob50)
    stats['contador_alertas'] += 1  # Incrementa o contador de alertas
    stats('sequencias_alertadas').insert(0, f"{alarme_tipo} - {horario}")
    # Salva o arquivo JSON com as novas informações
    save_stats(stats)  # Chama a função que realmente salva no JSON

def default_stats():
    return {
        "acertos": 0, "erros": 0,
        "historico_entradas": [], "historico_resultados": [],
        "historico_horarios": [], "historico_resultados_binarios": [],
        "historico_probabilidade_100": [], "historico_probabilidade_50": [],
        "historico_ciclos_preto_100": [], "historico_ciclos_vermelho_100": [],
        "historico_ciclos_preto_50": [],  "historico_ciclos_vermelho_50": [],
        "ultima_analisada": "", "ultima_uid_ws": "",
        "contador_alertas": 0, "sequencia_ativa": False, "estrategia_ativa": "",
        "sequencias_alertadas": []  # Este campo foi adicionado
    }


def load_stats():
    try:
        with open(ARQUIVO_JSON, 'r', encoding='utf-8') as f:
            stats = json.load(f)
            # Certifique-se de que a chave sequencias_alertadas existe e é uma lista
            if 'sequencias_alertadas' not in stats:
                stats['sequencias_alertadas'] = []  # Garante que a chave exista
            if 'contador_alertas' not in stats:
                stats['contador_alertas'] = 0  # Inicializa contador de alertas, se não existir
            return stats
    except Exception as e:
        print(f"[ERRO] Falha ao carregar JSON: {e}")
        return default_stats()  # Retorna valores padrão se ocorrer erro ao carregar


def save_stats(stats):
    """Salva as estatísticas no arquivo JSON"""
    try:
        tmp = ARQUIVO_JSON + ".tmp"
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=4)
        os.replace(tmp, ARQUIVO_JSON)  # Substitui o arquivo original
        print("[INFO] Dados salvos no JSON com sucesso.")
    except Exception as e:
        print(f"[ERRO] Falha ao salvar no JSON: {e}")


def reconstruir_ws_buffers_de_json(max_itens=100):
    """Recarrega _ws_cores/_ws_horarios a partir do JSON diário (mais antigo -> mais novo), mas só se houver no mínimo 100 jogadas."""
    try:
        stats = load_stats()
        historico_resultados = stats.get("historico_resultados", [])
        historico_horarios = stats.get("historico_horarios", [])

        # Verifica se há pelo menos 100 itens no histórico
        if len(historico_resultados) < 100 or len(historico_horarios) < 100:
            print(f"[BOOT] Menos de 100 jogadas no histórico. Usando API para preencher dados...")
            # Preenche com 100 rodadas da API se necessário
            preencher_json_diario_minimo_api(minimo=100)  # Garantir que temos o mínimo de dados
            return

        # Inverte os resultados do JSON para processar do mais antigo ao mais novo
        nomes = list(reversed(historico_resultados[:max_itens]))
        horas = list(reversed(historico_horarios[:max_itens]))

        def nome_para_cor(nome):
            u = (nome or "").upper()
            if "BRANCO" in u:    return 0
            if "VERMELHO" in u:  return 1
            if "PRETO" in u:     return 2
            return 2  # padrão seguro

        with _ws_lock:
            _ws_cores.clear()
            _ws_horarios.clear()
            _ws_numeros.clear()
            for nm, hr in zip(nomes, horas):
                _ws_cores.appendleft(nome_para_cor(nm))
                _ws_horarios.appendleft(hr if hr else "-")
        print(f"[BOOT] Buffers WS reconstruídos do JSON: {len(_ws_cores)} itens.")
        
    except Exception as e:
        print(f"[BOOT] Falha ao reconstruir buffers do JSON: {e}")

# cria o JSON do dia se não existir
if not os.path.exists(ARQUIVO_JSON):
    save_stats(default_stats())

def _ws_cor_nome(c):
    return "BRANCO" if c == 0 else "VERMELHO" if c == 1 else "PRETO" if c == 2 else "DESCONHECIDO"

def _contagem_rodadas_json():
    try:
        return len(load_stats().get("historico_resultados", []))
    except Exception:
        return 0

def _pode_disparar_alarme():
    try:
        with _ws_lock:
            qtd_ws = len(_ws_cores)
        qtd_json = _contagem_rodadas_json()
        
        # O alarme será disparado se tivermos no mínimo 100 rodadas (via WebSocket ou API)
        return max(qtd_ws, qtd_json) >= MIN_RODADAS_PARA_ALARME
    except Exception:
        return False

def _ws_parse_horario(iso):
    if not iso:
        return datetime.now().strftime("%H:%M:%S")
    for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return (datetime.strptime(iso, fmt) - timedelta(hours=3)).strftime("%H:%M:%S")
        except Exception:
            continue
    return datetime.now().strftime("%H:%M:%S")

# ======== 5) IO EXTERNO: API, TELEGRAM, EXCEL ================================
def boot_inicial():
    # Se o histórico do JSON não tem o mínimo de rodadas, baixa da API e preenche
    if _contagem_rodadas_json() < MIN_RODADAS_PARA_ALARME:
        print(f"[BOOT] Histórico com menos de {MIN_RODADAS_PARA_ALARME} jogadas. Buscando da API...")
        ok = preencher_json_diario_minimo_api(minimo=MIN_RODADAS_PARA_ALARME)  # Preenche com rodadas suficientes
        print(f"[BOOT] preencher_json_inicial_da_api -> {ok}")
    
    # Sempre reconstruir os buffers do WS a partir do JSON (após preencher a API, se necessário)
    reconstruir_ws_buffers_de_json(100)
    
    # Iniciar o WebSocket para pegar os dados ao vivo
    iniciar_websocket_fastlane()

def _api_buscar_historico(n=100, timeout=(4, 8)):
    """Busca até n registros mais recentes via API. Retorna lista normalizada."""    
    for size in (n, max(150, n), 120, 100, 80):
        try:
            j = requests.get(f"{API_HISTORY_URL}/1", timeout=timeout).json()
            recs = j.get("records") or []
            norm = []
            for r0 in recs:
                cor = r0.get("color"); created = r0.get("created_at")
                numero = (r0.get("roll") or r0.get("number") or r0.get("roll_number")
                          or r0.get("result") or r0.get("value") or r0.get("rolledNumber")
                          or r0.get("winning_number"))
                rid = r0.get("id")
                if cor in (0,1,2) and numero is not None and (created or rid):
                    norm.append({"color": cor, "created_at": created, "numero": numero, "id": rid})
            if norm:
                norm.sort(key=lambda x: (x["created_at"] or ""))  # antigo -> novo
                return norm[-n:]
        except Exception as e:
            print("[API] tentativa historico falhou:", e)
    return []

def enviar_mensagem_telegram(mensagem, alarme_tipo, horario):
    # Enviar mensagem via Telegram
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        r = requests.post(url, data={"chat_id": CHAT_ID, "text": mensagem})
        if r.status_code == 200:
            print(f"[TG] Mensagem enviada com sucesso.")
            
            # Atualiza o contador de alertas no JSON
            stats = load_stats()  # Carrega as estatísticas atuais
            
            # Incrementa o contador de alertas
            stats['contador_alertas'] += 1  # Incrementa o contador de alertas
            
            # Adiciona a nova sequência ao histórico de alertas
            stats.setdefault("sequencias_alertadas", []).insert(0, f"{alarme_tipo} - {horario}")
            
            # Salva as alterações no JSON
            save_stats(stats)  # Chama a função para salvar as estatísticas

        else:
            print(f"[TG] Erro ao enviar a mensagem: {r.text}")
    except Exception as e:
        print(f"[TG] Erro ao enviar a mensagem: {e}")

def enviar_alerta(mensagem): enviar_mensagem_telegram(mensagem)

def salvar_em_excel():
    try:
        if not os.path.exists(ARQUIVO_JSON):
            print("[✘] JSON não encontrado.")  # Adicione este log
            return
        stats = load_stats()
        
        # Verificando o nome do arquivo gerado
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", "historico diario percentuais",
                                    f"historico_completo_{date.today()}.xlsx")
        
        # Log para verificar o processo
        print(f"[INFO] Gerando o arquivo Excel em: {desktop_path}")  # Adicione este log
        
        # Criar lista com os dados para exportação
        historico_para_planilha = []
        total = len(stats['historico_resultados'])

        # Verificando o tamanho das listas antes de acessar
        if len(stats['historico_horarios']) < total:
            total = len(stats['historico_horarios'])
        if len(stats['historico_entradas']) < total:
            total = len(stats['historico_entradas'])
        if len(stats['historico_resultados_binarios']) < total:
            total = len(stats['historico_resultados_binarios'])
        if len(stats['historico_probabilidade_100']) < total:
            total = len(stats['historico_probabilidade_100'])
        if len(stats['historico_probabilidade_50']) < total:
            total = len(stats['historico_probabilidade_50'])
        if len(stats['historico_ciclos_preto_100']) < total:
            total = len(stats['historico_ciclos_preto_100'])
        if len(stats['historico_ciclos_vermelho_100']) < total:
            total = len(stats['historico_ciclos_vermelho_100'])
        if len(stats['historico_ciclos_preto_50']) < total:
            total = len(stats['historico_ciclos_preto_50'])
        if len(stats['historico_ciclos_vermelho_50']) < total:
            total = len(stats['historico_ciclos_vermelho_50'])

        # Adiciona os dados do histórico
        for i in range(1, total):
            historico_para_planilha.append({
                "Horário": stats['historico_horarios'][i-1] if i-1 < len(stats['historico_horarios']) else "-",
                "Previsão": stats['historico_entradas'][i],
                "Resultado": stats['historico_resultados'][i-1] if i-1 < len(stats['historico_resultados']) else "-",
                "Acertou": "Sim" if stats['historico_resultados_binarios'][i-1] is True
                           else "Não" if stats['historico_resultados_binarios'][i-1] is False else "N/D",
                "Probabilidade 100": stats['historico_probabilidade_100'][i-1] if i-1 < len(stats['historico_probabilidade_100']) else "-",
                "Probabilidade 50":  stats['historico_probabilidade_50'][i-1] if i-1 < len(stats['historico_probabilidade_50']) else "-",
                "Ciclos Preto 100":  stats['historico_ciclos_preto_100'][i-1] if i-1 < len(stats['historico_ciclos_preto_100']) else 0,
                "Ciclos Vermelho 100": stats['historico_ciclos_vermelho_100'][i-1] if i-1 < len(stats['historico_ciclos_vermelho_100']) else 0,
                "Ciclos Preto 50":   stats['historico_ciclos_preto_50'][i-1] if i-1 < len(stats['historico_ciclos_preto_50']) else 0,
                "Ciclos Vermelho 50": stats['historico_ciclos_vermelho_50'][i-1] if i-1 < len(stats['historico_ciclos_vermelho_50']) else 0,
            })
        
        # Verificando se há dados antes de salvar
        if not historico_para_planilha:
            print("[✘] Nenhum dado encontrado para salvar.")  # Adicione este log
            return

        # Salvando o arquivo Excel no desktop (ou outro diretório desejado)
        os.makedirs(os.path.dirname(desktop_path), exist_ok=True)
        df = pd.DataFrame(historico_para_planilha)
        df.to_excel(desktop_path, index=False)
        print(f"[✓] Planilha salva: {desktop_path}")
    except Exception as e:
        print(f"[✘] Falha ao salvar planilha: {e}")  # Log de erro detalhado


def iniciar_salvamento_automatico(intervalo_em_segundos=600):
    def loop():
        while True:
            salvar_em_excel()
            time.sleep(intervalo_em_segundos)
    threading.Thread(target=loop, daemon=True).start()

# ======== 6) LÓGICA: CÁLCULO E ESTRATÉGIAS ===================================
def calcular_estatisticas(cores, limite):
    arr = list(cores)
    filtrado = [c for c in arr[:limite] if c != 0]
    contagem = Counter(filtrado); total = len(filtrado)
    if total == 0:
        return "PRETO", 0.0, 0, 0
    preto = vermelho = 0
    atual = filtrado[0]
    for cor in filtrado[1:]:
        if cor != atual:
            if atual == 1: vermelho += 1
            if atual == 2: preto += 1
            atual = cor
    if atual == 1: vermelho += 1
    if atual == 2: preto += 1
    entrada = "PRETO" if preto >= vermelho else "VERMELHO"
    entrada_valor = 2 if entrada == "PRETO" else 1
    probabilidade = round((contagem[entrada_valor] / total) * 100, 2)
    return entrada, probabilidade, preto, vermelho


def verificar_estrategia_combinada(prob100, prob50, ultima_cor, previsao_anterior=None,
                                   status100=None, status50=None, horario=None, entrada100=None, entrada50=None):
    global ciclos100_vermelhos, ciclos100_preto, sequencia_alerta_ativa, estrategia_disparada, ciclos50_preto, ciclos50_vermelhos  # Incluindo a variável para controlar a sequência

    # Atualiza os ciclos de acordo com os últimos resultados
    entrada100, prob100, preto100, vermelho100 = calcular_estatisticas(_ws_cores, 100)
    entrada50,  prob50,  preto50,  vermelho50  = calcular_estatisticas(_ws_cores, 50)
    ciclos100_vermelhos = vermelho100
    ciclos100_preto = preto100
    ciclos50_vermelhos = vermelho50
    ciclos50_preto = preto50

    prob100_str = f"{prob100:.2f}"
    prob50_str = f"{prob50:.2f}"
    if not horario:
        horario = datetime.now().strftime("%H:%M:%S")

    msg = f"🔔 Alerta acionado! 🔔\n"

    # Dicionário para associar cores a emojis
    cor_emoji = {"Vermelho": "🔴", "Preto": "⚫", "Branco": "⚪"}

    alarme_tipo = None  # Tipo de alarme a ser disparado
    previsao_cor = None  # Cor da previsão

    # Condições para acionar os alarmes de acordo com as probabilidades
    if (prob100_str, prob50_str) in ALARM_PROB100_PROB50:
        alarme_tipo = "⚪️ BRANCO"
        previsao_cor = "Branco"
    elif (prob100_str, prob50_str) in ALARM_PROB100:  # Verifica apenas prob100 e prob50 em ALARM_PROB100
        alarme_tipo = "⚫️ PRETO"
        previsao_cor = "Preto"
    elif (prob100_str, prob50_str) in ALARM_PROB50:  # Verifica apenas prob100 e prob50 em ALARM_PROB50
        alarme_tipo = "🔴 VERMELHO"
        previsao_cor = "Vermelho"
    else:
        alarme_tipo = None  # Nenhum alarme disparado

    # Se houver previsão, inclui a mensagem
    if previsao_cor:
        msg += f"🎯 Previsão: {cor_emoji.get(previsao_cor.capitalize(), '❓')} {previsao_cor}\n"

    # Infos adicionais do alarme
    msg += f"🕒 Hora da jogada: {horario}\n"
    msg += f"⚫ Ciclos Preto 100: {ciclos100_preto}\n"
    msg += f"🔴 Ciclos Vermelho 100: {ciclos100_vermelhos}\n"
    msg += f"⚫ Ciclos Preto 50: {ciclos50_preto}\n"
    msg += f"🔴 Ciclos Vermelho 50: {ciclos50_vermelhos}\n"

    # Jogada atual
    if len(_ws_cores) > 0 and len(_ws_numeros) > 0:  # Certifique-se de que há pelo menos uma jogada
        cor_atual = _ws_cor_nome(_ws_cores[0])  # Cor da jogada atual (primeiro no buffer)
        numero_atual = _ws_numeros[0]  # Número da jogada atual
        msg += f"📊 Jogada atual Cor: {cor_atual} | Número: {numero_atual}\n"
    else:
        msg += "📊 Jogada atual: Não disponível.\n"  # Caso não haja jogada atual

    # Jogada anterior
    if len(_ws_cores) > 1 and len(_ws_numeros) > 1:  # Certifique-se de que há pelo menos duas jogadas
        ultima_cor_anterior = _ws_cor_nome(_ws_cores[1])  # A jogada anterior é a segunda no buffer
        ultimo_numero_anterior = _ws_numeros[1]
        msg += f"📊 Jogada anterior Cor: {ultima_cor_anterior} | Número: {ultimo_numero_anterior}\n"
        # Comparação dos ciclos
        comparacao_preto100_vermelho100 = ""
        comparacao_preto50_vermelho50 = ""

        if preto100 > vermelho100:
            comparacao_preto100_vermelho100 = "MAIOR 🔺"
        elif preto100 < vermelho100:
            comparacao_preto100_vermelho100 = "MENOR 🔻"
        else:
            comparacao_preto100_vermelho100 = "IGUAL 🔄"

        if preto50 > vermelho50:
            comparacao_preto50_vermelho50 = "MAIOR 🔺"
        elif preto50 < vermelho50:
            comparacao_preto50_vermelho50 = "MENOR 🔻"
        else:
            comparacao_preto50_vermelho50 = "IGUAL 🔄"
            # Resumo da comparação
        msg += f"📊 Comparação Ciclos 100: {comparacao_preto100_vermelho100}\n"
        msg += f"📊 Comparação Ciclos 50: {comparacao_preto50_vermelho50}\n"

        # Verificando se as cores são iguais ou diferentes
        if cor_atual == ultima_cor_anterior:
            msg += "🎨 As cores da jogada atual e anterior são IGUAIS SIM! ✔️\n"
        else:
            msg += "🎨 As cores da jogada atual e anterior são IGUAIS NÃO! ❌\n"
    else:
        msg += "📊 Jogada anterior: Não disponível.\n"  # Caso não haja jogada anterior


    # Checando o padrão de cor e ciclos
    padrao_encontrado = False

    # Verifica se o padrão de comparação é válido
    if previsao_cor == "Branco":
        if comparacao_preto100_vermelho100 == "MENOR 🔻" and comparacao_preto50_vermelho50 == "MENOR 🔻" and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif comparacao_preto100_vermelho100 == "MAIOR 🔺" and comparacao_preto50_vermelho50 == "MAIOR 🔺" and cor_atual == ultima_cor_anterior:
            padrao_encontrado = True

    # Previsão: Preto, Cor Atual: Preto
    elif previsao_cor == "Preto" and cor_atual == "PRETO":
        if ciclos100_preto == 27 and ciclos100_vermelhos == 26 and ciclos50_preto == 15 and ciclos50_vermelhos == 14 and cor_atual == ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 25 and ciclos100_vermelhos == 26 and ciclos50_preto == 13 and ciclos50_vermelhos == 13 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 24 and ciclos100_vermelhos == 25 and ciclos50_preto == 13 and ciclos50_vermelhos == 14 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 24 and ciclos100_vermelhos == 25 and ciclos50_preto == 11 and ciclos50_vermelhos == 12 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 24 and ciclos100_vermelhos == 24 and ciclos50_preto == 12 and ciclos50_vermelhos == 11 and cor_atual == ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 24 and ciclos100_vermelhos == 24 and ciclos50_preto == 10 and ciclos50_vermelhos == 10 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 24 and ciclos100_vermelhos == 23 and ciclos50_preto == 12 and ciclos50_vermelhos == 12 and cor_atual == ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 24 and ciclos100_vermelhos == 23 and ciclos50_preto == 11 and ciclos50_vermelhos == 10 and cor_atual == ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 23 and ciclos100_vermelhos == 23 and ciclos50_preto == 13 and ciclos50_vermelhos == 14 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 23 and ciclos100_vermelhos == 23 and ciclos50_preto == 13 and ciclos50_vermelhos == 13 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 23 and ciclos100_vermelhos == 23 and ciclos50_preto == 12 and ciclos50_vermelhos == 12 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 23 and ciclos100_vermelhos == 23 and ciclos50_preto == 11 and ciclos50_vermelhos == 11 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 23 and ciclos100_vermelhos == 23 and ciclos50_preto == 11 and ciclos50_vermelhos == 11 and cor_atual == ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 23 and ciclos100_vermelhos == 23 and ciclos50_preto == 10 and ciclos50_vermelhos == 11 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 23 and ciclos100_vermelhos == 22 and ciclos50_preto == 13 and ciclos50_vermelhos == 12 and cor_atual == ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 22 and ciclos100_vermelhos == 23 and ciclos50_preto == 11 and ciclos50_vermelhos == 11 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 22 and ciclos100_vermelhos == 23 and ciclos50_preto == 10 and ciclos50_vermelhos == 10 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 22 and ciclos100_vermelhos == 22 and ciclos50_preto == 12 and ciclos50_vermelhos == 12 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 22 and ciclos100_vermelhos == 22 and ciclos50_preto == 11 and ciclos50_vermelhos == 12 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 22 and ciclos100_vermelhos == 22 and ciclos50_preto == 11 and ciclos50_vermelhos == 11 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 22 and ciclos100_vermelhos == 22 and ciclos50_preto == 11 and ciclos50_vermelhos == 10 and cor_atual == ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 22 and ciclos100_vermelhos == 22 and ciclos50_preto == 10 and ciclos50_vermelhos == 9 and cor_atual == ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 22 and ciclos100_vermelhos == 21 and ciclos50_preto == 12 and ciclos50_vermelhos == 11 and cor_atual == ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 21 and ciclos100_vermelhos == 21 and ciclos50_preto == 12 and ciclos50_vermelhos == 11 and cor_atual == ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 21 and ciclos100_vermelhos == 21 and ciclos50_preto == 10 and ciclos50_vermelhos == 11 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 21 and ciclos100_vermelhos == 21 and ciclos50_preto == 10 and ciclos50_vermelhos == 10 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 20 and ciclos100_vermelhos == 21 and ciclos50_preto == 10 and ciclos50_vermelhos == 11 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True

    # Previsão: Preto, Cor Atual: Vermelho
    elif previsao_cor == "Preto" and cor_atual == "VERMELHO":
        if ciclos100_preto == 26 and ciclos100_vermelhos == 25 and ciclos50_preto == 14 and ciclos50_vermelhos == 14 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 25 and ciclos100_vermelhos == 26 and ciclos50_preto == 13 and ciclos50_vermelhos == 14 and cor_atual == ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 25 and ciclos100_vermelhos == 25 and ciclos50_preto == 14 and ciclos50_vermelhos == 14 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 25 and ciclos100_vermelhos == 25 and ciclos50_preto == 14 and ciclos50_vermelhos == 13 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 25 and ciclos100_vermelhos == 25 and ciclos50_preto == 13 and ciclos50_vermelhos == 13 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 25 and ciclos100_vermelhos == 25 and ciclos50_preto == 12 and ciclos50_vermelhos == 11 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 25 and ciclos100_vermelhos == 24 and ciclos50_preto == 14 and ciclos50_vermelhos == 13 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 25 and ciclos100_vermelhos == 24 and ciclos50_preto == 13 and ciclos50_vermelhos == 13 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 25 and ciclos100_vermelhos == 24 and ciclos50_preto == 13 and ciclos50_vermelhos == 12 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 24 and ciclos100_vermelhos == 25 and ciclos50_preto == 12 and ciclos50_vermelhos == 13 and cor_atual == ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 24 and ciclos100_vermelhos == 25 and ciclos50_preto == 10 and ciclos50_vermelhos == 11 and cor_atual == ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 24 and ciclos100_vermelhos == 24 and ciclos50_preto == 13 and ciclos50_vermelhos == 13 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 24 and ciclos100_vermelhos == 24 and ciclos50_preto == 12 and ciclos50_vermelhos == 12 and cor_atual == ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 24 and ciclos100_vermelhos == 24 and ciclos50_preto == 11 and ciclos50_vermelhos == 12 and cor_atual == ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 24 and ciclos100_vermelhos == 24 and ciclos50_preto == 11 and ciclos50_vermelhos == 11 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 24 and ciclos100_vermelhos == 24 and ciclos50_preto == 11 and ciclos50_vermelhos == 11 and cor_atual == ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 24 and ciclos100_vermelhos == 23 and ciclos50_preto == 12 and ciclos50_vermelhos == 12 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 24 and ciclos100_vermelhos == 23 and ciclos50_preto == 11 and ciclos50_vermelhos == 11 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 23 and ciclos100_vermelhos == 24 and ciclos50_preto == 13 and ciclos50_vermelhos == 13 and cor_atual == ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 23 and ciclos100_vermelhos == 24 and ciclos50_preto == 11 and ciclos50_vermelhos == 12 and cor_atual == ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 23 and ciclos100_vermelhos == 23 and ciclos50_preto == 13 and ciclos50_vermelhos == 13 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 23 and ciclos100_vermelhos == 23 and ciclos50_preto == 12 and ciclos50_vermelhos == 11 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 23 and ciclos100_vermelhos == 23 and ciclos50_preto == 11 and ciclos50_vermelhos == 12 and cor_atual == ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 23 and ciclos100_vermelhos == 22 and ciclos50_preto == 13 and ciclos50_vermelhos == 12 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 23 and ciclos100_vermelhos == 22 and ciclos50_preto == 12 and ciclos50_vermelhos == 11 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 23 and ciclos100_vermelhos == 22 and ciclos50_preto == 10 and ciclos50_vermelhos == 10 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 22 and ciclos100_vermelhos == 22 and ciclos50_preto == 12 and ciclos50_vermelhos == 12 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 22 and ciclos100_vermelhos == 22 and ciclos50_preto == 11 and ciclos50_vermelhos == 11 and cor_atual == ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 22 and ciclos100_vermelhos == 22 and ciclos50_preto == 11 and ciclos50_vermelhos == 10 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 22 and ciclos100_vermelhos == 22 and ciclos50_preto == 10 and ciclos50_vermelhos == 11 and cor_atual == ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 21 and ciclos100_vermelhos == 22 and ciclos50_preto == 10 and ciclos50_vermelhos == 11 and cor_atual == ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 21 and ciclos100_vermelhos == 21 and ciclos50_preto == 13 and ciclos50_vermelhos == 12 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 21 and ciclos100_vermelhos == 21 and ciclos50_preto == 11 and ciclos50_vermelhos == 11 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 21 and ciclos100_vermelhos == 20 and ciclos50_preto == 11 and ciclos50_vermelhos == 11 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True

    # Previsão: Vermelho, Cor Atual: Vermelho
    elif previsao_cor == "Vermelho" and cor_atual == "VERMELHO":
        if ciclos100_preto == 26 and ciclos100_vermelhos == 26 and ciclos50_preto == 13 and ciclos50_vermelhos == 13 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 26 and ciclos100_vermelhos == 25 and ciclos50_preto == 13 and ciclos50_vermelhos == 12 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 25 and ciclos100_vermelhos == 25 and ciclos50_preto == 13 and ciclos50_vermelhos == 12 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 25 and ciclos100_vermelhos == 25 and ciclos50_preto == 12 and ciclos50_vermelhos == 13 and cor_atual == ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 25 and ciclos100_vermelhos == 25 and ciclos50_preto == 12 and ciclos50_vermelhos == 12 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 25 and ciclos100_vermelhos == 24 and ciclos50_preto == 13 and ciclos50_vermelhos == 13 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 24 and ciclos100_vermelhos == 25 and ciclos50_preto == 12 and ciclos50_vermelhos == 12 and cor_atual == ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 24 and ciclos100_vermelhos == 24 and ciclos50_preto == 13 and ciclos50_vermelhos == 12 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 24 and ciclos100_vermelhos == 24 and ciclos50_preto == 12 and ciclos50_vermelhos == 12 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 24 and ciclos100_vermelhos == 23 and ciclos50_preto == 12 and ciclos50_vermelhos == 12 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 24 and ciclos100_vermelhos == 23 and ciclos50_preto == 10 and ciclos50_vermelhos == 10 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 23 and ciclos100_vermelhos == 23 and ciclos50_preto == 13 and ciclos50_vermelhos == 13 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 23 and ciclos100_vermelhos == 23 and ciclos50_preto == 11 and ciclos50_vermelhos == 10 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 23 and ciclos100_vermelhos == 23 and ciclos50_preto == 10 and ciclos50_vermelhos == 10 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 22 and ciclos100_vermelhos == 23 and ciclos50_preto == 11 and ciclos50_vermelhos == 11 and cor_atual == ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 22 and ciclos100_vermelhos == 23 and ciclos50_preto == 10 and ciclos50_vermelhos == 11 and cor_atual == ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 22 and ciclos100_vermelhos == 22 and ciclos50_preto == 13 and ciclos50_vermelhos == 12 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 22 and ciclos100_vermelhos == 22 and ciclos50_preto == 12 and ciclos50_vermelhos == 12 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 22 and ciclos100_vermelhos == 22 and ciclos50_preto == 11 and ciclos50_vermelhos == 12 and cor_atual == ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 22 and ciclos100_vermelhos == 22 and ciclos50_preto == 11 and ciclos50_vermelhos == 11 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 22 and ciclos100_vermelhos == 22 and ciclos50_preto == 10 and ciclos50_vermelhos == 11 and cor_atual == ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 22 and ciclos100_vermelhos == 22 and ciclos50_preto == 10 and ciclos50_vermelhos == 10 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 22 and ciclos100_vermelhos == 22 and ciclos50_preto == 10 and ciclos50_vermelhos == 10 and cor_atual == ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 22 and ciclos100_vermelhos == 21 and ciclos50_preto == 10 and ciclos50_vermelhos == 10 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 21 and ciclos100_vermelhos == 22 and ciclos50_preto == 11 and ciclos50_vermelhos == 12 and cor_atual == ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 21 and ciclos100_vermelhos == 21 and ciclos50_preto == 12 and ciclos50_vermelhos == 12 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 21 and ciclos100_vermelhos == 21 and ciclos50_preto == 12 and ciclos50_vermelhos == 12 and cor_atual == ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 21 and ciclos100_vermelhos == 21 and ciclos50_preto == 11 and ciclos50_vermelhos == 11 and cor_atual == ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 21 and ciclos100_vermelhos == 21 and ciclos50_preto == 10 and ciclos50_vermelhos == 11 and cor_atual == ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 21 and ciclos100_vermelhos == 21 and ciclos50_preto == 10 and ciclos50_vermelhos == 9 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 21 and ciclos100_vermelhos == 21 and ciclos50_preto == 9 and ciclos50_vermelhos == 10 and cor_atual == ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 20 and ciclos100_vermelhos == 19 and ciclos50_preto == 10 and ciclos50_vermelhos == 9 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 19 and ciclos100_vermelhos == 20 and ciclos50_preto == 8 and ciclos50_vermelhos == 9 and cor_atual == ultima_cor_anterior:
            padrao_encontrado = True

    # Previsão: Vermelho, Cor Atual: Preto
    elif previsao_cor == "Vermelho" and cor_atual == "PRETO":
        if ciclos100_preto == 25 and ciclos100_vermelhos == 25 and ciclos50_preto == 12 and ciclos50_vermelhos == 12 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 25 and ciclos100_vermelhos == 24 and ciclos50_preto == 13 and ciclos50_vermelhos == 13 and cor_atual == ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 24 and ciclos100_vermelhos == 25 and ciclos50_preto == 13 and ciclos50_vermelhos == 13 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 24 and ciclos100_vermelhos == 25 and ciclos50_preto == 11 and ciclos50_vermelhos == 11 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 24 and ciclos100_vermelhos == 25 and ciclos50_preto == 10 and ciclos50_vermelhos == 11 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 24 and ciclos100_vermelhos == 24 and ciclos50_preto == 14 and ciclos50_vermelhos == 13 and cor_atual == ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 24 and ciclos100_vermelhos == 24 and ciclos50_preto == 12 and ciclos50_vermelhos == 13 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 24 and ciclos100_vermelhos == 24 and ciclos50_preto == 12 and ciclos50_vermelhos == 12 and cor_atual == ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 24 and ciclos100_vermelhos == 24 and ciclos50_preto == 11 and ciclos50_vermelhos == 11 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 24 and ciclos100_vermelhos == 23 and ciclos50_preto == 13 and ciclos50_vermelhos == 13 and cor_atual == ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 24 and ciclos100_vermelhos == 23 and ciclos50_preto == 13 and ciclos50_vermelhos == 12 and cor_atual == ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 24 and ciclos100_vermelhos == 23 and ciclos50_preto == 12 and ciclos50_vermelhos == 11 and cor_atual == ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 23 and ciclos100_vermelhos == 24 and ciclos50_preto == 12 and ciclos50_vermelhos == 12 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 23 and ciclos100_vermelhos == 24 and ciclos50_preto == 11 and ciclos50_vermelhos == 12 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 23 and ciclos100_vermelhos == 23 and ciclos50_preto == 13 and ciclos50_vermelhos == 12 and cor_atual == ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 23 and ciclos100_vermelhos == 23 and ciclos50_preto == 12 and ciclos50_vermelhos == 12 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 23 and ciclos100_vermelhos == 22 and ciclos50_preto == 12 and ciclos50_vermelhos == 11 and cor_atual == ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 23 and ciclos100_vermelhos == 22 and ciclos50_preto == 10 and ciclos50_vermelhos == 10 and cor_atual == ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 22 and ciclos100_vermelhos == 23 and ciclos50_preto == 11 and ciclos50_vermelhos == 12 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 22 and ciclos100_vermelhos == 23 and ciclos50_preto == 10 and ciclos50_vermelhos == 11 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 22 and ciclos100_vermelhos == 22 and ciclos50_preto == 12 and ciclos50_vermelhos == 12 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 22 and ciclos100_vermelhos == 22 and ciclos50_preto == 11 and ciclos50_vermelhos == 11 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 22 and ciclos100_vermelhos == 22 and ciclos50_preto == 10 and ciclos50_vermelhos == 11 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 22 and ciclos100_vermelhos == 21 and ciclos50_preto == 12 and ciclos50_vermelhos == 11 and cor_atual == ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 21 and ciclos100_vermelhos == 22 and ciclos50_preto == 12 and ciclos50_vermelhos == 12 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 21 and ciclos100_vermelhos == 21 and ciclos50_preto == 12 and ciclos50_vermelhos == 12 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 21 and ciclos100_vermelhos == 21 and ciclos50_preto == 11 and ciclos50_vermelhos == 11 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 21 and ciclos100_vermelhos == 21 and ciclos50_preto == 9 and ciclos50_vermelhos == 9 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 21 and ciclos100_vermelhos == 20 and ciclos50_preto == 10 and ciclos50_vermelhos == 10 and cor_atual == ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 21 and ciclos100_vermelhos == 20 and ciclos50_preto == 10 and ciclos50_vermelhos == 9 and cor_atual == ultima_cor_anterior:
            padrao_encontrado = True
        elif ciclos100_preto == 20 and ciclos100_vermelhos == 20 and ciclos50_preto == 9 and ciclos50_vermelhos == 9 and cor_atual != ultima_cor_anterior:
            padrao_encontrado = True
   

    # Enviar mensagem adicional caso o padrão seja encontrado
    if padrao_encontrado:
        msg += "✅ Padrão encontrado! A estratégia está assertiva para a previsão.\n"

    # Função interna para verificar as probabilidades
    def verificar_probabilidades(prob100, prob50):
        """Verifica as probabilidades e retorna uma mensagem de alarme e o tipo de mensagem.""" 
        if prob100 > 50 and prob50 > 50:
            return f"✔️ Ambas as probabilidades são MAIORES que 50!\n", "Ambas maiores"
        elif prob100 < 50 and prob50 < 50:
            return f"✅ Ambas as probabilidades são MENORES que 50!\n", "Ambas menores"
        elif prob100 > 50 and prob50 <= 50:
            return f"⚠️ Prob100 é MAIOR que 50, mas Prob50 NÃO é!\n", "Prob100 maior"
        elif prob50 > 50 and prob100 <= 50:
            return f"⚠️ Prob50 é MAIOR que 50, mas Prob100 NÃO é!\n", "Prob50 maior"
        else:
            return None, None  # Caso não se encaixe em nenhuma das opções acima

    # Verifica as probabilidades e gera a mensagem de alarme
    mensagem, tipo_mensagem = verificar_probabilidades(prob100, prob50)

    # Envia a mensagem e atualiza o contador de alarmes
    if alarme_tipo and mensagem:
        # Envia a mensagem para o Telegram
        enviar_mensagem_telegram(msg + f"Probabilidade 100: {prob100_str}% | Probabilidade 50: {prob50_str}%", alarme_tipo, horario)
        # Atualiza a estratégia e marca como disparada
        estrategia_disparada = True  # Ativa a variável para indicar que a estratégia foi disparada
        # Incrementa o contador de alertas
        stats = load_stats()  # Carrega as estatísticas atuais
        stats['contador_alertas'] += 1  # Incrementa o contador de alertas
        save_stats(stats)  # Salva as alterações no JSON

    return None, None

# ======== 7) WSS: PARSE, HANDLERS E PIPELINE =================================
def _ws_find(obj, keys):
    if isinstance(obj, dict):
        for k in keys:
            if k in obj and obj[k] is not None: return obj[k]
        for v in obj.values():
            r = _ws_find(v, keys)
            if r is not None: return r
    elif isinstance(obj, list):
        for it in obj:
            r = _ws_find(it, keys)
            if r is not None: return r
    return None

def _ws_try_extract_full(body):
    if not isinstance(body, dict): return None, None, None, None
    cor        = _ws_find(body, ("color","colour","cor"))
    created_at = _ws_find(body, ("created_at","createdAt","time","timestamp"))
    numero     = _ws_find(body, ("roll","number","value","result","roll_number","rolledNumber","winning_number"))
    round_id   = None
    payload = body.get("payload", body)
    if isinstance(payload, dict):
        rid = payload.get("id")
        if isinstance(rid, str) and not rid.startswith("double."):
            round_id = rid
    return cor, created_at, numero, round_id

# Se for uma execução inicial, passe bootstrap=True
def processar_resultado_ws_fast(cor, created_at_iso=None, numero=None, round_id=None, bootstrap=False):
    """Atualiza buffers/estatísticas e persiste no JSON; controla alarmes com janela mínima."""
    global _ws_last_uid, _printed_uid
    if numero is None: return

    entrada100 = entrada50 = None
    prob100 = prob50 = None
    horario = None
    estrategia_disparada = None
    alarme_tipo = None  # Tipo de alarme acionado

    with _ws_lock:
        uid = created_at_iso or round_id
        if not uid: return

        if _printed_uid != uid:
            print(f"{_ws_parse_horario(created_at_iso)} -> {_ws_cor_nome(cor)} ({numero})", flush=True)
            _printed_uid = uid
        if _ws_last_uid == uid: return
        _ws_last_uid = uid

        horario = _ws_parse_horario(created_at_iso)
        _ws_cores.appendleft(cor)
        _ws_horarios.appendleft(horario)
        try: _ws_numeros.appendleft(int(numero))
        except: pass

        entrada100, prob100, preto100, vermelho100 = calcular_estatisticas(_ws_cores, 100)
        entrada50,  prob50,  preto50,  vermelho50  = calcular_estatisticas(_ws_cores, 50)
        janela_ok = _pode_disparar_alarme()

        stats = load_stats()  # Carrega as estatísticas atuais
        previsao_anterior = stats['historico_entradas'][0] if stats.get('historico_entradas') else None

        if (not bootstrap) and janela_ok:
            status100 = (preto100 < vermelho100)
            status50  = (preto50  < vermelho50)
            estrategia_disparada, alarme_tipo = verificar_estrategia_combinada(
                previsao_anterior=previsao_anterior, ultima_cor=cor,
                status100=status100, status50=status50,
                prob100=prob100, prob50=prob50, entrada100=entrada100, horario=horario
            )

        if uid != stats.get('ultima_uid_ws'):
            resultado_binario = None
            if previsao_anterior is not None:
                cor_prevista = 2 if previsao_anterior == "PRETO" else 1
                if cor == cor_prevista or cor == 0:
                    resultado_binario = True
                    stats['acertos'] += 1
                else:
                    resultado_binario = False
                    stats['erros'] += 1

            ultima_nome = _ws_cor_nome(cor)
            stats['historico_entradas'].insert(0, entrada100)
            stats['historico_resultados'].insert(0, ultima_nome)
            stats['historico_horarios'].insert(0, horario)
            stats['historico_resultados_binarios'].insert(0, resultado_binario)
            stats['historico_probabilidade_100'].insert(0, prob100)
            stats['historico_probabilidade_50'].insert(0, prob50)
            stats['historico_ciclos_preto_100'].insert(0, preto100)
            stats['historico_ciclos_vermelho_100'].insert(0, vermelho100)
            stats['historico_ciclos_preto_50'].insert(0, preto50)
            stats['historico_ciclos_vermelho_50'].insert(0, vermelho50)

            if created_at_iso: stats['ultima_analisada'] = created_at_iso
            stats['ultima_uid_ws'] = uid

            if estrategia_disparada:
                stats['contador_alertas'] += 1  # Incrementa o contador de alertas
                stats['sequencia_ativa'] = True
                stats['estrategia_ativa'] = estrategia_disparada
                stats.setdefault("sequencias_alertadas", []).insert(0, f"{estrategia_disparada} - {horario}")

                if alarme_tipo:
                    if resultado_binario:
                        contador_acertos_alarm[alarme_tipo] += 1
                    else:
                        contador_erros_alarm[alarme_tipo] += 1
            else:
                stats['sequencia_ativa'] = False
                stats['estrategia_ativa'] = ""

            save_stats(stats)  # Chama a função para salvar as estatísticas

    count_atual = max(len(_ws_cores), len(load_stats().get('historico_resultados', [])))
    nome_estrategia = (f"Aguardando {MIN_RODADAS_PARA_ALARME} jogadas ({count_atual}/{MIN_RODADAS_PARA_ALARME})"
                       if not janela_ok else f"Prob100: {prob100} | Prob50: {prob50}")

    WS_RENDER_CACHE.update({
        "entrada": entrada100,
        "probabilidade100": prob100,
        "probabilidade50": prob50,
        "ciclos100_preto": preto100, "ciclos100_vermelho": vermelho100,
        "ciclos50_preto":  preto50,  "ciclos50_vermelho":  vermelho50,
        "ultima": _ws_cor_nome(cor),
        "horario": horario,
        "sequencia_detectada": (not bootstrap) and janela_ok and bool(estrategia_disparada),
        "nome_estrategia": nome_estrategia,
        "created_at": created_at_iso, "uid": uid, "ts": time.time()
    })

def _ws_iter_json_packets(msg: str):
    if isinstance(msg, (bytes, bytearray)):
        try: msg = msg.decode("utf-8", "ignore")
        except Exception: msg = str(msg)
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
        packets.append(msg[i:end]); i = msg.find('[', end)
    return packets

def _ws_on_open(ws):
    global _socketio_opened, _last_round_ts
    print("[WS] OPEN", flush=True)
    _socketio_opened = False; _last_round_ts = 0.0
    try: ws.send("40"); _socketio_opened = True
    except Exception as e: print("[WS] erro send 40:", e, flush=True)
    threading.Thread(target=_ws_engineio_ping_loop, args=(ws,), daemon=True).start()
    threading.Thread(target=_ws_watchdog, args=(ws,), daemon=True).start()
    _ws_subscribe(ws)

def _ws_subscribe(ws):
    global _room_idx
    room = ROOMS[_room_idx % len(ROOMS)]
    frame = f'42["cmd",{{"id":"subscribe","payload":{{"room":"{room}"}}}}]'
    try: ws.send(frame)
    except Exception:
        try: ws.send(f'423["cmd",{{"id":"subscribe","payload":{{"room":"{room}"}}}}]')
        except Exception: pass

def _ws_engineio_ping_loop(ws):
    while True:
        try:
            if not ws or not ws.sock or not ws.sock.connected: break
            ws.send("2")  # ping Engine.IO v3
        except Exception: break
        time.sleep(ENGINEIO_PING_EVERY)

def _ws_watchdog(ws):
    global _room_idx, _last_round_ts
    while True:
        time.sleep(10)
        if not ws or not ws.sock or not ws.sock.connected or not _socketio_opened: break
        if time.time() - _last_round_ts > 30:
            _room_idx = (_room_idx + 1) % len(ROOMS)
            _ws_subscribe(ws)

def _ws_on_message(ws, message: str):
    global _ultimo_uid, _last_round_ts, _socketio_opened
    try:
        if isinstance(message, (bytes, bytearray)):
            try: message = message.decode("utf-8", "ignore")
            except Exception: message = str(message)
        if message in ("2","3"): return
        if message == "0":
            try: ws.send("40"); _socketio_opened = True
            except Exception: pass
            return
        if message == "40":
            _socketio_opened = True; return

        for raw in _ws_iter_json_packets(message) or []:
            try: data = json.loads(raw)
            except Exception: continue
            if not (isinstance(data, list) and len(data) >= 2): continue
            body = data[1]
            cor, created_at, numero, round_id = _ws_try_extract_full(body)
            if cor not in (0,1,2) or numero is None: continue
            uid_local = created_at or round_id
            if not uid_local: continue

            processar_resultado_ws_fast(cor, created_at_iso=created_at, numero=numero, round_id=round_id)
            _last_round_ts = time.time()
            _ultimo_uid = uid_local
    except Exception as e:
        try: sample = (message if isinstance(message, str) else repr(message))[:200]
        except Exception: sample = "<unprintable>"
        print("[WS] on_message error:", e, "| sample:", sample, flush=True)

def _ws_on_error(ws, error): pass
def _ws_on_close(ws, code, msg): pass

def iniciar_websocket_fastlane():
    def _run():
        while True:
            try:
                ws = websocket.WebSocketApp(
                    WS_URL, on_open=_ws_on_open, on_message=_ws_on_message,
                    on_error=_ws_on_error, on_close=_ws_on_close
                )
                ws.run_forever(ping_interval=30, ping_timeout=10)
            except Exception:
                pass
            time.sleep(5)
    threading.Thread(target=_run, daemon=True).start()

# ======== 8) BOOTSTRAP + RENDER ==============================================
def bootstrap_inicial_de_api(n=100):
    try:
        registros = _api_buscar_historico(n)
        if not registros:
            print("[BOOT] Não foi possível obter histórico inicial via API."); return
        with _ws_lock:
            _ws_cores.clear(); _ws_horarios.clear(); _ws_numeros.clear()
        for r in registros:  # antigo -> novo
            processar_resultado_ws_fast(r["color"], created_at_iso=r.get("created_at"),
                                        numero=r.get("numero"), round_id=r.get("id"), bootstrap=True)
        print(f"[BOOT] Histórico inicial carregado: {len(registros)} rodadas.")
    except Exception as e:
        print("[BOOT] Erro no bootstrap inicial:", e)

def render_somente_cache():
    entrada = WS_RENDER_CACHE.get("entrada", "PRETO")
    prob100 = WS_RENDER_CACHE.get("probabilidade100", 0)
    prob50  = WS_RENDER_CACHE.get("probabilidade50", 0)
    ciclos100_preto     = WS_RENDER_CACHE.get("ciclos100_preto", 0)
    ciclos100_vermelho  = WS_RENDER_CACHE.get("ciclos100_vermelho", 0)
    ciclos50_preto      = WS_RENDER_CACHE.get("ciclos50_preto", 0)
    ciclos50_vermelho   = WS_RENDER_CACHE.get("ciclos50_vermelho", 0)
    ultima = WS_RENDER_CACHE.get("ultima", "-")
    horario = WS_RENDER_CACHE.get("horario", "-")

    stats = load_stats()  # Carrega o histórico completo (acumulado)
    ultimos_resultados_txt = stats.get('historico_resultados', [])[:10]
    map_class = {"PRETO":"preto","VERMELHO":"vermelho","BRANCO":"branco"}
    ultimas = [map_class.get(x.upper(),"preto") for x in ultimos_resultados_txt][::-1]
    ultimos_horarios = stats.get('historico_horarios', [])[:10][::-1]
    entradas_slice = stats.get('historico_entradas', [])[1:11]
    entradas = ["preto" if e == "PRETO" else "vermelho" for e in entradas_slice]
    resultados = stats.get('historico_resultados_binarios', [])[:len(entradas_slice)]

    historico_completo = []
    n = min(len(stats.get('historico_entradas', [])),
            len(stats.get('historico_resultados', [])) + 1,
            len(stats.get('historico_horarios', [])) + 1,
            len(stats.get('historico_resultados_binarios', [])) + 1)
    for i in range(1, n):
        historico_completo.append({
            "horario": stats['historico_horarios'][i-1] if i-1 < len(stats['historico_horarios']) else "-",
            "previsao": stats['historico_entradas'][i],
            "resultado": stats['historico_resultados'][i-1] if i-1 < len(stats['historico_resultados']) else "-",
            "icone": "✅" if stats['historico_resultados_binarios'][i-1] is True
                     else "❌" if stats['historico_resultados_binarios'][i-1] is False else "?",
        })

    acertos = stats.get('acertos', 0); erros = stats.get('erros', 0)
    total = acertos + erros
    taxa  = round((acertos/total)*100, 1) if total > 0 else 0

    return render_template_string(
        TEMPLATE,
        entrada=entrada, resultados=resultados,
        sequencia_atual=f"Prob100: {prob100} | Prob50: {prob50}",
        ciclos100_preto=ciclos100_preto, ciclos100_vermelho=ciclos100_vermelho,
        ciclos50_preto=ciclos50_preto,   ciclos50_vermelho=ciclos50_vermelho,
        ultima=ultima, probabilidade100=prob100, probabilidade50=prob50,
        ultimas=ultimas, ultimos_horarios=ultimos_horarios, horario=horario,
        acertos=acertos, erros=erros, taxa_acerto=taxa, entradas=entradas,
        historico_completo=historico_completo,
        contador_alertas=stats.get('contador_alertas', 0),
        sequencia_detectada=WS_RENDER_CACHE.get("sequencia_detectada", stats.get('sequencia_ativa', False)),
        nome_estrategia=WS_RENDER_CACHE.get("nome_estrategia", f"Prob100: {prob100} | Prob50: {prob50}")
    )

# ======== 9) FLASK ROUTE =====================================================
@app.route('/')
def index():
    try:
        # Se o WS tiver pouco dado, reconstruímos on-demand (evita prob=100% com 1 item)
        if len(_ws_cores) < 10 and _contagem_rodadas_json() >= 10:
            reconstruir_ws_buffers_de_json(100)

        # 1) Preferir WSS
        if len(_ws_cores) > 0:
            with _ws_lock:
                cores = list(_ws_cores); horarios = list(_ws_horarios)
                horarios = list(_ws_horarios)

            entrada100, prob100, preto100, vermelho100 = calcular_estatisticas(cores, 100)
            entrada50,  prob50,  preto50,  vermelho50  = calcular_estatisticas(cores, 50)
            ultima_nome = _ws_cor_nome(cores[0])
            horario = horarios[0]

            stats = load_stats()
            entradas_slice = stats['historico_entradas'][1:11]
            entradas   = ["preto" if e == "PRETO" else "vermelho" for e in entradas_slice]
            resultados = stats['historico_resultados_binarios'][:len(entradas_slice)]
            ultimas  = [("branco" if c == 0 else "vermelho" if c == 1 else "preto") for c in cores[:10][::-1]]
            ultimos_horarios = horarios[:10][::-1]

            historico_completo = []
            tam = min(len(stats['historico_entradas']),
                      len(stats['historico_resultados']),
                      len(stats['historico_horarios']),
                      len(stats['historico_resultados_binarios']))
            for i in range(1, tam):
                historico_completo.append({
                    "horario":   stats['historico_horarios'][i - 1],
                    "previsao":  stats['historico_entradas'][i],
                    "resultado": stats['historico_resultados'][i - 1],
                    "icone": "✅" if stats['historico_resultados_binarios'][i - 1] is True
                             else "❌" if stats['historico_resultados_binarios'][i - 1] is False else "?",
                })

            return render_template_string(
                TEMPLATE,
                entrada=entrada100,
                sequencia_atual=f"Prob100: {prob100} | Prob50: {prob50}",
                ciclos100_preto=preto100, ciclos100_vermelho=vermelho100,
                ciclos50_preto=preto50, ciclos50_vermelho=vermelho50,
                ultima=ultima_nome, probabilidade100=prob100, probabilidade50=prob50,
                ultimas=ultimas, ultimos_horarios=ultimos_horarios, horario=horario,
                acertos=stats['acertos'], erros=stats['erros'],
                taxa_acerto=round((stats['acertos']/(stats['erros']+stats['acertos']))*100,1)
                            if (stats['erros']+stats['acertos'])>0 else 0,
                entradas=entradas, resultados=resultados, historico_completo=historico_completo,
                contador_alertas=stats['contador_alertas'],
                sequencia_detectada=WS_RENDER_CACHE.get("sequencia_detectada", stats.get('sequencia_ativa', False)),
                nome_estrategia=WS_RENDER_CACHE.get("nome_estrategia", f"Prob100: {prob100} | Prob50: {prob50}")
            )

        # 2) Fallback: API (1 registro) -> persiste -> render a partir disso
        try:
            # Em vez de "/1", peça 100 registros
            data = requests.get(f"{API_HISTORY_URL}/1", timeout=(3,5)).json()
            registros = data.get('records', [])

            if not registros:
                raise ValueError("API sem 'records'")
        except Exception as e:
            print(f"[API] fallback indisponível: {e}", flush=True)
            return render_somente_cache()

        cores = []
        horarios = []

        for r in registros:
            cor_api = r.get('color')
            created_api = r.get('created_at')

            if cor_api in (0,1,2):
                processar_resultado_ws_fast(cor_api, created_at_iso=created_api,
                                            numero=r.get('roll') or r.get('number') or r.get('result'),
                                            round_id=r.get('id'))
                cores.append(cor_api)
                if created_api:
                    horarios.append(
                        (datetime.strptime(created_api, "%Y-%m-%dT%H:%M:%S.%fZ") - timedelta(hours=3)).strftime("%H:%M:%S")
                    )


        entrada100, prob100, preto100, vermelho100 = calcular_estatisticas(cores, 100)
        entrada50,  prob50,  preto50,  vermelho50  = calcular_estatisticas(cores, 50)
        ultima_nome = _ws_cor_nome(cores[0])
        horario = horarios[0]

        stats = load_stats()
        entradas_slice = stats['historico_entradas'][1:11]
        entradas   = ["preto" if e == "PRETO" else "vermelho" for e in entradas_slice]
        resultados = stats['historico_resultados_binarios'][:len(entradas_slice)]
        ultimas = [("branco" if c == 0 else "vermelho" if c == 1 else "preto") for c in cores[:10][::-1]]
        ultimos_horarios = horarios[:10][::-1]


        historico_completo = []
        for i in range(1, len(stats['historico_entradas'])):
            historico_completo.append({
                "horario":   stats['historico_horarios'][i - 1],
                "previsao":  stats['historico_entradas'][i],
                "resultado": stats['historico_resultados'][i - 1],
                "icone": "✅" if stats['historico_resultados_binarios'][i - 1] is True
                        else "❌" if stats['historico_resultados_binarios'][i - 1] is False else "?"
            })

        return render_template_string(
            TEMPLATE,
            entrada=entrada100,
            sequencia_atual=f"Prob100: {prob100} | Prob50: {prob50}",
            ciclos100_preto=preto100, ciclos100_vermelho=vermelho100,
            ciclos50_preto=preto50,  ciclos50_vermelho=vermelho50,
            ultima=ultima_nome, probabilidade100=prob100, probabilidade50=prob50,
            ultimas=ultimas, ultimos_horarios=ultimos_horarios, horario=horario,
            acertos=stats['acertos'], erros=stats['erros'],
            taxa_acerto=round((stats['acertos']/(stats['acertos']+stats['erros']))*100,1)
                        if stats['acertos']+stats['erros']>0 else 0,
            entradas=entradas, resultados=resultados, historico_completo=historico_completo,
            contador_alertas=stats['contador_alertas'],
            sequencia_detectada=stats.get('sequencia_ativa', False),
            nome_estrategia=f"Prob100: {prob100} | Prob50: {prob50}"
        )

    except Exception as e:
        print(f"[INDEX] erro: {e}", flush=True)
        return render_somente_cache()

# ======== 10) TEMPLATE ========================================================
TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Previsão Blaze (Double)</title>
    <meta http-equiv="refresh" content="1">
    <style>
        body{font-family:Arial,sans-serif;background:#111;color:#eee;margin:0;padding:0;display:flex;justify-content:center}
        .container{display:flex;flex-direction:column;align-items:center;width:100%;max-width:1400px;padding:20px}
        .main-content{display:flex;justify-content:space-between;width:100%}
        .box{background:#222;border-radius:10px;padding:20px;width:65%;margin-right:20px}
        .sidebar{background:#1a1a1a;border-radius:10px;padding:15px;width:30%;overflow-y:auto;max-height:90vh}
        .btn-reset{background:linear-gradient(135deg,#ff4e50,#f9d423);border:none;color:#fff;padding:10px 20px;font-weight:bold;border-radius:30px;cursor:pointer;transition:.3s;box-shadow:0 4px 8px rgba(0,0,0,.3)}
        .btn-reset:hover{transform:scale(1.05);box-shadow:0 6px 12px rgba(0,0,0,.4)}
        .alerta-grande{display:none;background:#ff4d4d;color:#fff;border-radius:8px;padding:15px 25px;font-weight:bold;font-size:1.2em;margin-bottom:20px;box-shadow:0 0 10px rgba(255,0,0,.6);animation:pulsar 1.5s infinite;text-align:center}
        .alerta-grande button{margin-top:10px;background:#fff;color:#c00;border:none;padding:5px 10px;border-radius:5px;font-weight:bold;cursor:pointer}
        @keyframes pulsar{0%,100%{box-shadow:0 0 10px #c00}50%{box-shadow:0 0 20px #f11}}
        .entrada{font-size:1.5em;margin:10px 0;text-align:center}
        .info{font-size:1.1em;margin-top:10px;text-align:center}
        .prob{color:#0f0;font-weight:bold}.prob50{color:#ffa500;font-weight:bold}
        .bola{display:inline-block;width:25px;height:25px;border-radius:50%;margin:0 4px}
        .vermelho{background:red}.preto{background:black}.branco{background:white;border:1px solid #999}
        .entrada-bola{display:inline-block;width:14px;height:14px;border-radius:50%;margin:2px}
        .linha-historico{font-size:.9em;border-bottom:1px solid #444;padding:5px 0}
    </style>
</head>
<body>
<div class="container">
    <div class="alerta-grande" id="alerta" style="display: none;">
        🚨 Estratégia Acionada 🚨
        <button onclick="pararAlarme()">🔇 Silenciar Alarme</button>
    </div>
    <div class="main-content">
        <div class="box">
            <h1 style="text-align:center;color:#0ff;">🎯 Previsão da Blaze (Double)</h1>
            <div class="entrada">➡️ Entrada recomendada: <strong>{{ entrada }}</strong></div>
            <div class="entrada">⚪ Proteção no branco</div>
            <hr>
            <div class="info">🎲 Última jogada: <strong>{{ ultima }}</strong> às <strong>{{ horario }}</strong></div>
            <div class="info">
                📈 Probabilidade 100 rodadas: <span class="prob">{{ probabilidade100 }}%</span><br>
                📉 Probabilidade 50 rodadas: <span class="prob50">{{ probabilidade50 }}%</span>
            </div>
            <div class="info">
                📊 Ciclos (100 rodadas) — Preto: {{ ciclos100_preto }} | Vermelho: {{ ciclos100_vermelho }}<br>
                📊 Ciclos (50 rodadas) — Preto: {{ ciclos50_preto }} | Vermelho: {{ ciclos50_vermelho }}
            </div>
            <hr>
            <div class="info">✅ Acertos: {{ acertos }} | ❌ Erros: {{ erros }} | 🎯 Taxa: {{ taxa_acerto }}%</div>
            <hr>
            <div style="text-align:center;margin-top:10px;">
                <span style="font-size:16px;color:#cc0000;">🔔 Contador de Alarmes: <strong id="contador-alertas">{{ contador_alertas }}</strong></span>
            </div>
            <hr>
            <h3 style="text-align:center;">🕒 Últimas 10 jogadas</h3>
            <div style="text-align:center;">
                {% for i in range(ultimas|length) %}
                <div style="display:inline-block;text-align:center;margin:4px;">
                    <div class="bola {{ ultimas[i] }}"></div>
                    <div style="font-size:.7em;">{{ ultimos_horarios[i] }}</div>
                </div>
                {% endfor %}
            </div>
            <h3 style="text-align:center;">📋 Últimas entradas</h3>
            <div style="text-align:center;">
                {% for i in range(10) %}
                {% if i < entradas|length and i < resultados|length %}
                <div style="display:inline-block;text-align:center;margin:4px;">
                    <div class="entrada-bola {{ entradas[i] }}"></div>
                    <div style="font-size:.8em;">
                        {% if resultados[i] == True %}✅{% elif resultados[i] == False %}❌{% else %}?{% endif %}
                    </div>
                </div>
                {% endif %}
                {% endfor %}
            </div>
            <div style="text-align:center;margin-top:10px;font-size:.85em;color:#ccc;">Atualiza a cada 1s automaticamente</div>
        </div>
        <div class="sidebar scrollable">
            <h3>📜 Histórico Completo</h3>
            {% for h in historico_completo %}
            <div class="linha-historico">
                {{ h['horario'] }} - Previsão: <b>{{ h['previsao'] }}</b> - Resultado: {{ h['resultado'] }} {{ h['icone'] }}
            </div>
            {% endfor %}
        </div>
    </div>
</div>
<script>
let audio = null;

document.addEventListener("DOMContentLoaded", function() {
    const alerta = document.getElementById("alerta");
    const ultimaRodada = "{{ horario }}";
    const chave_silenciada = "silenciado_para_rodada";
    const rodada_silenciada = localStorage.getItem(chave_silenciada);

    // Verifica se a sequência foi detectada e se o alarme não foi silenciado para esta rodada
    if ({{ sequencia_detectada | tojson }} && rodada_silenciada !== ultimaRodada) {
        alerta.style.display = "block";
        
        // Tocar o áudio somente se ele não estiver tocando já para a rodada atual
        if (!window.audio || window.audio_rodada !== ultimaRodada) {
            try {
                window.audio = new Audio("{{ url_for('static', filename='ENTRADA_CONFIRMADA.mp3') }}");
                window.audio.loop = true;
                window.audio.play();
                window.audio_rodada = ultimaRodada;
            } catch (e) {
                console.log("Erro ao tocar o áudio:", e);
            }
        }
    } else {
        alerta.style.display = "none";  // Se não for alarme, esconde o alerta
    }
});

// Função para parar o alarme (pausar o áudio)
function pararAlarme() {
    if (window.audio) {
        window.audio.pause();
        window.audio.currentTime = 0;
    }
    document.getElementById("alerta").style.display = "none";
    const rodadaAtual = "{{ horario }}";
    localStorage.setItem("silenciado_para_rodada", rodadaAtual);  // Marca a rodada como silenciada
}
</script>
</body>
</html>
'''

# ======== 11) MAIN ===========================================================
if __name__ == '__main__':
    # Boot: garante JSON >=100 e buffers WS prontos
    boot_inicial()

    # WebSocket em tempo real
    iniciar_websocket_fastlane()

    # Excel periódico + no encerramento
    iniciar_salvamento_automatico(300)
    atexit.register(salvar_em_excel)

    # Flask
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
