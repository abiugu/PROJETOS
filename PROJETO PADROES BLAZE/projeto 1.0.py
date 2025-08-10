from flask import Flask, render_template_string, redirect
import requests
from collections import Counter
from datetime import datetime, timedelta, date
import json
import os
import pandas as pd
import threading
import time
import atexit
import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

app = Flask(__name__)

# Função para obter o nome do arquivo de estatísticas baseado na data
def obter_nome_arquivo_estatisticas():
    hoje = date.today().strftime('%Y-%m-%d')
    return f"estatisticas_{hoje}.json"

def analisar_com_historial(arquivo_json, previsao, txt_path):
    """
    Aguarda o histórico de entradas ter pelo menos duas jogadas adicionais e depois faz a análise de acerto ou erro.
    """
    try:
        # Carrega o histórico de entradas do arquivo JSON
        with open(arquivo_json, 'r') as f:
            stats = json.load(f)
        
        historico_entradas = stats.get("historico_entradas", [])
        
        # Verifica se o histórico tem pelo menos 2 jogadas para analisar
        jogadas_atuais = len(historico_entradas)
        while jogadas_atuais < 2:  # Aguarda pelo menos duas jogadas novas
            print("Aguardando jogadas futuras...")
            time.sleep(2)  # Aguarda 2 segundos antes de verificar novamente
            with open(arquivo_json, 'r') as f:
                stats = json.load(f)
            historico_entradas = stats.get("historico_entradas", [])
            jogadas_atuais = len(historico_entradas)
        
        # Agora temos pelo menos 2 jogadas, podemos analisar
        primeira_jogada = historico_entradas[-2]  # A penúltima jogada
        segunda_jogada = historico_entradas[-1]   # A última jogada
        
        # Define o valor da previsão (1 para vermelho, 2 para preto)
        cor_prevista = 2 if previsao == "PRETO" else 1  # 2 para preto, 1 para vermelho
        
        # Compara com a primeira jogada (sem gravar acerto/erro)
        if primeira_jogada == previsao:
            with open(txt_path, "a", encoding="cp1252", errors="ignore") as f_txt:
                f_txt.write(f"[PREVISÃO: {previsao}] - Resultado: {primeira_jogada}\n")
            return "acerto_direto"
        
        # Se não for acerto direto, tenta o gale (segunda jogada)
        if segunda_jogada == previsao:
            with open(txt_path, "a", encoding="cp1252", errors="ignore") as f_txt:
                f_txt.write(f"[PREVISÃO: {previsao}] - Resultado: {segunda_jogada}\n")
            return "acerto_gale"
        
        # Se nenhuma das jogadas for um acerto, apenas registra a previsão e o resultado
        with open(txt_path, "a", encoding="cp1252", errors="ignore") as f_txt:
            f_txt.write(f"[PREVISÃO: {previsao}] - Resultados: {primeira_jogada}, {segunda_jogada}\n")
        
        return "erro"

    except Exception as e:
        print(f"Erro ao analisar o histórico: {e}")
        return "Erro ao carregar histórico"
    
def verificar_alarme(sequencia_atual, previsao, arquivo_json, txt_path):
    """
    Verifica se uma nova sequência foi identificada e chama a função para análise de acerto ou erro.
    """
    if sequencia_atual is not None:
        print(f"Sequência detectada: {sequencia_atual}")
        
        # Chama a função para aguardar e analisar o histórico
        resultado = analisar_com_historial(arquivo_json, previsao, txt_path)
        
        # Aqui você pode tomar ações com base no resultado retornado
        print(f"Resultado da análise: {resultado}")
        return resultado
    return None

def verificar_acerto_erro(cores, previsao):
    """
    Verifica se a previsão da próxima jogada está correta com base na próxima jogada real.
    A previsão será para a próxima jogada, e a comparação será feita com a cor real dessa jogada.
    """
    if len(cores) < 2:  # Se não houver pelo menos 2 jogadas futuras, retorna "pendente"
        return "pendente"  # Aguarda as jogadas futuras para avaliar
    
    # A previsão será para a próxima jogada após a sequência
    cor_prevista = 2 if previsao == "PRETO" else 1  # 2 para preto, 1 para vermelho
    
    # A próxima jogada real após a previsão
    jogada_futura = cores[0]  # A próxima jogada após a sequência
    
    # Verifica se a previsão bate com a cor real da próxima jogada
    if jogada_futura == cor_prevista or jogada_futura == 0:  # Considera "BRANCO" como acerto também
        return "acerto"
    else:
        return "erro"

def analisar_rodadas_futuras(cores, previsao, txt_path):
    """
    Analisa as rodadas que ocorreram após o alarme, para verificar se houve acerto direto, gale ou erro.
    Espera-se que as rodadas futuras já tenham ocorrido.
    """
    if len(cores) < 2:  # Verifica se há pelo menos 2 jogadas (para a primeira e a segunda jogada)
        return "pendente"  # Aguarda as jogadas futuras para avaliar
    
    # Previsão para a próxima jogada
    cor_prevista = 2 if previsao == "PRETO" else 1  # 2 para preto, 1 para vermelho
    
    # Primeira jogada após a previsão (acerto direto)
    primeira_jogada = cores[0]
    if primeira_jogada == cor_prevista or primeira_jogada == 0:  # Considera "BRANCO" como acerto também
        with open(txt_path, "a", encoding="cp1252", errors="ignore") as f_txt:
            f_txt.write(f"[PREVISÃO: {previsao}] - Resultado: {primeira_jogada}\n")
        return "acerto_direto"

    # Se a primeira jogada falhar, tenta o gale (segunda jogada)
    if len(cores) > 1:  # Verifica se há pelo menos duas jogadas
        segunda_jogada = cores[1]
        if segunda_jogada == cor_prevista or segunda_jogada == 0:  # Considera "BRANCO" como acerto também
            with open(txt_path, "a", encoding="cp1252", errors="ignore") as f_txt:
                f_txt.write(f"[PREVISÃO: {previsao}] - Resultado: {segunda_jogada}\n")
            return "acerto_gale"
    
    # Se nem o acerto direto, nem o gale forem acertados, apenas registra a previsão e o resultado
    with open(txt_path, "a", encoding="cp1252", errors="ignore") as f_txt:
        f_txt.write(f"[PREVISÃO: {previsao}] - Resultado: {cores[1] if len(cores) > 1 else 'N/A'}\n")
    
    return "erro"

def salvar_alerta_pendente(sequencia, previsao):
    pendentes_path = os.path.join(os.getcwd(), "sequencias_pendentes.json")

    nova_entrada = {
        "sequencia": sequencia,
        "hora_alerta": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "previsao": previsao,
        "status": "pendente"
    }

    try:
        if os.path.exists(pendentes_path):
            with open(pendentes_path, "r") as f:
                dados = json.load(f)
        else:
            dados = []

        dados.append(nova_entrada)

        with open(pendentes_path, "w") as f:
            json.dump(dados, f, indent=4)
    except Exception as e:
        print(f"Erro ao salvar alerta pendente: {e}")

ESTATISTICAS_FILE = obter_nome_arquivo_estatisticas()

CONTADOR_ALERTAS_GLOBAL = 0
ULTIMAS_SEQUENCIAS_ALERTADAS = set() 

# Sequências válidas para 100 rodadas
desktop_path_100 = os.path.join(os.path.expanduser("~"), "Desktop", "TODAS_SEQUENCIAS_VALIDAS.txt")
with open(desktop_path_100, "r") as f:
    conteudo_100 = f.read()
listas_encontradas_100 = re.findall(r'\[[^\[\]]+\]', conteudo_100)
SEQUENCIAS_VALIDAS_100 = [eval(lista) for lista in listas_encontradas_100]

# Sequências válidas para 50 rodadas
desktop_path_50 = os.path.join(os.path.expanduser("~"), "Desktop", "SEQUENCIAS_VALIDAS_50.txt")
if os.path.exists(desktop_path_50):
    with open(desktop_path_50, "r") as f:
        conteudo_50 = f.read()
    listas_encontradas_50 = re.findall(r'\[[^\[\]]+\]', conteudo_50)
    SEQUENCIAS_VALIDAS_50 = [eval(lista) for lista in listas_encontradas_50]
else:
    SEQUENCIAS_VALIDAS_50 = []

CONTAGEM_ALERTAS = {}

def sequencia_bate(ultimas, sequencia):
    if len(ultimas) < len(sequencia):
        return False
    ultimas_invertidas = list(reversed(ultimas))
    return ultimas_invertidas[-len(sequencia):] == sequencia

def encontrar_alertas_completos(ultimas, *listas_sequencias):
    """Retorna todas as sequências que foram encontradas nas últimas probabilidades."""
    alertas = []
    if not isinstance(ultimas, list):
        return alertas
    
    # Junta todas as listas de sequências em uma única
    sequencias_combinadas = []
    for lista in listas_sequencias:
        sequencias_combinadas.extend(lista)
    
    # Verifica cada sequência
    for seq in sequencias_combinadas:
        if sequencia_bate(ultimas, seq):
            alertas.append(seq)
            chave = str(seq)
            CONTAGEM_ALERTAS[chave] = CONTAGEM_ALERTAS.get(chave, 0) + 1
    return alertas

# Inicializa o arquivo se não existir e garante que as chaves existam
if not os.path.exists(ESTATISTICAS_FILE):
    with open(ESTATISTICAS_FILE, 'w') as f:
        json.dump({
            'acertos': 0,
            'erros': 0,
            'historico_entradas': [],
            'historico_resultados': [],
            'historico_horarios': [],
            'historico_resultados_binarios': [],
            'historico_probabilidade_100': [],
            'historico_probabilidade_50': [],
            'historico_ciclos_preto_100': [],
            'historico_ciclos_vermelho_100': [],
            'historico_ciclos_preto_50': [],
            'historico_ciclos_vermelho_50': [],
            'ultima_analisada': "",
            'contador_alertas': 0,
            'sequencias_alertadas': []
        }, f)

def salvar_em_excel():
    try:
        if not os.path.exists(ESTATISTICAS_FILE):
            return

        with open(ESTATISTICAS_FILE, 'r') as f:
            stats = json.load(f)

        historico_para_planilha = []
        total = len(stats['historico_resultados'])

        for i in range(1, total):
            previsao = stats['historico_entradas'][i]
            resultado = stats['historico_resultados'][i - 1]
            acertou = stats['historico_resultados_binarios'][i - 1]
            historico_para_planilha.append({
                "Horário": stats['historico_horarios'][i - 1] if i - 1 < len(stats['historico_horarios']) else "-",
                "Previsão": previsao,
                "Resultado": resultado,
                "Acertou": "Sim" if acertou is True else "Não" if acertou is False else "N/D",
                "Probabilidade 100": stats['historico_probabilidade_100'][i - 1] if i - 1 < len(stats['historico_probabilidade_100']) else "-",
                "Probabilidade 50": stats['historico_probabilidade_50'][i - 1] if i - 1 < len(stats['historico_probabilidade_50']) else "-",
                "Ciclos Preto 100": stats['historico_ciclos_preto_100'][i - 1] if i - 1 < len(stats['historico_ciclos_preto_100']) else 0,
                "Ciclos Vermelho 100": stats['historico_ciclos_vermelho_100'][i - 1] if i - 1 < len(stats['historico_ciclos_vermelho_100']) else 0,
                "Ciclos Preto 50": stats['historico_ciclos_preto_50'][i - 1] if i - 1 < len(stats['historico_ciclos_preto_50']) else 0,
                "Ciclos Vermelho 50": stats['historico_ciclos_vermelho_50'][i - 1] if i - 1 < len(stats['historico_ciclos_vermelho_50']) else 0,
            })


        df = pd.DataFrame(historico_para_planilha)

        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", "historico diario percentuais", f"historico_completo_{date.today()}.xlsx")
        os.makedirs(os.path.dirname(desktop_path), exist_ok=True)
        df.to_excel(desktop_path, index=False)
        print(f"Planilha salva automaticamente: {desktop_path}")

    except Exception as e:
        print(f"[✘] Falha ao salvar planilha: {e}")

# Função que roda a cada 10 minutos em thread separada
def iniciar_salvamento_automatico(intervalo_em_segundos=600):
    def loop_salvamento():
        while True:
            salvar_em_excel()
            time.sleep(intervalo_em_segundos)

    thread = threading.Thread(target=loop_salvamento, daemon=True)
    thread.start()

# Inicia salvamento ao sair
atexit.register(salvar_em_excel)

# Inicia salvamento automático periódico
iniciar_salvamento_automatico()

TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Previsão Blaze (Double)</title>
    <meta http-equiv="refresh" content="2">
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #111;
            color: #eee;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
        }

        .container {
            display: flex;
            flex-direction: column;
            align-items: center;
            width: 100%;
            max-width: 1400px;
            padding: 20px;
        }

        .main-content {
            display: flex;
            justify-content: space-between;
            width: 100%;
        }

        .box {
            background-color: #222;
            border-radius: 10px;
            padding: 20px;
            width: 65%;
            margin-right: 20px;
        }

        .sidebar {
            background-color: #1a1a1a;
            border-radius: 10px;
            padding: 15px;
            width: 30%;
            overflow-y: auto;
            max-height: 90vh;
        }

        .btn-reset {
            background: linear-gradient(135deg, #ff4e50, #f9d423);
            border: none;
            color: white;
            padding: 10px 20px;
            font-size: 1em;
            font-weight: bold;
            border-radius: 30px;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        }

        .btn-reset:hover {
            transform: scale(1.05);
            box-shadow: 0 6px 12px rgba(0,0,0,0.4);
        }

        .alerta-grande {
            display: none;
            background-color: #ff4d4d;
            color: white;
            border-radius: 8px;
            padding: 15px 25px;
            font-weight: bold;
            font-size: 1.2em;
            margin-bottom: 20px;
            box-shadow: 0 0 10px rgba(255, 0, 0, 0.6);
            animation: pulsar 1.5s infinite;
            text-align: center;
        }

        .alerta-grande button {
            margin-top: 10px;
            background-color: white;
            color: #cc0000;
            border: none;
            padding: 5px 10px;
            border-radius: 5px;
            font-weight: bold;
            cursor: pointer;
        }

        @keyframes pulsar {
            0%, 100% { box-shadow: 0 0 10px #cc0000; }
            50% { box-shadow: 0 0 20px #ff1a1a; }
        }

        .entrada { font-size: 1.5em; margin: 10px 0; text-align: center; }
        .info { font-size: 1.1em; margin-top: 10px; text-align: center; }
        .prob { color: #0f0; font-weight: bold; }
        .prob50 { color: #ffa500; font-weight: bold; }
        .bola {
            display: inline-block;
            width: 25px;
            height: 25px;
            border-radius: 50%;
            margin: 0 4px;
        }
        .vermelho { background-color: red; }
        .preto { background-color: black; }
        .branco { background-color: white; border: 1px solid #999; }
        .entrada-bola {
            display: inline-block;
            width: 14px;
            height: 14px;
            border-radius: 50%;
            margin: 2px;
        }
        .linha-historico {
            font-size: 0.9em;
            border-bottom: 1px solid #444;
            padding: 5px 0;
        }

    </style>
</head>
<body>
    <div class="container">
        <div class="alerta-grande" id="alerta">
            🚨 Sequência Detectada! Alarme Acionado!<br>
            <button onclick="pararAlarme()">🔇 Silenciar Alarme</button>
        </div>

        <div class="main-content">
            <div class="box">
                <h1 style="text-align: center; color: #0ff;">🎯 Previsão da Blaze (Double)</h1>
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
                <div class="info">
                    ✅ Direto: {{ acertos }} | ❌ Erros: {{ erros }} | 🎯 Taxa: {{ taxa_acerto }}%
                </div>
                <hr>
                <div style="text-align: center; margin-top: 10px;">
                    <span style="font-size: 16px; color: #cc0000;">
                        🔔 Contador de Alarmes: <strong id="contador-alertas">{{ contador_alertas }}</strong>
                    </span>
                </div>
                <hr>
                <h3 style="text-align: center;">🕒 Últimas 10 jogadas</h3>
                <div style="text-align: center;">
                    {% for i in range(ultimas|length) %}
                        <div style="display:inline-block; text-align:center; margin: 4px;">
                            <div class="bola {{ ultimas[i] }}"></div>
                            <div style="font-size: 0.7em;">{{ ultimos_horarios[i] }}</div>
                        </div>
                    {% endfor %}
                </div>

                <h3 style="text-align: center;">📋 Últimas entradas</h3>
                <div style="text-align: center;">
                    {% for i in range(10) %}
                        {% if i < entradas|length and i < resultados|length %}
                        <div style="display:inline-block; text-align:center; margin: 4px;">
                            <div class="entrada-bola {{ entradas[i] }}"></div>
                            <div style="font-size: 0.8em;">
                                {% if resultados[i] == True %}
                                    ✅
                                {% elif resultados[i] == False %}
                                    ❌
                                {% else %}
                                    ?
                                {% endif %}
                            </div>
                        </div>
                        {% endif %}
                    {% endfor %}
                </div>
                <hr>
                <form method="POST" action="/reset" style="text-align:center; margin-top: 15px;">
                    <button class="btn-reset">🔄 Resetar Estatísticas</button>
                </form>
                <div style="text-align: center; margin-top: 10px; font-size: 0.85em; color: #ccc;">
                    Atualiza a cada 2s automaticamente
                </div>
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
            const sequenciaAtual = {{ sequencia_atual | tojson if sequencia_atual is not none else '"undefined"' }};

            // Verifica se o alerta foi silenciado para esta sequência
            const ultimaSequenciaSilenciada = localStorage.getItem("ultima_sequencia_silenciada");

            if ({{ sequencia_detectada | tojson }} && sequenciaAtual !== ultimaSequenciaSilenciada) {
                alerta.style.display = "block";
                audio = new Audio('{{ url_for("static", filename="ENTRADA_CONFIRMADA.mp3") }}');
                audio.loop = true;
                audio.play().catch(function(e) {
                    console.log("Erro ao tocar o áudio:", e);
                });
            }
        });

        function pararAlarme() {
            if (audio) {
                audio.pause();
                audio.currentTime = 0;
            }
            const alerta = document.getElementById("alerta");
            if (alerta) alerta.style.display = "none";

            // Salva no localStorage que essa sequência foi silenciada
            const sequenciaAtual = {{ sequencia_atual | tojson }};
            localStorage.setItem("ultima_sequencia_silenciada", sequenciaAtual);
        }
    </script>
</body>
</html>
'''

# Inicializa o arquivo se não existir
if not os.path.exists(ESTATISTICAS_FILE):
    with open(ESTATISTICAS_FILE, 'w') as f:
        json.dump({
            'acertos': 0,
            'erros': 0,
            'historico_entradas': [],
            'historico_resultados': [],
            'historico_horarios': [],
            'historico_resultados_binarios': [],
            'historico_probabilidades': [],
            'historico_ciclos_preto': [],
            'historico_ciclos_vermelho': [],
            'ultima_analisada': "",
            'contador_alertas': 0,
            'sequencias_alertadas': []
        }, f)

def calcular_probabilidade_ciclos(cores, limite=100):
    filtrado = [c for c in cores[:limite] if c != 0]
    contagem = Counter(filtrado)
    total = len(filtrado)
    if total == 0:
        return "PRETO", 0.0
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

def verificar_estrategia_combinada(previsao_anterior, ultima_cor, status100, status50, prob100, prob50):
    estrategia = None

    if previsao_anterior == "VERMELHO" and ultima_cor == 0:
        if status100 and not status50 and prob100 > 50 and prob50 > 50:
            estrategia = "Estratégia 1"
        elif status100 and not status50 and (prob100 > 50 or (prob100 > 50 and prob50 > 50)):
            estrategia = "Estratégia 2"
        elif not status100 and status50 and prob100 <= 50 and prob50 <= 50:
            estrategia = "Estratégia 3"
    elif previsao_anterior == "VERMELHO" and ultima_cor == 2:
        if not status100 and not status50 and prob50 > 50:
            estrategia = "Estratégia 4"
    elif previsao_anterior == "PRETO" and ultima_cor == 0:
        if status100 and not status50 and prob100 > 50 and prob50 > 50:
            estrategia = "Estratégia 5"
        elif status100 and not status50 and (prob100 > 50 or (prob100 > 50 and prob50 > 50)):
            estrategia = "Estratégia 6"
        elif status100 and not status50:
            estrategia = "Estratégia 7 (CORINGA)"
        elif not status100 and status50 and prob100 <= 50 and prob50 <= 50:
            estrategia = "Estratégia 8"
        elif not status100 and status50 and ((prob100 <= 50 and prob50 <= 50) or (prob100 > 50 and prob50 > 50)):
            estrategia = "Estratégia 9"
    elif previsao_anterior == "PRETO" and ultima_cor in [0, 1, 2]:
        if not status100 and  status50:
            estrategia = "Estratégia teste"

    return estrategia


def obter_previsao():
    try:
        with open(ESTATISTICAS_FILE, 'r') as f:
            stats = json.load(f)
        
        global CONTADOR_ALERTAS_GLOBAL, ULTIMAS_SEQUENCIAS_ALERTADAS
        CONTADOR_ALERTAS_GLOBAL = stats.get('contador_alertas', 0)
        ULTIMAS_SEQUENCIAS_ALERTADAS = set(stats.get('sequencias_alertadas', []))

        url = "https://blaze.bet.br/api/singleplayer-originals/originals/roulette_games/recent/history/1"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers)
        data = res.json()
        registros = data['records']
        cores = [r['color'] for r in registros]
        horarios_raw = [r['created_at'] for r in registros]
        horarios_format = [(datetime.strptime(h, "%Y-%m-%dT%H:%M:%S.%fZ") - timedelta(hours=3)).strftime("%H:%M:%S") for h in horarios_raw]

        entrada_100, prob_100, preto_100, vermelho_100 = calcular_probabilidade_ciclos(cores, 100)
        entrada_50, prob_50, preto_50, vermelho_50 = calcular_probabilidade_ciclos(cores, 50)

        entrada = entrada_100
        ultima_cor = cores[0]
        ultima_nome = "BRANCO" if ultima_cor == 0 else "VERMELHO" if ultima_cor == 1 else "PRETO"
        horario_utc = horarios_raw[0]
        horario_local = horarios_format[0]

        # CAMINHOS
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        pendentes_path = os.path.join(os.getcwd(), "sequencias_pendentes.json")

        # Processa nova rodada
        if stats.get("ultima_analisada") != horario_utc:
            if stats.get("ultima_analisada") and len(stats['historico_entradas']) > 0:
                previsao_anterior = stats['historico_entradas'][0]
                cor_prevista = 2 if previsao_anterior == "PRETO" else 1
                cor_realizada = ultima_cor
                if cor_realizada == cor_prevista or cor_realizada == 0:
                    resultado_binario = True
                    stats['acertos'] += 1
                else:
                    resultado_binario = False
                    stats['erros'] += 1
            else:
                resultado_binario = None

            stats.setdefault('historico_probabilidade_100', [])
            stats.setdefault('historico_probabilidade_50', [])
            stats.setdefault('historico_ciclos_preto_100', [])
            stats.setdefault('historico_ciclos_vermelho_100', [])
            stats.setdefault('historico_ciclos_preto_50', [])
            stats.setdefault('historico_ciclos_vermelho_50', [])

            stats['historico_probabilidade_100'].insert(0, prob_100)
            stats['historico_probabilidade_50'].insert(0, prob_50)
            stats['historico_ciclos_preto_100'].insert(0, preto_100)
            stats['historico_ciclos_vermelho_100'].insert(0, vermelho_100)
            stats['historico_ciclos_preto_50'].insert(0, preto_50)
            stats['historico_ciclos_vermelho_50'].insert(0, vermelho_50)
            stats['historico_entradas'].insert(0, entrada)
            stats['historico_resultados'].insert(0, ultima_nome)
            stats['historico_horarios'].insert(0, horario_local)
            stats['historico_resultados_binarios'].insert(0, resultado_binario)
            stats['ultima_analisada'] = horario_utc

            if os.path.exists(pendentes_path):
                with open(pendentes_path, "r") as f:
                    pendentes = json.load(f)

                novos_pendentes = []
                for item in pendentes:
                    if item["status"] == "pendente":
                        previsao = item["previsao"]
                        cor_prevista = 2 if previsao == "PRETO" else 1

                        if len(cores) > 1:
                            cor_1 = cores[1]
                            nome_1 = "BRANCO" if cor_1 == 0 else "VERMELHO" if cor_1 == 1 else "PRETO"
                            if cor_1 == cor_prevista or cor_1 == 0:
                                item["status"] = "acerto_direto"
                            elif len(cores) > 2:
                                cor_2 = cores[2]
                                nome_2 = "BRANCO" if cor_2 == 0 else "VERMELHO" if cor_2 == 1 else "PRETO"
                                if cor_2 == cor_prevista or cor_2 == 0:
                                    item["status"] = "acerto_gale"
                                else:
                                    item["status"] = "erro"
                            else:
                                # Ainda falta a segunda jogada (gale) — manter pendente
                                novos_pendentes.append(item)
                                continue
                        else:
                            # Ainda falta a primeira jogada — manter pendente
                            novos_pendentes.append(item)
                            continue



        # DETECTAR NOVAS SEQUÊNCIAS
        historico_probs_100 = [p for p in stats['historico_probabilidade_100'] if isinstance(p, (int, float))][:10]
        alertas_100 = encontrar_alertas_completos(historico_probs_100, SEQUENCIAS_VALIDAS_100)
        historico_probs_50 = [p for p in stats['historico_probabilidade_50'] if isinstance(p, (int, float))][:10]
        alertas_50 = encontrar_alertas_completos(historico_probs_50, SEQUENCIAS_VALIDAS_50)
        alertas_encontrados = alertas_100 + alertas_50

        sequencia_atual = str(alertas_encontrados[0]) if alertas_encontrados else None
        sequencia_mudou = sequencia_atual is not None and sequencia_atual != stats.get('sequencia_atual')
        stats['sequencia_atual'] = sequencia_atual
        sequencia_detectada = bool(sequencia_atual)
        estrategia_disparada = None

        for alerta in alertas_encontrados:
            alerta_str = str(alerta)
            if alerta_str not in ULTIMAS_SEQUENCIAS_ALERTADAS:
                previsao = "PRETO" if alerta[-1] >= 51.0 else "VERMELHO"
                estrategia_disparada = verificar_estrategia_combinada(
                    previsao, ultima_cor,
                    preto_100 > 0 if previsao == "PRETO" else vermelho_100 > 0,
                    preto_50 > 0 if previsao == "PRETO" else vermelho_50 > 0,
                    alerta[-1],  # prob100
                    stats['historico_probabilidade_50'][0] if stats['historico_probabilidade_50'] else 0  # prob50
                )

                print("Estratégia ativada:", estrategia_disparada)  # ← ADICIONE AQUI
                if estrategia_disparada:
                    CONTADOR_ALERTAS_GLOBAL += 1
                    ULTIMAS_SEQUENCIAS_ALERTADAS.add(alerta_str)
                    hora_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    salvar_alerta_pendente(alerta, previsao)

                    # Logar estratégia
                    txt_path = os.path.join(os.path.expanduser("~"), "Desktop", "sequencias_alertadas.txt")
                    with open(txt_path, "a", encoding="cp1252", errors="ignore") as f:
                        f.write(f"[ALERTA] {hora_atual} - {alerta} - Previsão: {previsao} - Estratégia: {estrategia_disparada}\n")

        sequencia_detectada = estrategia_disparada is not None
        stats['contador_alertas'] = CONTADOR_ALERTAS_GLOBAL
        stats['sequencias_alertadas'] = list(ULTIMAS_SEQUENCIAS_ALERTADAS)

        total_hits = stats['acertos'] + stats['erros']
        taxa = round((stats['acertos'] / total_hits) * 100, 1) if total_hits > 0 else 0
        entradas_formatadas = ["preto" if e == "PRETO" else "vermelho" for e in stats['historico_entradas']]
        ultimas_10 = ["branco" if c == 0 else "vermelho" if c == 1 else "preto" for c in cores[:10][::-1]]
        ultimos_horarios = horarios_format[:10][::-1]

        historico_completo = []
        for i in range(1, len(stats['historico_entradas'])):
            historico_completo.append({
                "horario": stats['historico_horarios'][i - 1],
                "previsao": stats['historico_entradas'][i],
                "resultado": stats['historico_resultados'][i - 1],
                "icone": "✅" if stats['historico_resultados_binarios'][i - 1] is True else "❌" if stats['historico_resultados_binarios'][i - 1] is False else "?",
            })

        with open(ESTATISTICAS_FILE, 'w') as f:
            json.dump(stats, f, indent=4)

        return (
            entrada, preto_100, vermelho_100, preto_50, vermelho_50, ultima_nome, prob_100, prob_50,
            ultimas_10, ultimos_horarios, horario_local,
            stats['acertos'], stats['erros'], taxa,
            entradas_formatadas, stats['historico_resultados_binarios'], historico_completo,
            sequencia_detectada, sequencia_mudou, sequencia_atual
        )

    except Exception as e:
        print("Erro:", e)
        return "Erro", 0, 0, 0, 0, "Indefinida", 0.0, 0.0, [], [], "--:--:--", 0, 0, 0, [], [], [], False, False, None

@app.route('/')
def home():
    # Inicializa sequencia_atual antes de usá-la
    sequencia_atual = "undefined"  # ou algum valor padrão que faça sentido no seu caso
    
    return renderizar_tela(sequencia_atual)

@app.route('/reset', methods=['POST'])
def resetar():
    resetar_estatisticas()
    return redirect('/')

def renderizar_tela(sequencia_atual):
    (entrada, preto100, vermelho100, preto50, vermelho50, ultima_nome, prob100, prob50, ultimas, ultimos_horarios, horario, acertos, erros, taxa_acerto, entradas, resultados, historico_completo, sequencia_detectada, sequencia_mudou, sequencia_atual) = obter_previsao()

    # Carrega estatísticas para enviar ao template
    with open(ESTATISTICAS_FILE, 'r') as f:
        stats = json.load(f)
    
    ULTIMAS_PROBABILIDADES = [p for p in stats['historico_probabilidade_100'] if isinstance(p, (int, float))][:10]
    alertas_iminentes = encontrar_alertas_completos(ULTIMAS_PROBABILIDADES, SEQUENCIAS_VALIDAS_50, SEQUENCIAS_VALIDAS_100)
    contador_alertas = CONTADOR_ALERTAS_GLOBAL

    # Passa a sequencia_atual para o template
    return render_template_string(TEMPLATE,
        entrada=entrada,
        sequencia_atual=sequencia_atual,  # Passando a variável corretamente para o template
        ciclos100_preto=preto100, ciclos100_vermelho=vermelho100,
        ciclos50_preto=preto50, ciclos50_vermelho=vermelho50,
        ultima=ultima_nome,
        probabilidade100=prob100,
        probabilidade50=prob50,
        ultimas=ultimas,
        ultimos_horarios=ultimos_horarios,
        horario=horario,
        acertos=acertos,
        erros=erros,
        taxa_acerto=taxa_acerto,
        entradas=entradas,
        resultados=resultados,
        historico_completo=historico_completo,
        alertas_iminentes=alertas_iminentes,
        contador_alertas=contador_alertas,
        sequencia_detectada=sequencia_detectada
    )

def resetar_estatisticas():
    with open(ESTATISTICAS_FILE, 'w') as f:
        json.dump({
            'acertos': 0,
            'erros': 0,
            'historico_entradas': [],
            'historico_resultados': [],
            'historico_horarios': [],
            'historico_resultados_binarios': [],
            'historico_probabilidade_100': [],
            'historico_probabilidade_50': [],
            'historico_ciclos_preto_100': [],
            'historico_ciclos_vermelho_100': [],
            'historico_ciclos_preto_50': [],
            'historico_ciclos_vermelho_50': [],
            'ultima_analisada': "",
            'contador_alertas': 0,
            'sequencias_alertadas': []
        }, f, indent=4)  # Use indent para formatar o JSON de forma mais legível

    try:
        os.remove("sequencias_pendentes.json")
    except FileNotFoundError:
        pass

    try:
        os.remove(os.path.join(os.path.expanduser("~"), "Desktop", "sequencias_alertadas.txt"))
    except FileNotFoundError:
        pass

    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
