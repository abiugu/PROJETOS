import pandas as pd
import tkinter as tk
from tkinter import filedialog
import numpy as np
import os
from tqdm import tqdm  # Importar tqdm

# Função para abrir o arquivo .xlsx
def abrir_arquivo():
    root = tk.Tk()
    root.withdraw()  # Ocultar a janela principal
    arquivo = filedialog.askopenfilename(title="Selecione o arquivo .xlsx", filetypes=[("Arquivos Excel", "*.xlsx")])
    return arquivo

# Carregar a planilha
def carregar_planilha(arquivo):
    # Usando pandas para ler o arquivo Excel
    return pd.read_excel(arquivo)

# Processar os dados
def processar_dados(df):
    total_linhas = len(df)

    # Agrupar pelas combinações de Probabilidade 100 e Probabilidade 50
    agrupado = df.groupby(['Probabilidade 100', 'Probabilidade 50']).size().reset_index(name='Contagem')

    # Contar as cores nas jogadas seguintes (primeira, segunda, até a décima entrada)
    for i in range(1, 11):
        df[f'Proxima Cor {i}'] = df['Cor'].shift(-i)  # Jogadas seguintes até a décima jogada

    # Contagem de acertos para cada cor nas jogadas seguintes (até 10 entradas)
    for i in range(1, 11):
        df[f'Acertos White {i}'] = (df[f'Proxima Cor {i}'] == 'white').astype(int)
        df[f'Acertos Black {i}'] = (df[f'Proxima Cor {i}'] == 'black').astype(int)
        df[f'Acertos Red {i}'] = (df[f'Proxima Cor {i}'] == 'red').astype(int)

    # Se houver acerto em uma entrada, contará nas entradas subsequentes
    for i in range(1, 10):  # Para cada jogada de 1 a 9, acumula os acertos
        for color in ['White', 'Black', 'Red']:
            df[f'Acertos {color} {i+1}'] += df[f'Acertos {color} {i}']

    # Garantir que não haja valores negativos
    for i in range(1, 11):
        for color in ['White', 'Black', 'Red']:
            df[f'Acertos {color} {i}'] = df[f'Acertos {color} {i}'].clip(upper=1)

    # Agrupar os acertos de acordo com as combinações
    acertos_white = [df.groupby(['Probabilidade 100', 'Probabilidade 50'])[f'Acertos White {i}'].sum().reset_index(name=f'Acertos White {i}') for i in range(1, 11)]
    acertos_black = [df.groupby(['Probabilidade 100', 'Probabilidade 50'])[f'Acertos Black {i}'].sum().reset_index(name=f'Acertos Black {i}') for i in range(1, 11)]
    acertos_red = [df.groupby(['Probabilidade 100', 'Probabilidade 50'])[f'Acertos Red {i}'].sum().reset_index(name=f'Acertos Red {i}') for i in range(1, 11)]

    # Combinar as informações de acertos com as contagens
    resultado = agrupado
    for i in range(1, 11):
        resultado = pd.merge(resultado, acertos_white[i-1], on=['Probabilidade 100', 'Probabilidade 50'], how='left')
        resultado = pd.merge(resultado, acertos_black[i-1], on=['Probabilidade 100', 'Probabilidade 50'], how='left')
        resultado = pd.merge(resultado, acertos_red[i-1], on=['Probabilidade 100', 'Probabilidade 50'], how='left')

    # Preencher valores nulos com 0 (caso não haja "white", "black" ou "red" nas jogadas seguintes)
    resultado = resultado.fillna(0)

    # Calcular os percentuais de acertos para até dez jogadas seguintes
    for i in range(1, 11):
        for color in ['White', 'Black', 'Red']:
            resultado[f'Percentual Acertos {color} {i}'] = ((resultado[f'Acertos {color} {i}'] / resultado['Contagem']) * 100).round(2)

    return resultado, acertos_white, acertos_black, acertos_red

# Função para salvar o arquivo no desktop com abas separadas por cor
def salvar_arquivo(resultado, acertos_white, acertos_black, acertos_red):
    # Obter o caminho do desktop
    caminho_desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
    
    # Definir o caminho completo para o novo arquivo
    arquivo_saida = os.path.join(caminho_desktop, "resultado_analisado_separado_por_cor.xlsx")
    
    # Salvar o DataFrame no arquivo .xlsx com diferentes abas para cada cor
    with pd.ExcelWriter(arquivo_saida) as writer:
        resultado.to_excel(writer, sheet_name='Resultado Geral', index=False)

        # Criar a aba "Branco" (White) e salvar os percentuais de White
        branco = pd.DataFrame()  # Inicializar o DataFrame vazio para branco
        branco['Probabilidade 100'] = resultado['Probabilidade 100']
        branco['Probabilidade 50'] = resultado['Probabilidade 50']
        branco['Contagem'] = resultado['Contagem']

        for i in range(1, 11):  # Para as 10 jogadas
            branco[f'Percentual Acertos White {i}'] = resultado[f'Percentual Acertos White {i}']

        branco.to_excel(writer, sheet_name='Branco', index=False)

        # Criar a aba "Preto" (Black) e salvar os percentuais de Black
        preto = pd.DataFrame()  # Inicializar o DataFrame vazio para preto
        preto['Probabilidade 100'] = resultado['Probabilidade 100']
        preto['Probabilidade 50'] = resultado['Probabilidade 50']
        preto['Contagem'] = resultado['Contagem']

        for i in range(1, 11):  # Para as 10 jogadas
            preto[f'Percentual Acertos Black {i}'] = resultado[f'Percentual Acertos Black {i}']

        preto.to_excel(writer, sheet_name='Preto', index=False)

        # Criar a aba "Vermelho" (Red) e salvar os percentuais de Red
        vermelho = pd.DataFrame()  # Inicializar o DataFrame vazio para vermelho
        vermelho['Probabilidade 100'] = resultado['Probabilidade 100']
        vermelho['Probabilidade 50'] = resultado['Probabilidade 50']
        vermelho['Contagem'] = resultado['Contagem']

        for i in range(1, 11):  # Para as 10 jogadas
            vermelho[f'Percentual Acertos Red {i}'] = resultado[f'Percentual Acertos Red {i}']

        vermelho.to_excel(writer, sheet_name='Vermelho', index=False)
    
    print(f"Arquivo salvo com sucesso em: {arquivo_saida}")

# Função principal para rodar o processo
def main():
    arquivo = abrir_arquivo()  # Abrir arquivo .xlsx
    df = carregar_planilha(arquivo)  # Carregar a planilha
    
    # Criar a barra de progresso no terminal
    for _ in tqdm(range(100), desc="Processando dados", unit="%", ncols=100, bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{rate_fmt}] {elapsed}"):
        pass  # Só para simular uma progressão, será removido com o real cálculo de progresso

    resultado, acertos_white, acertos_black, acertos_red = processar_dados(df)  # Processar os dados
    salvar_arquivo(resultado, acertos_white, acertos_black, acertos_red)  # Salvar o arquivo no desktop

if __name__ == "__main__":
    main()