import tkinter as tk
from tkinter import filedialog
import re
import pandas as pd

def extrair_percentuais(txt_file):
    # Abrir e ler o arquivo de texto
    with open(txt_file, 'r') as file:
        conteudo = file.read()

    # Expressão regular para capturar o percentual de cada linha
    padrao = re.compile(r"(.*?):.*?Percentual de Acertos = (\d+\.\d+)%")
    
    # Buscar todas as ocorrências no conteúdo do arquivo
    resultados = padrao.findall(conteudo)

    # Criar um dicionário com as combinações e percentuais
    percentuais = {}
    for item in resultados:
        # Se a combinação de acertos for 0% (sem jogadas) ou não houver jogadas, colocar "SEM JOGADAS"
        if float(item[1]) == 0:
            percentuais[item[0]] = "0"  # Para 0%, mostrar como 0
        elif float(item[1]) == 0.0:
            percentuais[item[0]] = "SEM JOGADAS"  # Quando não há jogadas
        else:
            percentuais[item[0]] = float(item[1])

    return percentuais

def escolher_arquivos():
    # Usar tkinter para abrir o seletor de arquivos
    root = tk.Tk()
    root.withdraw()  # Ocultar a janela principal do tkinter
    
    # Abrir caixa de diálogo para escolher múltiplos arquivos .txt
    arquivos = filedialog.askopenfilenames(
        title="Selecione os arquivos",
        filetypes=(("Text files", "*.txt"), ("All files", "*.*"))
    )
    
    return arquivos

def gerar_excel_com_percentuais(arquivos):
    dados_completos = []
    combinacoes = set()

    # Extrair percentuais de cada arquivo
    for arquivo in arquivos:
        dados = extrair_percentuais(arquivo)
        dados['Arquivo'] = arquivo.split("/")[-1]  # Nome do arquivo
        dados_completos.append(dados)
        combinacoes.update(dados.keys())  # Atualiza as combinações

    # Criar DataFrame com as combinações como colunas
    df = pd.DataFrame(dados_completos)

    # Garantir que todas as combinações estejam como colunas
    for combinacao in combinacoes:
        if combinacao not in df.columns:
            df[combinacao] = None

    # Reorganizar as colunas, com as combinações como colunas
    df = df[['Arquivo'] + list(combinacoes)]

    # Salvar em um arquivo Excel
    output_file = 'percentuais_combinados.xlsx'
    df.to_excel(output_file, index=False)

    print(f"Arquivo Excel gerado com sucesso: {output_file}")

# Escolher arquivos através da interface tkinter
arquivos = escolher_arquivos()

# Gerar o Excel com os percentuais dos arquivos selecionados
gerar_excel_com_percentuais(arquivos)
