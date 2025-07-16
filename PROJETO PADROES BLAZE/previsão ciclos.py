from flask import Flask, render_template_string, url_for, redirect
import requests
from collections import Counter
from datetime import datetime, timedelta, date
import json
import os
import pandas as pd
import atexit

app = Flask(__name__)

def obter_nome_arquivo_estatisticas():
    hoje = date.today().strftime('%Y-%m-%d')
    return f"estatisticas_{hoje}.json"

ESTATISTICAS_FILE = obter_nome_arquivo_estatisticas()

PROBABILIDADES_ESPECIFICAS = [
    38.3, 38.89, 40.86, 40.91, 41.11, 41.38, 42.05, 45.98, 46.15, 47.13,
    47.25, 48.28, 51.02, 51.11, 51.14, 53.61, 54.08, 55.17, 55.81, 56.67,
    57.14, 57.3, 57.73, 57.78, 58.62, 58.7, 59.78, 60.22, 60.42, 61.05,
    61.22, 61.29, 62.11, 62.77, 63.16, 63.83, 64.21
]
# percentuais dos dia 09 até dia 15 acima de 70%

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

salvar_em_excel()
atexit.register(salvar_em_excel)


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

            <hr>
            <div class="info">
                <h3>📌 Probabilidades Específicas Atuais</h3>
                <div style="display: flex; flex-wrap: wrap; justify-content: center; gap: 6px; padding: 10px;">
                    {% for prob in probabilidades_especificas %}
                        <span style="
                            background-color: {% if prob == probabilidade %}#f00{% else %}#0f0{% endif %};
                            color: {% if prob == probabilidade %}#fff{% else %}#000{% endif %};
                            padding: 6px 12px;
                            border-radius: 15px;
                            font-size: {% if prob == probabilidade %}1.05em{% else %}0.95em{% endif %};
                            font-weight: bold;
                            box-shadow: 0 1px 4px rgba(0,0,0,0.5);
                            display: inline-flex;
                            align-items: center;
                        ">
                            {% if prob == probabilidade %}🔥 {% endif %}{{ prob }}
                        </span>
                    {% endfor %}
                </div>
            </div>


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

        filtrado = [c for c in cores if c != 0]
        contagem = Counter(filtrado)
        total = len(filtrado)

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

        ultima_cor = cores[0]
        ultima_nome = "BRANCO" if ultima_cor == 0 else "VERMELHO" if ultima_cor == 1 else "PRETO"
        horario_utc = horarios_raw[0]
        horario_local = horarios_format[0]
        probabilidade = round((contagem[entrada_valor] / total) * 100, 2)

        if stats.get("ultima_analisada") != horario_utc:
            if stats.get("ultima_analisada") and len(stats['historico_entradas']) > 0:
                previsao_anterior = stats['historico_entradas'][0]
                cor_prevista = 2 if previsao_anterior == "PRETO" else 1
                cor_realizada = ultima_cor  # Cor atual é o resultado da previsão passada
        
                if cor_realizada == cor_prevista or cor_realizada == 0:
                    resultado_binario = True
                    stats['acertos'] += 1
                else:
                    resultado_binario = False
                    stats['erros'] += 1
            else:
                resultado_binario = None
        
            stats['historico_entradas'].insert(0, entrada)
            stats['historico_resultados'].insert(0, ultima_nome)
            stats['historico_horarios'].insert(0, horario_local)
            stats['historico_resultados_binarios'].insert(0, resultado_binario)
            stats['historico_probabilidades'].insert(0, probabilidade)
            stats['ultima_analisada'] = horario_utc

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
            json.dump(stats, f)

        return (
            entrada, ultima_nome, preto, vermelho, ultima_nome, probabilidade,
            ultimas_10, ultimos_horarios, horario_local,
            stats['acertos'], stats['erros'],
            taxa, entradas_formatadas, stats['historico_resultados_binarios'], historico_completo
        )
    except Exception as e:
        return "Erro", "Erro", 0, 0, "Indefinida", 0.0, [], [], "--:--:--", 0, 0, 0, 0, [], [], []

@app.route('/')
def home():
    entrada, ultima, preto, vermelho, ultima_nome, probabilidade, ultimas, ultimos_horarios, horario, acertos, erros, taxa_acerto, entradas, resultados, historico_completo = obter_previsao()
    return render_template_string(
        TEMPLATE,
        entrada=entrada,
        ultima=ultima,
        preto=preto,
        vermelho=vermelho,
        ultima_nome=ultima_nome,
        probabilidade=probabilidade,
        ultimas=ultimas,
        ultimos_horarios=ultimos_horarios,
        horario=horario,
        acertos=acertos,
        erros=erros,
        taxa_acerto=taxa_acerto,
        entradas=entradas,
        resultados=resultados,
        historico_completo=historico_completo,
        probabilidades_especificas=PROBABILIDADES_ESPECIFICAS
    )

if __name__ == '__main__':
    app.run(debug=True)
