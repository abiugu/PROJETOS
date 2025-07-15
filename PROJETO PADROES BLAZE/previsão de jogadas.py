from flask import Flask, render_template_string, url_for, redirect
import requests
from collections import Counter
from datetime import datetime, timedelta, date
import json
import os
import pandas as pd
import atexit
import random

app = Flask(__name__)

def obter_nome_arquivo_estatisticas():
    hoje = date.today().strftime('%Y-%m-%d')
    return f"estatisticas2_{hoje}.json"

ESTATISTICAS_FILE = obter_nome_arquivo_estatisticas()

PROBABILIDADES_ESPECIFICAS = [
    47.25, 59.78, 55.17, 62.11, 53.85, 40.91, 41.38, 45.98, 57.73, 60.22, 63.83, 52.87, 58.62
]

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
            'ultima_analisada': ""
        }, f)

def salvar_em_excel():
    if not os.path.exists(ESTATISTICAS_FILE):
        return
    with open(ESTATISTICAS_FILE, 'r') as f:
        stats = json.load(f)
    historico_para_planilha = []
    for i in range(len(stats['historico_entradas'])):
        historico_para_planilha.append({
            "Horário": stats['historico_horarios'][i],
            "Previsão": stats['historico_entradas'][i],
            "Resultado": stats['historico_resultados'][i],
            "Acertou": "Sim" if stats['historico_resultados_binarios'][i] is True else "Não" if stats['historico_resultados_binarios'][i] is False else "N/D",
            "Probabilidade": stats['historico_probabilidades'][i] if i < len(stats['historico_probabilidades']) else "-"
        })
    df = pd.DataFrame(historico_para_planilha)
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", "historico diario percentuais", f"historico_completo_{date.today()}.xlsx")
    df.to_excel(desktop_path, index=False)


TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Previsão Blaze (Double)</title>
    <meta http-equiv="refresh" content="2">
    <style>
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
            justify-content: center;
            padding: 20px;
            max-width: 1400px;
            width: 100%;
        }
        .box {
            background-color: #222;
            border-radius: 10px;
            padding: 20px;
            width: 60%;
            margin-right: 20px;
        }
        .sidebar {
            background-color: #1a1a1a;
            border-radius: 10px;
            padding: 15px;
            width: 35%;
            overflow-y: auto;
            max-height: 90vh;
        }
        h1 { color: #0ff; text-align: center; }
        .entrada { font-size: 1.5em; margin: 10px 0; text-align: center; }
        .info { font-size: 1.1em; margin-top: 10px; text-align: center; }
        .prob { color: #0f0; }
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
    </style>
</head>
<body>
    <div class="container">
        <div class="box">
            <h1>🎯 Previsão da Blaze (Double)</h1>
            <div class="entrada">➡️ Entrada recomendada: <strong>{{ entrada }}</strong></div>
            <div class="entrada">⚪ Proteção no branco</div>
            <hr>
            <div class="info">🎲 Última jogada: <strong>{{ ultima }}</strong> às <strong>{{ horario }}</strong></div>
            <div class="info">📈 Probabilidade estimada: <span class="prob">{{ probabilidade }}%</span></div>

            {% if probabilidade in probabilidades_especificas %}
            <audio autoplay>
                <source src="{{ url_for('static', filename='ENTRADA_CONFIRMADA.mp3') }}" type="audio/mpeg">
            </audio>
            {% endif %}

            <hr>
            <div class="info">
                ✅ Direto: {{ acertos }} | ❌ Erros: {{ erros }} | 🎯 Taxa: {{ taxa_acerto }}%
            </div>
            <div class="info">📊 Ciclos — Preto: {{ preto }} | Vermelho: {{ vermelho }}</div>

            <div class="historico">
                <h3 style="text-align: center;">🕒 Últimas 10 jogadas</h3>
                <div style="text-align: center;">
                    {% for i in range(ultimas|length) %}
                        <div style="display:inline-block; text-align:center; margin: 4px;">
                            <div class="bola {{ ultimas[i] }}"></div>
                            <div style="font-size: 0.7em;">{{ ultimos_horarios[i] }}</div>
                        </div>
                    {% endfor %}
                </div>
            </div>
            
            <div class="historico">
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
            </div>


            <div class="historico">
                <form method="POST" action="/reset">
                    <div style="display: flex; justify-content: center; margin-top: 10px;">
                        <button class="btn-reset">🔄 Resetar Estatísticas</button>
                    </div>
                </form>
                <div style="text-align: center; margin-top: 10px; font-size: 0.85em; color: #ccc;">
                    Atualiza a cada 2s automaticamente
                </div>
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
</body>
</html>
'''

@app.route('/reset', methods=['POST'])
def reset():
    with open(ESTATISTICAS_FILE, 'w') as f:
        json.dump({
            'acertos': 0,
            'gales': 0,
            'erros': 0,
            'historico_entradas': [],
            'historico_resultados': [],
            'historico_horarios': [],
            'historico_resultados_binarios': [],
            'historico_probabilidades': [],
            'ultima_analisada': ""
        }, f)
    return redirect('/')

def obter_previsao():
    try:
        with open(ESTATISTICAS_FILE, 'r') as f:
            stats = json.load(f)

        # Coleta do histórico da API
        url = "https://blaze.bet.br/api/singleplayer-originals/originals/roulette_games/recent/history/1"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers)
        data = res.json()
        registros = data['records']

        cores = [r['color'] for r in registros]
        horarios_raw = [r['created_at'] for r in registros]
        horarios_format = [
            (datetime.strptime(h, "%Y-%m-%dT%H:%M:%S.%fZ") - timedelta(hours=3)).strftime("%H:%M:%S")
            for h in horarios_raw
        ]

        # Análise das últimas 10 rodadas
        ultimas_10 = cores[:10]
        total_pretos = ultimas_10.count(2)
        total_vermelhos = ultimas_10.count(1)

        # Estratégia de previsão
        if total_pretos > total_vermelhos:
            entrada = "PRETO"
            entrada_valor = 2
        elif total_vermelhos > total_pretos:
            entrada = "VERMELHO"
            entrada_valor = 1
        else:
            entrada = random.choice(["PRETO", "VERMELHO"])
            entrada_valor = 2 if entrada == "PRETO" else 1

        # Probabilidade baseada nas 10 últimas
        contagem = Counter(ultimas_10)
        total = len([c for c in ultimas_10 if c in [1, 2]])
        probabilidade = round((contagem[entrada_valor] / total) * 100, 2) if total > 0 else 50.0

        # Última jogada
        ultima_cor = cores[0]
        ultima_nome = "BRANCO" if ultima_cor == 0 else "VERMELHO" if ultima_cor == 1 else "PRETO"
        horario_local = horarios_format[0]

        # Resultados finais
        return {
            'entrada': entrada,
            'entrada_valor': entrada_valor,
            'ultima': ultima_nome,
            'horario': horario_local,
            'probabilidade': probabilidade,
            'ultimas_cores': cores[:10],
            'ultimos_horarios': horarios_format[:10],
            'preto': total_pretos,
            'vermelho': total_vermelhos
        }

    except Exception as e:
        print(f"Erro ao obter previsão: {e}")
        return None

@app.route('/')
def home():
    previsao = obter_previsao()
    if not previsao:
        return "Erro ao obter previsão", 500

    with open(ESTATISTICAS_FILE, 'r') as f:
        stats = json.load(f)

    return render_template_string(
        TEMPLATE,
        entrada=previsao['entrada'],
        ultima=previsao['ultima'],
        horario=previsao['horario'],
        probabilidade=previsao['probabilidade'],
        ultimas=previsao['ultimas_cores'],
        ultimos_horarios=previsao['ultimos_horarios'],
        preto=previsao['preto'],
        vermelho=previsao['vermelho'],
        acertos=stats['acertos'],
        erros=stats['erros'],
        taxa_acerto=round((stats['acertos'] / (stats['acertos'] + stats['erros'])) * 100, 1) if stats['acertos'] + stats['erros'] > 0 else 0,
        entradas=stats['historico_entradas'][:10],
        resultados=stats['historico_resultados'][:10],
        historico_completo=stats['historico_resultados']
    )

if __name__ == '__main__':
    app.run(debug=True)