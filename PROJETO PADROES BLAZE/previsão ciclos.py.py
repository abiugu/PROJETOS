from flask import Flask, render_template_string, url_for, redirect
import requests
from collections import Counter
from datetime import datetime, timedelta
import json
import os

app = Flask(__name__)
ESTATISTICAS_FILE = 'estatisticas.json'

if not os.path.exists(ESTATISTICAS_FILE):
    with open(ESTATISTICAS_FILE, 'w') as f:
        json.dump({
            'acertos': 0,
            'gales': 0,
            'erros': 0,
            'historico_entradas': [],
            'historico_resultados': [],
            'historico_horarios': [],
            'historico_resultados_binarios': [],
            'historico_completo': [],
            'ultima_analisada': ""
        }, f)

TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Previsão Blaze (Double)</title>
    <meta http-equiv="refresh" content="5">
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
        .reset-btn {
            margin-top: 15px;
            padding: 8px 16px;
            background-color: #900;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        .historico {
            text-align: center;
            margin-top: 20px;
        }
        .linha-historico {
            font-size: 0.9em;
            border-bottom: 1px solid #444;
            padding: 5px 0;
        }
        .scrollable {
            height: 500px;
            overflow-y: scroll;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="box">
            <h1>🎯 Previsão da Blaze (Double)</h1>
            <div class="entrada">➡️ Entrada recomendada: <strong>{{ entrada }}</strong></div>
            <div class="entrada">🔁 Gale 1: <strong>{{ gale }}</strong></div>
            <div class="entrada">⚪ Proteção no branco</div>
            <hr>
            <div class="info">🎲 Última jogada: <strong>{{ ultima }}</strong> às <strong>{{ horario }}</strong></div>
            <div class="info">📈 Probabilidade estimada: <span class="prob">{{ probabilidade }}%</span></div>
            {% if probabilidade > 60 %}
            <audio autoplay>
                <source src="{{ url_for('static', filename='alerta60.mp3') }}" type="audio/mpeg">
            </audio>
            {% endif %}
            <hr>
            <div class="info">
                ✅ Direto: {{ acertos }} | ❌ Erros: {{ erros }} | 🎯 Taxa: {{ taxa_acerto }}%
            </div>
            <div class="info">📊 Ciclos — Preto: {{ preto }} | Vermelho: {{ vermelho }}</div>

            <div class="historico">
                <h3>🕒 Últimas 10 jogadas</h3>
                {% for i in range(ultimas|length) %}
                    <div style="display:inline-block; text-align:center; margin: 4px;">
                        <div class="bola {{ ultimas[i] }}"></div>
                        <div style="font-size: 0.7em;">{{ ultimos_horarios[i] }}</div>
                    </div>
                {% endfor %}
            </div>

            <div class="historico">
                <h3>📋 Últimas entradas</h3>
                {% for i in range(entradas|length) %}
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
                {% endfor %}
            </div>

            <form method="POST" action="/reset">
                <button class="reset-btn" type="submit">Resetar Estatísticas</button>
            </form>
            <div style="margin-top:10px; font-size:0.8em;">Atualiza a cada 5s automaticamente</div>
        </div>

        <div class="sidebar">
            <h3>📜 Histórico Completo</h3>
            {% for h in historico_completo %}
                <div class="linha-historico">
                    {{ h['horario'] }} - Previsão: <b>{{ h['previsao'] }}</b> - Resultado: {{ h['resultado'] }}
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
            'ultima_analisada': ""
        }, f)
    return redirect('/')

def obter_previsao():
    try:
        import pandas as pd

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
        gale = entrada
        entrada_valor = 2 if entrada == "PRETO" else 1

        ultima_cor = cores[0]
        ultima_nome = "BRANCO" if ultima_cor == 0 else "VERMELHO" if ultima_cor == 1 else "PRETO"
        horario_utc = horarios_raw[0]
        horario_local = horarios_format[0]
        probabilidade = round((contagem[entrada_valor] / total) * 100, 2)

        if stats.get("ultima_analisada") != horario_utc:
            stats['historico_probabilidades'] = [probabilidade] + stats.get('historico_probabilidades', [])[:9]
            if stats.get("ultima_analisada"):
                if len(cores) >= 3:
                    previsao = stats['historico_entradas'][0]
                    cor_esperada = 2 if previsao == "PRETO" else 1

                    rodada1 = cores[1]
                    rodada2 = cores[2]
                    
                    if rodada1 == cor_esperada or rodada1 == 0:
                        stats['acertos'] += 1
                        stats['historico_resultados_binarios'] = [True] + stats['historico_resultados_binarios'][:9]
                    else:
                        stats['erros'] += 1
                        stats['historico_resultados_binarios'] = [False] + stats['historico_resultados_binarios'][:9]

                else:
                    stats['historico_resultados_binarios'] = [None] + stats['historico_resultados_binarios'][:9]
            else:
                stats['historico_resultados_binarios'] = [None] + stats['historico_resultados_binarios'][:9]

            stats['historico_entradas'] = [entrada] + stats['historico_entradas'][:9]
            stats['historico_resultados'] = [ultima_nome] + stats['historico_resultados'][:9]
            stats['historico_horarios'] = [horario_local] + stats['historico_horarios'][:9]
            stats['ultima_analisada'] = horario_utc

        total_hits = stats['acertos'] + stats['gales'] + stats['erros']
        taxa = round(((stats['acertos'] + stats['gales']) / total_hits) * 100, 1) if total_hits > 0 else 0
        entradas_formatadas = ["preto" if e == "PRETO" else "vermelho" for e in stats['historico_entradas']]
        ultimas_10 = ["branco" if c == 0 else "vermelho" if c == 1 else "preto" for c in cores[:10][::-1]]
        ultimos_horarios = horarios_format[:10][::-1]

        # Construir histórico completo para exibição (sem probabilidade)
        historico_completo = []
        for i in range(len(stats['historico_entradas'])):
            historico_completo.append({
                "horario": stats['historico_horarios'][i],
                "previsao": stats['historico_entradas'][i],
                "resultado": stats['historico_resultados'][i],
                "icone": (
                    "✅" if stats['historico_resultados_binarios'][i] is True else
                    "❌" if stats['historico_resultados_binarios'][i] is False else
                    "?"
                )
            })

        # Salvar os dados atualizados
        with open(ESTATISTICAS_FILE, 'w') as f:
            json.dump(stats, f)

        # Gerar o Excel com probabilidade, mas sem mostrar no front
        # Gerar o Excel com probabilidade individual por rodada
        historico_para_planilha = []
        for i in range(len(stats['historico_entradas'])):
            historico_para_planilha.append({
                "Horário": stats['historico_horarios'][i],
                "Previsão": stats['historico_entradas'][i],
                "Resultado": stats['historico_resultados'][i],
                "Acertou": (
                    "Sim" if stats['historico_resultados_binarios'][i] is True else
                    "Não" if stats['historico_resultados_binarios'][i] is False else
                    "N/D"
                ),
                "Probabilidade": stats['historico_probabilidades'][i] if i < len(stats['historico_probabilidades']) else "-"
            })
        
        df = pd.DataFrame(historico_para_planilha)
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", "historico_completo.xlsx")
        df.to_excel(desktop_path, index=False)
        


        return (
            entrada, gale, preto, vermelho, ultima_nome, probabilidade,
            ultimas_10, ultimos_horarios, horario_local,
            stats['acertos'], stats['gales'], stats['erros'],
            taxa, entradas_formatadas, stats['historico_resultados_binarios'], historico_completo
        )
    except Exception as e:
        return "Erro", "Erro", 0, 0, "Indefinida", 0.0, [], [], "--:--:--", 0, 0, 0, 0, [], [], []


@app.route('/')
def home():
    entrada, gale, preto, vermelho, ultima, probabilidade, ultimas, ultimos_horarios, horario, acertos, gales, erros, taxa_acerto, entradas, resultados, historico_completo = obter_previsao()
    return render_template_string(
        TEMPLATE,
        entrada=entrada,
        gale=gale,
        preto=preto,
        vermelho=vermelho,
        ultima=ultima,
        probabilidade=probabilidade,
        ultimas=ultimas,
        ultimos_horarios=ultimos_horarios,
        horario=horario,
        acertos=acertos,
        gales=gales,
        erros=erros,
        taxa_acerto=taxa_acerto,
        entradas=entradas,
        resultados=resultados,
        historico_completo=historico_completo
    )

if __name__ == '__main__':
    app.run(debug=True)
