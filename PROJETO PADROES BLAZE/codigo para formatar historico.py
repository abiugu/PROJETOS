import pandas as pd
import os
from tkinter import Tk, filedialog
from collections import Counter

def calcular_probabilidade(ultimas_cores):
    filtrado = [c for c in ultimas_cores if c != 0]
    total = len(filtrado)
    if total == 0:
        return 0.0
    pretos = filtrado.count(2)  # Contagem apenas da cor preta
    return round((pretos / total) * 100, 2)

def contar_ciclos(cores, cor_alvo):
    ciclos = 0
    anterior = None
    for cor in cores:
        if cor == 0:
            continue
        if cor == cor_alvo and anterior != cor_alvo:
            ciclos += 1
        anterior = cor
    return ciclos

def processar_arquivo_excel(caminho_arquivo):
    df = pd.read_excel(caminho_arquivo)

    cor_map = {"red": 1, "black": 2, "white": 0}
    df['CorMap'] = df['Cor'].map(cor_map)

    prob_preto_100 = []
    prob_preto_50 = []
    ciclos_preto_100 = []
    ciclos_preto_50 = []
    ciclos_vermelho_100 = []
    ciclos_vermelho_50 = []

    for i in range(len(df)):
        cores_100 = df['CorMap'].iloc[max(0, i-100):i].tolist()
        cores_50 = df['CorMap'].iloc[max(0, i-50):i].tolist()

        prob_preto_100.append(calcular_probabilidade(cores_100))
        prob_preto_50.append(calcular_probabilidade(cores_50))

        ciclos_preto_100.append(contar_ciclos(cores_100, 2))
        ciclos_vermelho_100.append(contar_ciclos(cores_100, 1))
        ciclos_preto_50.append(contar_ciclos(cores_50, 2))
        ciclos_vermelho_50.append(contar_ciclos(cores_50, 1))

    df['Probabilidade 100'] = prob_preto_100
    df['Probabilidade 50'] = prob_preto_50
    df['Ciclos PRETO 100'] = ciclos_preto_100
    df['Ciclos PRETO 50'] = ciclos_preto_50
    df['Ciclos VERMELHO 100'] = ciclos_vermelho_100
    df['Ciclos VERMELHO 50'] = ciclos_vermelho_50

    # Adiciona a coluna Previsão com base na linha anterior
    previsoes = []
    for i in range(len(df)):
        if i == 0:
            previsoes.append("")  # primeira linha sem previsão anterior
        else:
            if df.loc[i-1, 'Ciclos PRETO 100'] >= df.loc[i-1, 'Ciclos VERMELHO 100']:
                previsoes.append("PRETO")
            else:
                previsoes.append("VERMELHO")

    df['Previsão'] = previsoes

    df.drop(columns=['CorMap'], inplace=True)
    return df

def escolher_arquivo():
    root = Tk()
    root.withdraw()
    caminho = filedialog.askopenfilename(title="Selecione o arquivo Excel", filetypes=[("Excel files", "*.xlsx")])
    return caminho

# Execução principal
caminho_arquivo = escolher_arquivo()

if caminho_arquivo and os.path.exists(caminho_arquivo):
    df_resultado = processar_arquivo_excel(caminho_arquivo)

    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", "saida_completa.xlsx")
    df_resultado.to_excel(desktop_path, index=False)
    print(f"✅ Arquivo salvo em: {desktop_path}")
else:
    print("❌ Nenhum arquivo selecionado ou caminho inválido.")
