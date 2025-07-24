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


ESTATISTICAS_FILE = obter_nome_arquivo_estatisticas()

CONTADOR_ALERTAS_GLOBAL = 0
ULTIMAS_SEQUENCIAS_ALERTADAS = set() 

usuario = os.getlogin()
desktop_path = fr"C:\Users\{usuario}\Desktop\SEQUENCIAS_VALIDAS.txt"

with open(desktop_path, "r") as f:
    conteudo = f.read()

# Encontra todas as listas dentro do conteúdo, mesmo que esteja em "SEQUENCIAS_VALIDAS = [...]"
listas_encontradas = re.findall(r'\[[^\[\]]+\]', conteudo)

SEQUENCIAS_VALIDAS = [eval(lista) for lista in listas_encontradas]

CONTAGEM_ALERTAS = {}

SEQUENCIAS_VALIDAS = [
    
    [50.0, 50.54],
    [50.0, 51.06],
    [29.17, 29.35],
    [29.35, 29.47],
    [29.47, 29.67],
    [29.67, 30.53],
    [30.53, 31.03],
    [31.03, 31.25],
    [31.25, 31.31],
    [31.31, 31.82],
    [31.82, 32.61],
    [32.61, 32.65],
    [32.65, 32.95],
    [32.95, 33.72],
    [33.72, 34.48],
    [34.48, 34.69],
    [34.69, 34.78],
    [34.78, 35.96],
    [35.96, 36.78],
    [36.78, 37.65],
    [37.65, 38.0],
    [38.0, 42.17],
    [42.17, 44.58],
    [44.58, 45.24],
    [45.24, 45.78],
    [45.78, 46.34],
    [46.34, 51.22],
    [51.22, 52.44],
    [52.44, 53.57],
    [53.57, 54.88],
    [54.88, 55.95],
    [55.95, 56.63],
    [56.63, 57.83],
    [57.83, 58.82],
    [58.82, 60.71],
    [60.71, 61.0],
    [61.0, 64.65],
    [64.65, 65.12],
    [65.12, 65.66],
    [65.66, 65.91],
    [65.91, 65.93],
    [65.93, 67.01],
    [67.01, 67.42],
    [67.42, 67.71],
    [67.71, 67.82],
    [67.82, 68.04],
    [68.04, 68.37],
    [68.37, 68.75],
    [68.75, 68.89],
    [68.89, 69.15],
    [69.15, 69.39],
    [69.39, 69.79],
    [69.79, 69.89],
    [69.89, 70.65],
    [70.65, 71.28],
    [29.17, 29.35, 29.47],
    [29.35, 29.47, 29.67],
    [29.47, 29.67, 30.53],
    [29.67, 30.53, 31.03],
    [30.53, 31.03, 31.25],
    [31.03, 31.25, 31.31],
    [31.25, 31.31, 31.82],
    [31.31, 31.82, 32.61],
    [31.82, 32.61, 32.65],
    [32.61, 32.65, 32.95],
    [32.65, 32.95, 33.72],
    [32.95, 33.72, 34.48],
    [33.72, 34.48, 34.69],
    [34.48, 34.69, 34.78],
    [34.69, 34.78, 35.96],
    [34.78, 35.96, 36.78],
    [35.96, 36.78, 37.65],
    [36.78, 37.65, 38.0],
    [37.65, 38.0, 42.17],
    [38.0, 42.17, 44.58],
    [42.17, 44.58, 45.24],
    [44.58, 45.24, 45.78],
    [45.24, 45.78, 46.34],
    [45.78, 46.34, 51.22],
    [46.34, 51.22, 52.44],
    [51.22, 52.44, 53.57],
    [52.44, 53.57, 54.88],
    [53.57, 54.88, 55.95],
    [54.88, 55.95, 56.63],
    [55.95, 56.63, 57.83],
    [56.63, 57.83, 58.82],
    [57.83, 58.82, 60.71],
    [58.82, 60.71, 61.0],
    [60.71, 61.0, 64.65],
    [61.0, 64.65, 65.12],
    [64.65, 65.12, 65.66],
    [65.12, 65.66, 65.91],
    [65.66, 65.91, 65.93],
    [65.91, 65.93, 67.01],
    [65.93, 67.01, 67.42],
    [67.01, 67.42, 67.71],
    [67.42, 67.71, 67.82],
    [67.71, 67.82, 68.04],
    [67.82, 68.04, 68.37],
    [68.04, 68.37, 68.75],
    [68.37, 68.75, 68.89],
    [68.75, 68.89, 69.15],
    [68.89, 69.15, 69.39],
    [69.15, 69.39, 69.79],
    [69.39, 69.79, 69.89],
    [69.79, 69.89, 70.65],
    [69.89, 70.65, 71.28],
    [29.17, 29.35, 29.47, 29.67],
    [29.35, 29.47, 29.67, 30.53],
    [29.47, 29.67, 30.53, 31.03],
    [29.67, 30.53, 31.03, 31.25],
    [30.53, 31.03, 31.25, 31.31],
    [31.03, 31.25, 31.31, 31.82],
    [31.25, 31.31, 31.82, 32.61],
    [31.31, 31.82, 32.61, 32.65],
    [31.82, 32.61, 32.65, 32.95],
    [32.61, 32.65, 32.95, 33.72],
    [32.65, 32.95, 33.72, 34.48],
    [32.95, 33.72, 34.48, 34.69],
    [33.72, 34.48, 34.69, 34.78],
    [34.48, 34.69, 34.78, 35.96],
    [34.69, 34.78, 35.96, 36.78],
    [34.78, 35.96, 36.78, 37.65],
    [35.96, 36.78, 37.65, 38.0],
    [36.78, 37.65, 38.0, 42.17],
    [37.65, 38.0, 42.17, 44.58],
    [38.0, 42.17, 44.58, 45.24],
    [42.17, 44.58, 45.24, 45.78],
    [44.58, 45.24, 45.78, 46.34],
    [45.24, 45.78, 46.34, 51.22],
    [45.78, 46.34, 51.22, 52.44],
    [46.34, 51.22, 52.44, 53.57],
    [51.22, 52.44, 53.57, 54.88],
    [52.44, 53.57, 54.88, 55.95],
    [53.57, 54.88, 55.95, 56.63],
    [54.88, 55.95, 56.63, 57.83],
    [55.95, 56.63, 57.83, 58.82],
    [56.63, 57.83, 58.82, 60.71],
    [57.83, 58.82, 60.71, 61.0],
    [58.82, 60.71, 61.0, 64.65],
    [60.71, 61.0, 64.65, 65.12],
    [61.0, 64.65, 65.12, 65.66],
    [64.65, 65.12, 65.66, 65.91],
    [65.12, 65.66, 65.91, 65.93],
    [65.66, 65.91, 65.93, 67.01],
    [65.91, 65.93, 67.01, 67.42],
    [65.93, 67.01, 67.42, 67.71],
    [67.01, 67.42, 67.71, 67.82],
    [67.42, 67.71, 67.82, 68.04],
    [67.71, 67.82, 68.04, 68.37],
    [67.82, 68.04, 68.37, 68.75],
    [68.04, 68.37, 68.75, 68.89],
    [68.37, 68.75, 68.89, 69.15],
    [68.75, 68.89, 69.15, 69.39],
    [68.89, 69.15, 69.39, 69.79],
    [69.15, 69.39, 69.79, 69.89],
    [69.39, 69.79, 69.89, 70.65],
    [69.79, 69.89, 70.65, 71.28],
    [29.17, 29.35, 29.47, 29.67, 30.53],
    [29.35, 29.47, 29.67, 30.53, 31.03],
    [29.47, 29.67, 30.53, 31.03, 31.25],
    [29.67, 30.53, 31.03, 31.25, 31.31],
    [30.53, 31.03, 31.25, 31.31, 31.82],
    [31.03, 31.25, 31.31, 31.82, 32.61],
    [31.25, 31.31, 31.82, 32.61, 32.65],
    [31.31, 31.82, 32.61, 32.65, 32.95],
    [31.82, 32.61, 32.65, 32.95, 33.72],
    [32.61, 32.65, 32.95, 33.72, 34.48],
    [32.65, 32.95, 33.72, 34.48, 34.69],
    [32.95, 33.72, 34.48, 34.69, 34.78],
    [33.72, 34.48, 34.69, 34.78, 35.96],
    [34.48, 34.69, 34.78, 35.96, 36.78],
    [34.69, 34.78, 35.96, 36.78, 37.65],
    [34.78, 35.96, 36.78, 37.65, 38.0],
    [35.96, 36.78, 37.65, 38.0, 42.17],
    [36.78, 37.65, 38.0, 42.17, 44.58],
    [37.65, 38.0, 42.17, 44.58, 45.24],
    [38.0, 42.17, 44.58, 45.24, 45.78],
    [42.17, 44.58, 45.24, 45.78, 46.34],
    [44.58, 45.24, 45.78, 46.34, 51.22],
    [45.24, 45.78, 46.34, 51.22, 52.44],
    [45.78, 46.34, 51.22, 52.44, 53.57],
    [46.34, 51.22, 52.44, 53.57, 54.88],
    [51.22, 52.44, 53.57, 54.88, 55.95],
    [52.44, 53.57, 54.88, 55.95, 56.63],
    [53.57, 54.88, 55.95, 56.63, 57.83],
    [54.88, 55.95, 56.63, 57.83, 58.82],
    [55.95, 56.63, 57.83, 58.82, 60.71],
    [56.63, 57.83, 58.82, 60.71, 61.0],
    [57.83, 58.82, 60.71, 61.0, 64.65],
    [58.82, 60.71, 61.0, 64.65, 65.12],
    [60.71, 61.0, 64.65, 65.12, 65.66],
    [61.0, 64.65, 65.12, 65.66, 65.91],
    [64.65, 65.12, 65.66, 65.91, 65.93],
    [65.12, 65.66, 65.91, 65.93, 67.01],
    [65.66, 65.91, 65.93, 67.01, 67.42],
    [65.91, 65.93, 67.01, 67.42, 67.71],
    [65.93, 67.01, 67.42, 67.71, 67.82],
    [67.01, 67.42, 67.71, 67.82, 68.04],
    [67.42, 67.71, 67.82, 68.04, 68.37],
    [67.71, 67.82, 68.04, 68.37, 68.75],
    [67.82, 68.04, 68.37, 68.75, 68.89],
    [68.04, 68.37, 68.75, 68.89, 69.15],
    [68.37, 68.75, 68.89, 69.15, 69.39],
    [68.75, 68.89, 69.15, 69.39, 69.79],
    [68.89, 69.15, 69.39, 69.79, 69.89],
    [69.15, 69.39, 69.79, 69.89, 70.65],
    [69.39, 69.79, 69.89, 70.65, 71.28],
    [29.17, 29.35, 29.47, 29.67, 30.53, 31.03],
    [29.35, 29.47, 29.67, 30.53, 31.03, 31.25],
    [29.47, 29.67, 30.53, 31.03, 31.25, 31.31],
    [29.67, 30.53, 31.03, 31.25, 31.31, 31.82],
    [30.53, 31.03, 31.25, 31.31, 31.82, 32.61],
    [31.03, 31.25, 31.31, 31.82, 32.61, 32.65],
    [31.25, 31.31, 31.82, 32.61, 32.65, 32.95],
    [31.31, 31.82, 32.61, 32.65, 32.95, 33.72],
    [31.82, 32.61, 32.65, 32.95, 33.72, 34.48],
    [32.61, 32.65, 32.95, 33.72, 34.48, 34.69],
    [32.65, 32.95, 33.72, 34.48, 34.69, 34.78],
    [32.95, 33.72, 34.48, 34.69, 34.78, 35.96],
    [33.72, 34.48, 34.69, 34.78, 35.96, 36.78],
    [34.48, 34.69, 34.78, 35.96, 36.78, 37.65],
    [34.69, 34.78, 35.96, 36.78, 37.65, 38.0],
    [34.78, 35.96, 36.78, 37.65, 38.0, 42.17],
    [35.96, 36.78, 37.65, 38.0, 42.17, 44.58],
    [36.78, 37.65, 38.0, 42.17, 44.58, 45.24],
    [37.65, 38.0, 42.17, 44.58, 45.24, 45.78],
    [38.0, 42.17, 44.58, 45.24, 45.78, 46.34],
    [42.17, 44.58, 45.24, 45.78, 46.34, 51.22],
    [44.58, 45.24, 45.78, 46.34, 51.22, 52.44],
    [45.24, 45.78, 46.34, 51.22, 52.44, 53.57],
    [45.78, 46.34, 51.22, 52.44, 53.57, 54.88],
    [46.34, 51.22, 52.44, 53.57, 54.88, 55.95],
    [51.22, 52.44, 53.57, 54.88, 55.95, 56.63],
    [52.44, 53.57, 54.88, 55.95, 56.63, 57.83],
    [53.57, 54.88, 55.95, 56.63, 57.83, 58.82],
    [54.88, 55.95, 56.63, 57.83, 58.82, 60.71],
    [55.95, 56.63, 57.83, 58.82, 60.71, 61.0],
    [56.63, 57.83, 58.82, 60.71, 61.0, 64.65],
    [57.83, 58.82, 60.71, 61.0, 64.65, 65.12],
    [58.82, 60.71, 61.0, 64.65, 65.12, 65.66],
    [60.71, 61.0, 64.65, 65.12, 65.66, 65.91],
    [61.0, 64.65, 65.12, 65.66, 65.91, 65.93],
    [64.65, 65.12, 65.66, 65.91, 65.93, 67.01],
    [65.12, 65.66, 65.91, 65.93, 67.01, 67.42],
    [65.66, 65.91, 65.93, 67.01, 67.42, 67.71],
    [65.91, 65.93, 67.01, 67.42, 67.71, 67.82],
    [65.93, 67.01, 67.42, 67.71, 67.82, 68.04],
    [67.01, 67.42, 67.71, 67.82, 68.04, 68.37],
    [67.42, 67.71, 67.82, 68.04, 68.37, 68.75],
    [67.71, 67.82, 68.04, 68.37, 68.75, 68.89],
    [67.82, 68.04, 68.37, 68.75, 68.89, 69.15],
    [68.04, 68.37, 68.75, 68.89, 69.15, 69.39],
    [68.37, 68.75, 68.89, 69.15, 69.39, 69.79],
    [68.75, 68.89, 69.15, 69.39, 69.79, 69.89],
    [68.89, 69.15, 69.39, 69.79, 69.89, 70.65],
    [69.15, 69.39, 69.79, 69.89, 70.65, 71.28],
]

def sequencia_bate(ultimas, sequencia):
    if len(ultimas) < len(sequencia):
        return False
    ultimas_invertidas = list(reversed(ultimas))
    return ultimas_invertidas[-len(sequencia):] == sequencia


def encontrar_alertas_completos(ultimas, sequencias_validas):
    """Retorna todas as sequências que foram encontradas nas últimas probabilidades."""
    alertas = []
    if not isinstance(ultimas, list):
        return alertas
    for seq in sequencias_validas:
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
            'historico_probabilidades': [],
            'historico_ciclos_preto': [],
            'historico_ciclos_vermelho': [],
            'ultima_analisada': "",
            'contador_alertas': 0,  # <-- NOVO
            'sequencias_alertadas': []  # <-- NOVO
        }, f)


def salvar_em_excel():
    try:
        if not os.path.exists(ESTATISTICAS_FILE):
            return

        with open(ESTATISTICAS_FILE, 'r') as f:
            stats = json.load(f)
        ULTIMAS_PROBABILIDADES = [p for p in stats['historico_probabilidades'] if isinstance(p, (int, float))][:10]
        alertas_iminentes = encontrar_alertas_completos(ULTIMAS_PROBABILIDADES, SEQUENCIAS_VALIDAS)
        contador_alertas = len(alertas_iminentes)

        stats.setdefault('historico_horarios', [])
        stats.setdefault('historico_entradas', [])
        stats.setdefault('historico_resultados', [])
        stats.setdefault('historico_resultados_binarios', [])
        stats.setdefault('historico_probabilidades', [])
        stats.setdefault('historico_ciclos_preto', [])
        stats.setdefault('historico_ciclos_vermelho', [])

        historico_para_planilha = []
        total = len(stats['historico_resultados'])  # agora usamos resultados como base (é a jogada válida)

        for i in range(total):
            historico_para_planilha.append({
                "Horário": stats['historico_horarios'][i] if i < len(stats['historico_horarios']) else "-",
                "Previsão": stats['historico_entradas'][i + 1] if i + 1 < len(stats['historico_entradas']) else "-",  # previsão anterior
                "Resultado": stats['historico_resultados'][i],
                "Acertou": "Sim" if i < len(stats['historico_resultados_binarios']) and stats['historico_resultados_binarios'][i] is True else
                            "Não" if i < len(stats['historico_resultados_binarios']) and stats['historico_resultados_binarios'][i] is False else "N/D",
                "Probabilidade da Previsão": stats['historico_probabilidades'][i] if i < len(stats['historico_probabilidades']) else "-",
                "Ciclos Preto": stats['historico_ciclos_preto'][i] if i < len(stats['historico_ciclos_preto']) else 0,
                "Ciclos Vermelho": stats['historico_ciclos_vermelho'][i] if i < len(stats['historico_ciclos_vermelho']) else 0
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
        }
        .alerta-grande + .alerta-grande { margin-top: 15px; }
        .alerta-vermelho {
            background-color: #ff4d4d;
            color: #fff;
            border-left: 8px solid #cc0000;
            animation: pulsar 1.5s infinite;
        }
        .alerta-amarelo {
            background-color: #fff3cd;
            color: #856404;
            border-left: 8px solid #ffc107;
        }
        @keyframes pulsar {
            0%, 100% { box-shadow: 0 0 15px #cc0000; }
            50% { box-shadow: 0 0 25px #ff1a1a; }
        }
        .alerta-titulo {
            font-size: 1.6em;
            margin-bottom: 12px;
        }
        .alerta-grande ul {
            list-style: none;
            padding: 0;
            margin: 10px 0 0 0;
        }
        .alerta-grande li {
            font-size: 1.4em;
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

            <audio id="som-alerta" src="{{ url_for('static', filename='ENTRADA_CONFIRMADA.mp3') }}"></audio>

            <script>
                const prob = {{ probabilidade }};
                const especiais = {{ probabilidades_especificas | safe }};
                const sequencia = {{ 'true' if sequencia_detectada else 'false' }};

                if (especiais.includes(prob) || sequencia === 'true') {
                    const som = document.getElementById("som-alerta");
                    som.play().catch(err => {
                        console.log("⚠️ Navegador bloqueou o som:", err);
                    });
                    fetch('/incrementar_contador/' + prob)
                        .then(response => response.json())
                        .then(data => {
                            document.querySelector("#contador-alertas").innerText = data.contador;
                        });

                }
            </script>

            <hr>
            <div class="info">
                ✅ Direto: {{ acertos }} | ❌ Erros: {{ erros }} | 🎯 Taxa: {{ taxa_acerto }}%
            </div>
            <div class="info">📊 Ciclos — Preto: {{ preto }} | Vermelho: {{ vermelho }}</div>
            <hr>
            <div style="text-align: center; margin-top: 10px;">
                <span style="font-size: 16px; color: #cc0000;">
                    🔔 Contador de Alarmes: <strong id="contador-alertas">{{ contador_alertas }}</strong>
                </span>
            </div>
            <hr>

            {% if alertas_iminentes %}
                <div class="alerta-grande alerta-vermelho">
                    <div class="alerta-titulo">🚨 Alerta Iminente!</div>
                    <p>A seguinte sequência está prestes a se completar:</p>
                    <ul>
                        {% for alerta in alertas_iminentes %}
                            <li><strong>{{ alerta }}</strong></li>
                        {% endfor %}
                    </ul>
                </div>

                <div class="alerta-grande alerta-amarelo">
                    <div class="alerta-titulo">⚠️ Próxima sequência esperada:</div>
                    <ul>
                        {% for seq in alertas_iminentes %}
                            <li><strong>{{ seq }}</strong></li>
                        {% endfor %}
                    </ul>
                </div>
            {% endif %}

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
            'erros': 0,
            'historico_entradas': [],
            'historico_resultados': [],
            'historico_horarios': [],
            'historico_resultados_binarios': [],
            'historico_probabilidades': [],
            'historico_ciclos_preto': [],
            'historico_ciclos_vermelho': [],
            'ultima_analisada': "",
            'contador_alertas': 0,  # <-- NOVO
            'sequencias_alertadas': []  # <-- NOVO
        }, f)
    return redirect('/')

def obter_previsao():
    try:
        with open(ESTATISTICAS_FILE, 'r') as f:
            stats = json.load(f)

        global CONTADOR_ALERTAS_GLOBAL, ULTIMAS_SEQUENCIAS_ALERTADAS
        CONTADOR_ALERTAS_GLOBAL = stats.get('contador_alertas', 0)
        ULTIMAS_SEQUENCIAS_ALERTADAS = set(stats.get('sequencias_alertadas', []))


        stats.setdefault("probabilidade_anterior", None)

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

        probabilidade_nova = round((contagem[entrada_valor] / total) * 100, 2)
        probabilidade_anterior = stats.get("probabilidade_anterior")

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

                stats['historico_probabilidades'].insert(0, probabilidade_anterior)
            else:
                resultado_binario = None
                stats['historico_probabilidades'].insert(0, None)

            stats['historico_entradas'].insert(0, entrada)
            stats['historico_resultados'].insert(0, ultima_nome)
            stats['historico_horarios'].insert(0, horario_local)
            stats['historico_resultados_binarios'].insert(0, resultado_binario)
            stats['ultima_analisada'] = horario_utc

            stats.setdefault('historico_ciclos_preto', [])
            stats.setdefault('historico_ciclos_vermelho', [])
            stats['historico_ciclos_preto'].insert(0, preto)
            stats['historico_ciclos_vermelho'].insert(0, vermelho)

            stats["probabilidade_anterior"] = probabilidade_nova

        # 🚨 Verificação de sequência
                # 🚨 Verificação de sequência
        sequencia_detectada = False
        historico_probs = [p for p in stats['historico_probabilidades'] if isinstance(p, (int, float))][:10]
        alertas_encontrados = encontrar_alertas_completos(historico_probs, SEQUENCIAS_VALIDAS)

        for alerta in alertas_encontrados:
            alerta_str = str(alerta)
            if alerta_str not in ULTIMAS_SEQUENCIAS_ALERTADAS:
                CONTADOR_ALERTAS_GLOBAL += 1  # incrementa só quando for novo
                ULTIMAS_SEQUENCIAS_ALERTADAS.add(alerta_str)
                sequencia_detectada = True
        
        # 🔹 Salvar o contador e as sequências no JSON
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
            json.dump(stats, f)

        return (
            entrada, preto, vermelho, ultima_nome, probabilidade_nova,
            ultimas_10, ultimos_horarios, horario_local,
            stats['acertos'], stats['erros'],
            taxa, entradas_formatadas, stats['historico_resultados_binarios'], historico_completo,
            sequencia_detectada
        )
    except Exception as e:
        return "Erro", "Erro", 0, 0, "Indefinida", 0.0, [], [], "--:--:--", 0, 0, 0, 0, [], [], False



@app.route('/')

def home():
    entrada, preto, vermelho, ultima_nome, probabilidade, ultimas, ultimos_horarios, horario, acertos, erros, taxa_acerto, entradas, resultados, historico_completo, sequencia_detectada = obter_previsao()

    # Definindo valores que estavam ausentes
    PREVISAO = entrada  # Pode ser substituído por outro valor representativo da previsão
    PROBABILIDADE_ATUAL = probabilidade if isinstance(probabilidade, float) else (probabilidade[-1] if probabilidade else None)
    ULTIMOS_RESULTADOS = resultados[-5:] if resultados else []

    ULTIMAS_PROBABILIDADES = [p for p in json.load(open(ESTATISTICAS_FILE))['historico_probabilidades'] if isinstance(p, (int, float))][:10]
    alertas_iminentes = encontrar_alertas_completos(ULTIMAS_PROBABILIDADES, SEQUENCIAS_VALIDAS)

    global CONTADOR_ALERTAS_GLOBAL
    contador_alertas = CONTADOR_ALERTAS_GLOBAL


    return render_template_string(
        TEMPLATE,
        previsao=PREVISAO,
        prob_atual=PROBABILIDADE_ATUAL,
        ultimos_resultados=ULTIMOS_RESULTADOS,
        alertas_iminentes=alertas_iminentes,
        contador_alertas=contador_alertas,  # <-- Mantemos apenas esse
        entrada=entrada,
        preto=preto,
        vermelho=vermelho,
        ultima=ultima_nome,
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
        sequencia_detectada=sequencia_detectada
)




if __name__ == '__main__':
    app.run(debug=True)