import tkinter as tk
from tkinter import filedialog
import pandas as pd

# Função para calcular acertos e erros antes de cada tipo de jogada sinalizada
def contar_acertos_erros(df):
    acertos_antes_erro = 0
    erros_antes_erro = 0
    acertos_antes_acerto_direto = 0
    erros_antes_acerto_direto = 0
    acertos_antes_acerto_gale = 0
    erros_antes_acerto_gale = 0

    for i in range(len(df) - 1):  # Ajuste para não ultrapassar o limite do DataFrame
        if pd.notna(df.loc[i, 'Sinalização']):  # Verifica se a linha é uma jogada sinalizada
            tipo_acerto = df.loc[i, 'Tipo de Acerto']
            
            # Quando a jogada anterior foi um acerto
            if df.loc[i + 1, 'Acertou'] == 'Sim':  # A jogada anterior (linha abaixo) foi um acerto
                if tipo_acerto == 'Erro':
                    acertos_antes_erro += 1
                elif tipo_acerto == 'Acerto Gale':
                    acertos_antes_acerto_gale += 1
                elif tipo_acerto == 'Acerto Direto':
                    acertos_antes_acerto_direto += 1

            # Quando a jogada anterior foi um erro
            elif df.loc[i + 1, 'Acertou'] == 'Não':  # A jogada anterior (linha abaixo) foi um erro
                if tipo_acerto == 'Erro':
                    erros_antes_erro += 1
                elif tipo_acerto == 'Acerto Gale':
                    erros_antes_acerto_gale += 1
                elif tipo_acerto == 'Acerto Direto':
                    erros_antes_acerto_direto += 1

    # Retorna os resultados para o arquivo de resumo
    resultados = {
        "Acertos antes de Erro": acertos_antes_erro,
        "Erros antes de Erro": erros_antes_erro,
        "Acertos antes de Acerto Direto": acertos_antes_acerto_direto,
        "Erros antes de Acerto Direto": erros_antes_acerto_direto,
        "Acertos antes de Acerto Gale": acertos_antes_acerto_gale,
        "Erros antes de Acerto Gale": erros_antes_acerto_gale
    }
    return resultados

# Função para selecionar múltiplos arquivos .xlsx
def selecionar_arquivos():
    root = tk.Tk()
    root.withdraw()  # Oculta a janela principal do tkinter
    arquivos = filedialog.askopenfilenames(filetypes=[("Arquivos Excel", "*.xlsx")])  # Seleciona múltiplos arquivos
    return arquivos

# Função principal que lê os arquivos e cria o arquivo de resumo
def processar_arquivos():
    arquivos = selecionar_arquivos()
    resumo_geral = {
        "Acertos antes de Erro": 0,
        "Erros antes de Erro": 0,
        "Acertos antes de Acerto Direto": 0,
        "Erros antes de Acerto Direto": 0,
        "Acertos antes de Acerto Gale": 0,
        "Erros antes de Acerto Gale": 0
    }

    for arquivo in arquivos:
        df = pd.read_excel(arquivo)  # Lê o arquivo Excel
        resultados = contar_acertos_erros(df)  # Calcula os acertos e erros para o arquivo
        # Atualiza o resumo geral com os resultados do arquivo atual
        for chave in resumo_geral:
            resumo_geral[chave] += resultados[chave]

        # Salva um resumo individual em um arquivo de texto
        caminho_txt = arquivo.replace('.xlsx', '_resumo.txt')
        with open(caminho_txt, 'w') as file:
            file.write(f"Resumo de {arquivo}:\n")
            for chave, valor in resultados.items():
                file.write(f"{chave}: {valor}\n")
    
    # Salva o resumo geral em um arquivo de texto no último arquivo processado
    if arquivos:
        caminho_txt_geral = arquivos[-1].replace('.xlsx', '_resumo_geral.txt')
        with open(caminho_txt_geral, 'w') as file:
            file.write("Resumo Geral de Todos os Arquivos:\n")
            for chave, valor in resumo_geral.items():
                file.write(f"{chave}: {valor}\n")
    
    print(f"Resumo geral e individuais salvos nos arquivos de texto.")

# Executar a função principal
processar_arquivos()
