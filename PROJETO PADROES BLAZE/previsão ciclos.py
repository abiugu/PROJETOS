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

app = Flask(__name__)

def obter_nome_arquivo_estatisticas():
    hoje = date.today().strftime('%Y-%m-%d')
    return f"estatisticas_{hoje}.json"

def salvar_alerta_pendente(sequencia, previsao):
    pendentes_path = os.path.join(os.getcwd(), "sequencias_pendentes.json")

    nova_entrada = {
        "sequencia": sequencia,
        "hora_alerta": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "previsao": previsao,
        "status": "pendente"
    }

    if os.path.exists(pendentes_path):
        with open(pendentes_path, "r") as f:
            dados = json.load(f)
    else:
        dados = []

    dados.append(nova_entrada)

    with open(pendentes_path, "w") as f:
        json.dump(dados, f, indent=4)

ESTATISTICAS_FILE = obter_nome_arquivo_estatisticas()

CONTADOR_ALERTAS_GLOBAL = 0
ULTIMAS_SEQUENCIAS_ALERTADAS = set() 

# Sequências válidas para 100 rodadas (já existente)
desktop_path_100 = os.path.join(os.path.expanduser("~"), "Desktop", "SEQUENCIAS_VALIDAS.txt")
with open(desktop_path_100, "r") as f:
    conteudo_100 = f.read()
listas_encontradas_100 = re.findall(r'\[[^\[\]]+\]', conteudo_100)
SEQUENCIAS_VALIDAS_100 = [eval(lista) for lista in listas_encontradas_100]

# Sequências válidas para 50 rodadas (novo)
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

        # Sequências iminentes (só para exibir na lateral)
        ULTIMAS_PROBABILIDADES = [p for p in stats['historico_probabilidade_100'] if isinstance(p, (int, float))][:10]
        alertas_iminentes = encontrar_alertas_completos(ULTIMAS_PROBABILIDADES, SEQUENCIAS_VALIDAS_50, SEQUENCIAS_VALIDAS_100)

        historico_para_planilha = []
        total = len(stats['historico_resultados'])

        for i in range(total):
            historico_para_planilha.append({
                "Horário": stats['historico_horarios'][i] if i < len(stats['historico_horarios']) else "-",
                "Previsão": stats['historico_entradas'][i + 1] if i + 1 < len(stats['historico_entradas']) else "-",
                "Resultado": stats['historico_resultados'][i],
                "Acertou": "Sim" if i < len(stats['historico_resultados_binarios']) and stats['historico_resultados_binarios'][i] is True else
                          "Não" if i < len(stats['historico_resultados_binarios']) and stats['historico_resultados_binarios'][i] is False else "N/D",
                "Probabilidade 100": stats['historico_probabilidade_100'][i] if i < len(stats['historico_probabilidade_100']) else "-",
                "Probabilidade 50": stats['historico_probabilidade_50'][i] if i < len(stats['historico_probabilidade_50']) else "-",
                "Ciclos Preto 100": stats['historico_ciclos_preto_100'][i] if i < len(stats['historico_ciclos_preto_100']) else 0,
                "Ciclos Vermelho 100": stats['historico_ciclos_vermelho_100'][i] if i < len(stats['historico_ciclos_vermelho_100']) else 0,
                "Ciclos Preto 50": stats['historico_ciclos_preto_50'][i] if i < len(stats['historico_ciclos_preto_50']) else 0,
                "Ciclos Vermelho 50": stats['historico_ciclos_vermelho_50'][i] if i < len(stats['historico_ciclos_vermelho_50']) else 0,
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
        /* Estilos do botão reset */
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
            justify-content: space-between;
            padding: 20px;
            width: 100%;
            max-width: 1400px;
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
            margin-top: 20px;
        }

        h1 { color: #0ff; text-align: center; }
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
        .scrollable {
            overflow-y: auto;
            max-height: 500px;
        }

        /* ALERTAS */
        .alerta-grande {
            margin: 20px auto;
            padding: 20px;
            max-width: 650px;
            border-radius: 12px;
            font-size: 1.3em;
            font-weight: bold;
            text-align: center;
            box-shadow: 0 0 15px rgba(0,0,0,0.3);
            display: none; /* Inicialmente escondido */
        }
        .alerta-vermelho {
            background-color: #ff4d4d;
            color: #fff;
            border-left: 8px solid #cc0000;
            animation: pulsar 1.5s infinite;
        }
        @keyframes pulsar {
            0%, 100% { box-shadow: 0 0 15px #cc0000; }
            50% { box-shadow: 0 0 25px #ff1a1a; }
        }

        .alerta-titulo {
            font-size: 1.6em;
            margin-bottom: 12px;
        }
    </style>

<script>
    // Verifica se a sequência foi detectada
    if ({{ sequencia_detectada | tojson }}) {
        // Exibe a notificação vermelha
        document.getElementById('alerta').style.display = 'block';

        // Toca o som de alerta
        var audio = new Audio('{{ url_for("static", filename="ENTRADA_CONFIRMADA.mp3") }}');
        audio.play().catch(function(error) {
            console.log("Erro ao tentar tocar o áudio: ", error);
        });
    }
</script>
</head>
<body>
    <div class="container">
        <!-- Alerta Vermelho -->
        <div class="alerta-grande alerta-vermelho" id="alerta">
            <div class="alerta-titulo">🚨 Sequência Detectada! Alarme Acionado!</div>
            <p>Uma sequência válida foi encontrada. Fique atento!</p>
        </div>

        <div class="box">
            <h1>🎯 Previsão da Blaze (Double)</h1>
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
            <!-- Exibindo os contadores de acertos e erros de sequências alertadas -->
            <div class="info">
                <strong>Acertos de Sequências Alertadas:</strong> {{ acertos_sequencias_alertadas }}<br>
                <strong>Erros de Sequências Alertadas:</strong> {{ erros_sequencias_alertadas }}
            </div>

            <form method="POST" action="/reset" style="text-align:center; margin-top: 15px;">
                <button class="btn-reset">🔄 Resetar Estatísticas</button>
            </form>
            <div style="text-align: center; margin-top: 10px; font-size: 0.85em; color: #ccc;">
                Atualiza a cada 2s automaticamente
            </div>
        </div>

        <!-- Histórico lateral -->
        <div class="sidebar scrollable">
            <h3>📜 Histórico Completo</h3>
            {% for h in historico_completo %}
                <div class="linha-historico">
                    {{ h['horario'] }} - Previsão: <b>{{ h['previsao'] }}</b> - Resultado: {{ h['resultado'] }} {{ h['icone'] }}
                </div>
            {% endfor %}
        </div>
    </div>
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

        contador_acertos = stats.get("acertos_sequencias_alertadas", 0)
        contador_erros = stats.get("erros_sequencias_alertadas", 0)

        # CAMINHOS
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        pendentes_path = os.path.join(os.getcwd(), "sequencias_pendentes.json")
        txt_path = os.path.join(desktop, "sequencias_alertadas.txt")

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

            # VERIFICAR SEQUÊNCIAS PENDENTES
            if os.path.exists(pendentes_path):
                with open(pendentes_path, "r") as f:
                    pendentes = json.load(f)

                novos_pendentes = []
                for item in pendentes:
                    if item["status"] == "pendente":
                        previsao = item["previsao"]
                        cor_prevista = 2 if previsao == "PRETO" else 1
                        cor_real = ultima_cor
                        if cor_real == cor_prevista or cor_real == 0:
                            item["status"] = "acerto"
                            contador_acertos += 1
                            with open(txt_path, "a", encoding="utf-8") as f_txt:
                                f_txt.write(f"[✅ ACERTO] {item['hora_alerta']} - {item['sequencia']} - Previsão: {previsao} - Resultado: {ultima_nome}\n")
                        else:
                            item["status"] = "erro"
                            contador_erros += 1
                            with open(txt_path, "a", encoding="utf-8") as f_txt:
                                f_txt.write(f"[❌ ERRO] {item['hora_alerta']} - {item['sequencia']} - Previsão: {previsao} - Resultado: {ultima_nome}\n")
                    novos_pendentes.append(item)

                with open(pendentes_path, "w") as f:
                    json.dump(novos_pendentes, f, indent=4)

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

        for alerta in alertas_encontrados:
            alerta_str = str(alerta)
            if alerta_str not in ULTIMAS_SEQUENCIAS_ALERTADAS:
                CONTADOR_ALERTAS_GLOBAL += 1
                ULTIMAS_SEQUENCIAS_ALERTADAS.add(alerta_str)
                previsao = "PRETO" if alerta[-1] >= 51.0 else "VERMELHO"
                hora_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                salvar_alerta_pendente(alerta, previsao)

        stats['contador_alertas'] = CONTADOR_ALERTAS_GLOBAL
        stats['sequencias_alertadas'] = list(ULTIMAS_SEQUENCIAS_ALERTADAS)
        stats['acertos_sequencias_alertadas'] = contador_acertos
        stats['erros_sequencias_alertadas'] = contador_erros

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
    (entrada, preto100, vermelho100, preto50, vermelho50, ultima_nome, prob100, prob50, ultimas, ultimos_horarios, horario, acertos, erros, taxa_acerto, entradas, resultados, historico_completo, sequencia_detectada, sequencia_mudou, sequencia_atual) = obter_previsao()

    # Acessando os contadores de acertos e erros das sequências alertadas
    with open(ESTATISTICAS_FILE, 'r') as f:
        stats = json.load(f)
    acertos_sequencias_alertadas = stats.get('acertos_sequencias_alertadas', 0)
    erros_sequencias_alertadas = stats.get('erros_sequencias_alertadas', 0)

    ULTIMAS_PROBABILIDADES = [p for p in stats['historico_probabilidade_100'] if isinstance(p, (int, float))][:10]
    alertas_iminentes = encontrar_alertas_completos(ULTIMAS_PROBABILIDADES, SEQUENCIAS_VALIDAS_50, SEQUENCIAS_VALIDAS_100)
    
    contador_alertas = CONTADOR_ALERTAS_GLOBAL

    # Passando os valores de acertos e erros de sequências alertadas para o template
    return render_template_string(TEMPLATE,
        entrada=entrada,
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
        sequencia_detectada=sequencia_detectada,
        acertos_sequencias_alertadas=stats.get('acertos_sequencias_alertadas', 0),  # Passando o contador de acertos
        erros_sequencias_alertadas=stats.get('erros_sequencias_alertadas', 0)   # Passando o contador de erros
    )

if __name__ == '__main__':
    app.run(debug=True)
