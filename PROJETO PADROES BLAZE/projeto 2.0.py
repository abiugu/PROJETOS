# blaze_novo_sistema.py

from flask import Flask, render_template_string, redirect, url_for
import requests
import json
import os
import threading
import time
import pandas as pd
from datetime import datetime, timedelta, date
from collections import Counter
import atexit

app = Flask(__name__)

ARQUIVO_JSON = f"estatisticas_{date.today()}.json"

if not os.path.exists(ARQUIVO_JSON):
    with open(ARQUIVO_JSON, 'w') as f:
        json.dump({
            "acertos": 0,
            "erros": 0,
            "historico_entradas": [],
            "historico_resultados": [],
            "historico_horarios": [],
            "historico_resultados_binarios": [],
            "historico_probabilidade_100": [],
            "historico_probabilidade_50": [],
            "historico_ciclos_preto_100": [],
            "historico_ciclos_vermelho_100": [],
            "historico_ciclos_preto_50": [],
            "historico_ciclos_vermelho_50": [],
            "ultima_analisada": "",
            "contador_alertas": 0,
            "sequencia_ativa": False,
            "estrategia_ativa": ""
        }, f)


def calcular_estatisticas(cores, limite):
    filtrado = [c for c in cores[:limite] if c != 0]
    contagem = Counter(filtrado)
    total = len(filtrado)
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


def verificar_estrategia_combinada(previsao_anterior, ultima_cor, status100, status50, prob100, prob50):
    # Normaliza entrada
    prev = (previsao_anterior or "").strip().upper()

    # Só avaliamos quando saiu BRANCO
    if ultima_cor != 0:
        print("→ Sem estratégia (última cor não é BRANCO).")
        return None

    print(f"\n→ Verificando Estratégia:")
    print(f"Previsão: {prev} | Última cor: {ultima_cor} (BRANCO)")
    print(f"Status100: {status100}, Status50: {status50}")
    print(f"Prob100(E): {prob100}, Prob50(F): {prob50}")

    # Helpers para leitura
    ambas_maior_50 = (prob100 > 50) and (prob50 > 50)
    col_e_maior_50 = (prob100 > 50)  # Coluna E
    col_f_maior_50 = (prob50  > 50)  # Coluna F

    estrategia = None

    # 1) VERMELHO | white | S100=V | S50=F | Ambas > 50
    if prev == "VERMELHO" and status100 and not status50 and ambas_maior_50:
        estrategia = "Estrategia 1"

    # 2) PRETO | white | S100=V | S50=F | Coluna F > 50
    elif prev == "PRETO" and status100 and not status50 and col_f_maior_50:
        estrategia = "Estrategia 2"

    # 3) PRETO | white | S100=V | S50=F | Coluna E > 50
    elif prev == "PRETO" and status100 and not status50 and col_e_maior_50:
        estrategia = "Estrategia 3"

    # 4) VERMELHO | white | S100=V | S50=F | Coluna F > 50
    elif prev == "VERMELHO" and status100 and not status50 and col_f_maior_50:
        estrategia = "Estrategia 4"

    # 5) VERMELHO | white | S100=V | S50=V | Coluna F > 50
    elif prev == "VERMELHO" and status100 and status50 and col_f_maior_50:
        estrategia = "Estrategia 5"

    # 6) VERMELHO | white | S100=V | S50=V | Ambas > 50
    elif prev == "VERMELHO" and status100 and status50 and ambas_maior_50:
        estrategia = "Estrategia 6"

    print(f"Estratégia retornada: {estrategia}")
    return estrategia



@app.route('/')
def index():
    try:
        res = requests.get("https://blaze.bet.br/api/singleplayer-originals/originals/roulette_games/recent/history/1")
        data = res.json()

        # Tentativas de buscar os dados da API
        tentativas = 0
        while 'records' not in data and tentativas < 3:
            print(f"[✘] Erro: campo 'records' não encontrado. Tentando novamente ({tentativas+1}/3)...")
            time.sleep(3)  # espera 3 segundos
            try:
                res = requests.get("https://blaze.bet.br/api/singleplayer-originals/originals/roulette_games/recent/history/1")
                data = res.json()
            except Exception as e:
                print(f"[✘] Erro ao requisitar API: {e}")
            tentativas += 1

        # Se depois de 3 tentativas ainda não veio, recarrega a página
        if 'records' not in data:
            print("[!] Falha após 3 tentativas, recarregando...")
            return redirect(url_for('index'))



        registros = data['records']
        
        cores = [r['color'] for r in registros]
        horarios = [(datetime.strptime(r['created_at'], "%Y-%m-%dT%H:%M:%S.%fZ") - timedelta(hours=3)).strftime("%H:%M:%S") for r in registros]

        entrada100, prob100, preto100, vermelho100 = calcular_estatisticas(cores, 100)
        entrada50, prob50, preto50, vermelho50 = calcular_estatisticas(cores, 50)
        ultima_cor = cores[0]
        ultima_nome = "BRANCO" if ultima_cor == 0 else "VERMELHO" if ultima_cor == 1 else "PRETO"
        horario = horarios[0]

        try:
            with open(ARQUIVO_JSON, 'r') as f:
                stats = json.load(f)
        except:
            stats = {
                "acertos": 0,
                "erros": 0,
                "historico_entradas": [],
                "historico_resultados": [],
                "historico_horarios": [],
                "historico_resultados_binarios": [],
                "historico_probabilidade_100": [],
                "historico_probabilidade_50": [],
                "historico_ciclos_preto_100": [],
                "historico_ciclos_vermelho_100": [],
                "historico_ciclos_preto_50": [],
                "historico_ciclos_vermelho_50": [],
                "ultima_analisada": "",
                "contador_alertas": 0
            }

        # VERIFICAÇÃO CORRETA DA JOGADA JÁ ANALISADA
        ultima_api = registros[0]['created_at']
        if stats['ultima_analisada'] == ultima_api:
            # Jogada já processada, não atualiza nada, só renderiza
            entradas = ["preto" if e == "PRETO" else "vermelho" for e in stats['historico_entradas'][:10]]
            ultimas = ["branco" if c == 0 else "vermelho" if c == 1 else "preto" for c in cores[:10][::-1]]
            ultimos_horarios = horarios[:10][::-1]

            historico_completo = []
            for i in range(1, len(stats['historico_entradas'])):
                historico_completo.append({
                    "horario": stats['historico_horarios'][i - 1],
                    "previsao": stats['historico_entradas'][i],
                    "resultado": stats['historico_resultados'][i - 1],
                    "icone": "✅" if stats['historico_resultados_binarios'][i - 1] is True else "❌" if stats['historico_resultados_binarios'][i - 1] is False else "?",
                })

            return render_template_string(TEMPLATE,
                entrada=stats['historico_entradas'][0] if stats['historico_entradas'] else "N/A",
                sequencia_atual="estrategia",
                ciclos100_preto=preto100,
                ciclos100_vermelho=vermelho100,
                ciclos50_preto=preto50,
                ciclos50_vermelho=vermelho50,
                ultima=ultima_nome,
                probabilidade100=prob100,
                probabilidade50=prob50,
                ultimas=ultimas,
                ultimos_horarios=ultimos_horarios,
                horario=horario,
                acertos=stats['acertos'],
                erros=stats['erros'],
                taxa_acerto=round((stats['acertos'] / (stats['acertos'] + stats['erros'])) * 100, 1) if stats['acertos'] + stats['erros'] > 0 else 0,
                entradas=entradas,
                resultados=stats['historico_resultados_binarios'][:10],
                historico_completo=historico_completo,
                contador_alertas=stats['contador_alertas'],
                sequencia_detectada=stats.get('sequencia_ativa', False),
                nome_estrategia = stats.get('estrategia_ativa', "")

            )


        previsao_anterior = stats['historico_entradas'][0] if len(stats['historico_entradas']) > 1 else None
        resultado_binario = None
        estrategia_disparada = None

        if previsao_anterior:
            cor_prevista = 2 if previsao_anterior == "PRETO" else 1
            if ultima_cor == cor_prevista or ultima_cor == 0:
                resultado_binario = True
                stats['acertos'] += 1
            else:
                resultado_binario = False
                stats['erros'] += 1

            status100 = preto100 < vermelho100
            status50 = preto50 < vermelho50

            estrategia_disparada = verificar_estrategia_combinada(
                previsao_anterior=previsao_anterior,  # ✅ Correto
                ultima_cor=ultima_cor,
                status100=status100,
                status50=status50,
                prob100=prob100,
                prob50=prob50
)


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
        stats['ultima_analisada'] = registros[0]['created_at']
        if estrategia_disparada:
            stats['contador_alertas'] += 1
            stats['sequencia_ativa'] = True
            stats['estrategia_ativa'] = estrategia_disparada

            # Adiciona estratégia + horário ao histórico de alertas
            if "sequencias_alertadas" not in stats:
                stats["sequencias_alertadas"] = []

            stats["sequencias_alertadas"].insert(0, f"{estrategia_disparada} - {horario}")

        else:
            # Sempre limpar se não houve nova estratégia, independente de nova rodada
            stats['sequencia_ativa'] = False
            stats['estrategia_ativa'] = ""


        with open(ARQUIVO_JSON, 'w') as f:
            json.dump(stats, f, indent=4)

        entradas = ["preto" if e == "PRETO" else "vermelho" for e in stats['historico_entradas'][:10]]
        ultimas = ["branco" if c == 0 else "vermelho" if c == 1 else "preto" for c in cores[:10][::-1]]
        ultimos_horarios = horarios[:10][::-1]

        historico_completo = []
        tamanho = min(
            len(stats['historico_entradas']),
            len(stats['historico_resultados']),
            len(stats['historico_horarios']),
            len(stats['historico_resultados_binarios'])
        )
        
        for i in range(1, tamanho):
            historico_completo.append({
                "horario": stats['historico_horarios'][i - 1],
                "previsao": stats['historico_entradas'][i],
                "resultado": stats['historico_resultados'][i - 1],
                "icone": "✅" if stats['historico_resultados_binarios'][i - 1] is True else "❌" if stats['historico_resultados_binarios'][i - 1] is False else "?",
            })


        return render_template_string(TEMPLATE,
            entrada=entrada100,
            sequencia_atual=stats.get('estrategia_ativa', ""),
            ciclos100_preto=preto100,
            ciclos100_vermelho=vermelho100,
            ciclos50_preto=preto50,
            ciclos50_vermelho=vermelho50,
            ultima=ultima_nome,
            probabilidade100=prob100,
            probabilidade50=prob50,
            ultimas=ultimas,
            ultimos_horarios=ultimos_horarios,
            horario=horario,
            acertos=stats['acertos'],
            erros=stats['erros'],
            taxa_acerto=round((stats['acertos'] / (stats['acertos'] + stats['erros'])) * 100, 1) if stats['acertos'] + stats['erros'] > 0 else 0,
            entradas=entradas,
            resultados=stats['historico_resultados_binarios'][:10],
            historico_completo=historico_completo,
            contador_alertas=stats['contador_alertas'],
            sequencia_detectada=bool(estrategia_disparada),
            nome_estrategia = stats.get('estrategia_ativa', "")
        )

    except Exception as e:
        return f"Erro: {e}"


@app.route('/reset', methods=['POST'])
def reset():
    if os.path.exists(ARQUIVO_JSON):
        os.remove(ARQUIVO_JSON)
    return redirect('/')


def salvar_em_excel():
    try:
        if not os.path.exists(ARQUIVO_JSON):
            return

        with open(ARQUIVO_JSON, 'r') as f:
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
            🚨 Estratégia Acionada: <strong id="nome-estrategia">{{ nome_estrategia or "N/D" }}</strong>
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
        const nomeEstrategia = "{{ nome_estrategia }}";
        const ultimaRodada = "{{ horario }}";

        // Chaves para controle no localStorage
        const chave_silenciada = "silenciado_para_rodada";
        const rodada_silenciada = localStorage.getItem(chave_silenciada);

        if ({{ sequencia_detectada | tojson }} && rodada_silenciada !== ultimaRodada) {
            alerta.style.display = "block";

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
            alerta.style.display = "none";
        }
    });

    function pararAlarme() {
        if (window.audio) {
            window.audio.pause();
            window.audio.currentTime = 0;
        }
        document.getElementById("alerta").style.display = "none";

        // Salva no localStorage que essa rodada foi silenciada
        const rodadaAtual = "{{ horario }}";
        localStorage.setItem("silenciado_para_rodada", rodadaAtual);
    }
</script>
</body>
</html>
'''

if __name__ == '__main__':
    app.run(debug=True)
