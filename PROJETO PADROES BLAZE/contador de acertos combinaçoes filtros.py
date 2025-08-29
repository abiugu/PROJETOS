import tkinter as tk
from tkinter import filedialog
import pandas as pd
import os

def open_files():
    # Abrir a janela para selecionar múltiplos arquivos
    file_paths = filedialog.askopenfilenames(filetypes=[("Excel files", "*.xlsx")])
    
    if file_paths:
        # Processar cada arquivo selecionado
        for file_path in file_paths:
            # Carregar a planilha no pandas
            df = pd.read_excel(file_path)

            # Limpar espaços extras nos nomes das colunas, se houver
            df.columns = df.columns.str.strip()
            
            # Exibir os nomes das colunas para verificar se 'Tipo de Acerto' está correto
            print("Colunas do arquivo Excel:")
            print(df.columns)
            
            # Aplicar os filtros e realizar as contagens
            process_data(df, file_path)

def process_data(df, file_path):
    # Filtrar as linhas onde a coluna "Sinalização" não esteja vazia
    df = df[df['Sinalização'].notna()]  # Ignora linhas com "Sinalização" vazia
    
    # Inicializar as contagens de acertos, erros e o total para cada filtro
    resultados = {
        "possibilidade 100 >= 50": {"acertos": 0, "erros": 0},
        "possibilidade 50 >= 50": {"acertos": 0, "erros": 0},
        "ambas as possibilidades >= 50": {"acertos": 0, "erros": 0},
        "ambas as possibilidades < 50": {"acertos": 0, "erros": 0},
        "ambas as possibilidades >= 50 e resultado PRETO": {"acertos": 0, "erros": 0},
        "possibilidade 50 >= 50 e resultado PRETO": {"acertos": 0, "erros": 0},
        "possibilidade 100 >= 50 e resultado PRETO": {"acertos": 0, "erros": 0},
        "possibilidade 100 < 50 e resultado VERMELHO": {"acertos": 0, "erros": 0},
        "possibilidade 50 < 50 e resultado VERMELHO": {"acertos": 0, "erros": 0},
        "ambas as possibilidades < 50 e resultado PRETO": {"acertos": 0, "erros": 0},
        "ambas as possibilidades < 50 e ciclos vermelho 100 >= ciclo preto 100": {"acertos": 0, "erros": 0},
        "ambas as possibilidades < 50 e ciclos vermelho 100 > ciclo preto 100": {"acertos": 0, "erros": 0},
        "ambas as possibilidades >= 50 e ciclos preto 100 >= ciclo vermelho 100": {"acertos": 0, "erros": 0},
        "ambas as possibilidades >= 50 e ciclos preto 100 > ciclo vermelho 100": {"acertos": 0, "erros": 0},
    }

    # Iterar sobre as linhas e aplicar filtros
    for _, row in df.iterrows():
        tipo_acerto = row["Tipo de Acerto"]
        possibilidade_100 = row["Probabilidade 100"]
        possibilidade_50 = row["Probabilidade 50"]
        ciclos_preto_100 = row["Ciclos Preto 100"]
        ciclos_vermelho_100 = row["Ciclos Vermelho 100"]
        resultado = row["Resultado"].lower()  # Tornar a comparação insensível a maiúsculas/minúsculas
        
        # Filtrar apenas os valores BRANCO, PRETO e VERMELHO na coluna Resultado
        if resultado not in ['branco', 'preto', 'vermelho']:
            continue  # Ignorar se o valor de Resultado não for um dos três

        # Contar acertos e erros
        acerto = False  # Inicializa como False (erro)
        if tipo_acerto.lower() == "acerto direto" or tipo_acerto.lower() == "acerto gale":
            acerto = True  # Se for acerto direto ou acerto gale, conta como acerto
        elif tipo_acerto.lower() == "erro":
            acerto = False  # Se for erro, conta como erro
        else:
            continue  # Ignora outras possíveis entradas na coluna "Tipo de Acerto" que não sejam "acerto direto", "acerto gale", ou "erro"

        # Aplicar os filtros de acordo com a combinação de possibilidade e resultado

        # Possibilidade 100 >= 50
        if possibilidade_100 >= 50:
            resultados["possibilidade 100 >= 50"]["acertos" if acerto else "erros"] += 1

        # Possibilidade 50 >= 50
        if possibilidade_50 >= 50:
            resultados["possibilidade 50 >= 50"]["acertos" if acerto else "erros"] += 1

        # Ambas as possibilidades >= 50
        if possibilidade_100 >= 50 and possibilidade_50 >= 50:
            resultados["ambas as possibilidades >= 50"]["acertos" if acerto else "erros"] += 1

        # Ambas as possibilidades < 50
        if possibilidade_100 < 50 and possibilidade_50 < 50:
            resultados["ambas as possibilidades < 50"]["acertos" if acerto else "erros"] += 1

        # Ambas as possibilidades >= 50 e resultado PRETO
        if possibilidade_100 >= 50 and possibilidade_50 >= 50 and "preto" in resultado:
            resultados["ambas as possibilidades >= 50 e resultado PRETO"]["acertos" if acerto else "erros"] += 1

        # Possibilidade 50 >= 50 e resultado PRETO
        if possibilidade_50 >= 50 and "preto" in resultado:
            resultados["possibilidade 50 >= 50 e resultado PRETO"]["acertos" if acerto else "erros"] += 1

        # Possibilidade 100 >= 50 e resultado PRETO
        if possibilidade_100 >= 50 and "preto" in resultado:
            resultados["possibilidade 100 >= 50 e resultado PRETO"]["acertos" if acerto else "erros"] += 1

        # Possibilidade 100 < 50 e resultado VERMELHO
        if possibilidade_100 < 50 and "vermelho" in resultado:
            resultados["possibilidade 100 < 50 e resultado VERMELHO"]["acertos" if acerto else "erros"] += 1

        # Possibilidade 50 < 50 e resultado VERMELHO
        if possibilidade_50 < 50 and "vermelho" in resultado:
            resultados["possibilidade 50 < 50 e resultado VERMELHO"]["acertos" if acerto else "erros"] += 1

        # Ambas as possibilidades < 50 e resultado PRETO
        if possibilidade_100 < 50 and possibilidade_50 < 50 and "preto" in resultado:
            resultados["ambas as possibilidades < 50 e resultado PRETO"]["acertos" if acerto else "erros"] += 1

        # Ambas as possibilidades < 50 e ciclos vermelho 100 >= ciclo preto 100
        if possibilidade_100 < 50 and possibilidade_50 < 50 and ciclos_vermelho_100 >= ciclos_preto_100:
            resultados["ambas as possibilidades < 50 e ciclos vermelho 100 >= ciclo preto 100"]["acertos" if acerto else "erros"] += 1

        # Ambas as possibilidades < 50 e ciclos vermelho 100 > ciclo preto 100
        if possibilidade_100 < 50 and possibilidade_50 < 50 and ciclos_vermelho_100 > ciclos_preto_100:
            resultados["ambas as possibilidades < 50 e ciclos vermelho 100 > ciclo preto 100"]["acertos" if acerto else "erros"] += 1

        # Ambas as possibilidades >= 50 e ciclos preto 100 >= ciclo vermelho 100
        if possibilidade_100 >= 50 and possibilidade_50 >= 50 and ciclos_preto_100 >= ciclos_vermelho_100:
            resultados["ambas as possibilidades >= 50 e ciclos preto 100 >= ciclo vermelho 100"]["acertos" if acerto else "erros"] += 1

        # Ambas as possibilidades >= 50 e ciclos preto 100 > ciclo vermelho 100
        if possibilidade_100 >= 50 and possibilidade_50 >= 50 and ciclos_preto_100 > ciclos_vermelho_100:
            resultados["ambas as possibilidades >= 50 e ciclos preto 100 > ciclo vermelho 100"]["acertos" if acerto else "erros"] += 1

    # Calcular o percentual de acertos para cada filtro
    for filtro, valores in resultados.items():
        total = valores["acertos"] + valores["erros"]
        percentual_acertos = (valores["acertos"] / total) * 100 if total > 0 else 0
        resultados[filtro]["percentual"] = percentual_acertos

    # Preparar o caminho do arquivo de saída
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", "Resultados padroes e modelos treinados double")
    
    # Verificar se a pasta existe, caso contrário, criar
    if not os.path.exists(desktop_path):
        os.makedirs(desktop_path)

    # Preparar o caminho do arquivo de saída
    file_name = os.path.basename(file_path).replace(".xlsx", ".txt")
    output_file = os.path.join(desktop_path, file_name)

    # Salvar os resultados em um arquivo TXT
    with open(output_file, 'w') as f:
        f.write("Resultados de Filtros:\n")
        for key, value in resultados.items():
            f.write(f"{key}: Acertos = {value['acertos']}, Erros = {value['erros']}, Percentual de Acertos = {value['percentual']:.2f}%\n")

    print(f"Resultados salvos em: {output_file}")

# Criar interface Tkinter
root = tk.Tk()
root.withdraw()  # Esconde a janela principal

# Abrir os arquivos e processar os dados
open_files()
