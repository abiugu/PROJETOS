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

# Alarme para Probabilidade 100
ALARM_PROB100 = {
    "35.71", "46.00", "58.82", "48.00", "46.43", "67.39", "30.11", "47.62", "62.63", "66.29",
    "44.00", "31.58", "43.00", "69.79", "32.65", "36.78", "31.25", "59.52", "31.63", "30.53",
    "71.28", "67.71", "29.67", "62.35", "69.15", "45.78", "30.61", "62.00", "33.71", "29.35",
    "30.43", "37.65", "68.75", "35.35", "65.91", "68.89", "70.00", "69.23", "29.47", "70.21",
    "37.00", "29.03", "41.00", "68.09", "66.28", "60.71", "68.04", "44.58", "45.12", "30.30",
    "67.82", "69.57", "34.48", "35.63", "48.78", "47.56", "64.65", "53.01", "40.48", "35.23",
    "34.09", "32.95", "71.88", "50.00"
}

# Alarme para Probabilidade 50
ALARM_PROB50 = {
    "32.50", "76.60", "58.97", "73.17", "22.22", "80.43", "69.23", "21.74", "25.58", "30.77",
    "75.51", "74.00", "26.83", "61.54", "44.74", "47.37", "22.73", "42.11", "78.05", "24.00",
    "39.47", "78.72", "80.00", "18.75", "22.92", "68.42", "50.00"
}

# Alarme para a combinação de Probabilidade 100 e Probabilidade 50
ALARM_PROB100_PROB50 = {
    ("48.89", "52.27"), ("44.79", "37.5"), ("45.65", "47.73"), ("48.94", "39.13"),
    ("40.86", "41.3"), ("52.63", "62.5"), ("44.57", "47.73"), ("43.01", "46.67"),
    ("53.33", "47.73"), ("59.57", "56.25"), ("43.62", "44.9"), ("51.61", "54.55"),
    ("58.51", "62.5"), ("44.57", "41.67"), ("45.92", "48.98"), ("57.14", "63.04"),
    ("48.98", "45.83"), ("60.42", "58.33"), ("50.54", "60.87"), ("51.55", "56"),
    ("53.76", "43.48"), ("43.3", "37.5"), ("44.44", "44.68"), ("47.25", "47.92"),
    ("50.53", "60.42"), ("46.15", "48.84"), ("61.05", "58.33"), ("56.04", "47.83"),
    ("57.29", "63.27"), ("53.26", "42.22"), ("44.68", "40.82"), ("48.31", "44.44"),
    ("44.68", "48.98"), ("47.73", "46.51"), ("53.26", "45.83"), ("61.05", "62.5"),
    ("54.17", "54"), ("45.16", "42.86"), ("42.22", "44.44"), ("55.91", "46.81"),
    ("60.22", "62.22"), ("53.93", "48.89"), ("56.38", "46.81"), ("62.11", "65.96"),
    ("43.82", "46.67"), ("49.45", "46.51"), ("48.91", "56.82"), ("43.88", "40.82"),
    ("47.83", "57.78"), ("60", "65.96"), ("48.31", "43.18"), ("47.25", "36.96"),
    ("56.38", "66.67"), ("49.46", "43.18"), ("45.65", "52.27"), ("51.14", "45.45"),
    ("48.35", "56.82"), ("48.35", "47.92"), ("46.88", "55.1"), ("40.66", "40"),
    ("47.78", "56.82"), ("48.45", "42.55"), ("45.26", "36.73"), ("51.65", "56.25"),
    ("51.58", "48"), ("58.51", "57.14"), ("57.78", "60.87"), ("44.68", "34.78"),
    ("39.36", "37.5"), ("52.22", "55.81"), ("49.47", "40.82"), ("52.08", "61.22"),
    ("45.83", "47.83"), ("45.92", "46"), ("52.17", "62.22"), ("45.05", "41.67"),
    ("54.44", "46.67"), ("43.48", "47.73"), ("56.18", "54.55"), ("54.84", "52.27"),
    ("60", "54.35"), ("44.21", "36.96"), ("45.16", "43.18"), ("51.69", "53.19"),
    ("41.24", "39.58"), ("41.76", "35.56"), ("55.91", "64.44"), ("49.47", "61.7"),
    ("40.22", "42.55"), ("42.55", "46.94"), ("46.07", "51.16"), ("44.68", "37.78"),
    ("45.05", "33.33"), ("58.7", "61.7"), ("46.59", "44.19"), ("55.79", "47.83"),
    ("50.56", "46.51"), ("47.73", "40.91"), ("51.11", "60"), ("46.88", "36.73"),
    ("45.83", "52.17"), ("47.42", "57.14"), ("55.79", "65.22"), ("51.69", "45.45")
}


app = Flask(__name__)

# Substitua com o token do seu bot e ID do chat
BOT_TOKEN = '8426186947:AAFd4ZSTWfnffJGusY9CiOka0oblLpQvsgU'
CHAT_ID = '1139158385'

# Função para enviar uma mensagem para o Telegram
def enviar_mensagem_telegram(mensagem):
    url = f"https://api.telegram.org/bot8426186947:AAFd4ZSTWfnffJGusY9CiOka0oblLpQvsgU/sendMessage"
    params = {
        "chat_id": 1139158385,
        "text": mensagem
    }
    try:
        response = requests.post(url, data=params)
        if response.status_code != 200:
            print(f"Erro ao enviar mensagem para o Telegram: {response.text}")
    except Exception as e:
        print(f"Erro de conexão: {e}")

# Função para salvar os dados em Excel
def salvar_em_excel():
    try:
        # Certifique-se de que o ARQUIVO_JSON existe
        if not os.path.exists(ARQUIVO_JSON):
            print("[✘] Arquivo JSON não encontrado.")
            return

        # Lê o arquivo JSON
        with open(ARQUIVO_JSON, 'r') as f:
            stats = json.load(f)

        # Prepara os dados para salvar em Excel
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

        # Converte para DataFrame
        df = pd.DataFrame(historico_para_planilha)

        # Salva o arquivo Excel na área de trabalho
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", "historico diario percentuais", f"historico_completo_{date.today()}.xlsx")
        os.makedirs(os.path.dirname(desktop_path), exist_ok=True)
        df.to_excel(desktop_path, index=False)
        print(f"Planilha salva automaticamente: {desktop_path}")

    except Exception as e:
        print(f"[✘] Falha ao salvar planilha: {e}")

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

def enviar_alerta(mensagem):
    """Função para enviar uma mensagem para o Telegram."""
    enviar_mensagem_telegram(mensagem)

def verificar_alarme(prob100, prob50):
    prob100_str = f"{prob100:.2f}"
    prob50_str = f"{prob50:.2f}"

    # Verifica os critérios de alarme para cada probabilidade
    if (prob100_str, prob50_str) in ALARM_PROB100_PROB50:
        return f"Alarme: Prob100 & Prob50 acionado ({prob100_str}% / {prob50_str}%)"
    if prob100_str in ALARM_PROB100:
        return f"Alarme: Prob100 acionado ({prob100_str}%)"
    if prob50_str in ALARM_PROB50:
        return f"Alarme: Prob50 acionado ({prob50_str}%)"
    
    return None  # Não há alarme

def aguardar_atualizacao_json(stats_atualizado):
    """Verifica se houve atualização no JSON, comparando a data da última jogada.""" 
    ultima_analisada_atual = stats_atualizado.get('ultima_analisada', '')

    # Se a data da última jogada mudou, significa que houve atualização no JSON
    if ultima_analisada_atual != stats_atualizado['ultima_analisada']:
        stats_atualizado['ultima_analisada'] = ultima_analisada_atual
        return True  # Houve atualização

    return False  # Não houve atualização

def verificar_acerto_ou_erro(stats):
    # Verifica se o histórico de resultados binários está vazio
    if not stats['historico_resultados_binarios']:
        return None  # Se não houver histórico, não há acerto nem erro

    # Pega o último valor do histórico de acertos/erros (True/False)
    resultado_binario = stats['historico_resultados_binarios'][0]

    # Se for True, significa que foi um acerto
    if resultado_binario:
        return "Acerto Direto"

    # Se for False, significa que foi um erro, então precisamos de uma previsão de Gale
    else:
        return "Erro - Previsão de Gale"

def aguardar_e_verificar_acerto_ou_erro(stats, previsao_anterior, entrada_template=None):
    """Aguarda a atualização do JSON e verifica o resultado para determinar a próxima ação."""  
    ultima_atualizacao = stats['ultima_analisada']  # Armazenando o valor inicial da última atualização
    
    while True:  # Laço infinito para aguardar a atualização do JSON
        # Lê o arquivo JSON
        with open(ARQUIVO_JSON, 'r') as f:
            stats_atualizado = json.load(f)
        
        # Verifica se houve atualização no JSON
        if stats_atualizado['ultima_analisada'] != ultima_atualizacao:
            ultima_atualizacao = stats_atualizado['ultima_analisada']  # Atualiza a variável de última atualização
            break  # Sair do loop quando houver atualização

    # Verificar se houve acerto ou erro
    resultado = verificar_acerto_ou_erro(stats)

    if resultado == "Acerto Direto":
        # Enviar mensagem de acerto direto
        mensagem_acerto = f"🔔 Acerto Direto! 🎯 Previsão correta!"
        enviar_mensagem_telegram(mensagem_acerto)
        return "Acerto Direto"
    
    elif resultado == "Erro - Previsão de Gale":
        # Enviar mensagem para nova previsão de Gale
        mensagem_gale = f"🔔 Erro! 🚨 Enviando previsão de Gale!"
        if entrada_template:
            mensagem_gale += f" Nova previsão de Gale: {entrada_template}"
        enviar_mensagem_telegram(mensagem_gale)
        
        # Aguarda o Gale ser resolvido
        resultado_gale = aguardar_e_verificar_acerto_ou_erro(stats, previsao_anterior, entrada_template)
        return resultado_gale
    
    return "Nenhuma atualização após 3 tentativas"

def verificar_estrategia_combinada(stats, prob100, prob50, ultima_cor, previsao_anterior=None, status100=None, status50=None, entrada100=None, horario=None):
    prob100_str = f"{prob100:.2f}"
    prob50_str = f"{prob50:.2f}"

    # Mapeamento de cores para emojis
    cor_emoji = {
        "Vermelho": "🔴",
        "Preto": "⚫",
        "Branco": "⚪"
    }

    # Formatação do horário para HH:MM:SS
    horario = datetime.now().strftime("%H:%M:%S")

    # Emoji de alerta
    alarme_emoji = "🔔"

    # Verifica se a probabilidade atende aos critérios para disparar um alarme
    alarme = verificar_alarme(prob100, prob50)

    if alarme:  # Se atender aos critérios de alarme
        # Cria a mensagem de alerta
        mensagem = f"{alarme_emoji} Alerta acionado! {alarme_emoji}\n"

        # Previsão com emoji da cor
        if entrada100:
            emoji_cor = cor_emoji.get(entrada100.capitalize(), "❓")
            mensagem += f"{alarme_emoji} Previsão: {emoji_cor} {entrada100}\n"

        # Adiciona as probabilidades 100 e 50 nas mensagens
        mensagem += f"📊 Probabilidade 100: {prob100_str}% | Probabilidade 50: {prob50_str}%\n"

        # Hora da jogada
        if horario:
            mensagem += f"🕒 Hora da jogada: {horario}\n"

        # Envia a mensagem para o Telegram
        enviar_mensagem_telegram(mensagem)

        # Aguardar e verificar acerto/erro
        resultado = aguardar_e_verificar_acerto_ou_erro(stats, previsao_anterior, entrada100)

        if resultado == "Acerto Direto":
            print("Acerto direto! Prosseguir com a próxima jogada.")
        elif resultado == "Erro - Previsão de Gale":
            print("Erro! Realizar previsão de Gale.")
    else:
        print("Não há alarme, não será enviado mensagem.")


# Função para determinar a cor da previsão
def verificar_cor(cor):
    if cor == 0:
        return "BRANCO"
    elif cor == 1:
        return "VERMELHO"
    elif cor == 2:
        return "PRETO"
    else:
        return "Desconhecido"


@app.route('/')
def index():
    try:
        res = requests.get("https://blaze.bet.br/api/singleplayer-originals/originals/roulette_games/recent/history/1")
        data = res.json()

        tentativas = 0
        while 'records' not in data and tentativas < 3:
            print(f"[✘] Erro: campo 'records' não encontrado. Tentando novamente ({tentativas+1}/3)...")
            time.sleep(3)
            try:
                res = requests.get("https://blaze.bet.br/api/singleplayer-originals/originals/roulette_games/recent/history/1")
                data = res.json()
            except Exception as e:
                print(f"[✘] Erro ao requisitar API: {e}")
            tentativas += 1

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

        ultima_api = registros[0]['created_at']
        if stats['ultima_analisada'] == ultima_api:
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
                sequencia_atual= "Prob100: {} | Prob50: {}".format(prob100, prob50),
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
                nome_estrategia = "Prob100: {} | Prob50: {}".format(prob100, prob50)
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
            previsao_anterior=previsao_anterior,
            ultima_cor=ultima_cor,
            status100=status100,
            status50=status50,
            prob100=prob100,
            prob50=prob50,
            entrada100=entrada100,
            stats=stats
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

            if "sequencias_alertadas" not in stats:
                stats["sequencias_alertadas"] = []

            stats["sequencias_alertadas"].insert(0, f"{estrategia_disparada} - {horario}")
        else:
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
            sequencia_atual="Prob100: {} | Prob50: {}".format(prob100, prob50),
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
            nome_estrategia = "Prob100: {} | Prob50: {}".format(prob100, prob50)
        )

    except Exception as e:
        return f"Erro: {e}"


# Função que roda o Flask no background (Thread separado)
def run_flask():
    app.run(debug=True, use_reloader=False)

# Inicia o servidor Flask em um thread
flask_thread = threading.Thread(target=run_flask)
flask_thread.daemon = True
flask_thread.start()

# Restante do código para salvar automaticamente e processar dados em segundo plano
def iniciar_salvamento_automatico(intervalo_em_segundos=600):
    def loop_salvamento():
        while True:
            salvar_em_excel()
            time.sleep(intervalo_em_segundos)

    thread = threading.Thread(target=loop_salvamento, daemon=True)
    thread.start()

# Inicia salvamento automático periódico
iniciar_salvamento_automatico()

atexit.register(salvar_em_excel)


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
            🚨 Estratégia Acionada 🚨</strong></strong>
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

def run_flask():
    app.run(debug=True, use_reloader=False)

if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Se quiser manter o programa aberto e evitar sair, pode usar:
    while True:
        time.sleep(0)