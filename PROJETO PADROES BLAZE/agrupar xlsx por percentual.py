import pandas as pd
import tkinter as tk
from tkinter import filedialog
import os

# Função para calcular o percentual de acertos e erros agrupado por "Percentual Últimas 10"
def calcular_acertos_erro_por_percentual(df):
    # Agrupar pelos valores únicos da coluna "Percentual Últimas 10"
    grupos = df.groupby('Percentual Últimas 10')['Acertou'].value_counts(normalize=False).unstack(fill_value=0)
    
    # Calcular os percentuais de acertos e erros por "Percentual Últimas 10"
    acertos_por_percentual = grupos.get('Sim', 0)
    erros_por_percentual = grupos.get('Não', 0)
    
    total_previsoes = acertos_por_percentual + erros_por_percentual
    acertos_percentual = (acertos_por_percentual / total_previsoes) * 100 if total_previsoes.all() else 0
    erros_percentual = (erros_por_percentual / total_previsoes) * 100 if total_previsoes.all() else 0
    
    return pd.DataFrame({
        'Percentual Últimas 10': acertos_por_percentual.index,
        'Acertos (Total)': acertos_por_percentual.values,
        'Erros (Total)': erros_por_percentual.values,
        'Acertos (%)': acertos_percentual.values,
        'Erros (%)': erros_percentual.values
    })

# Função para abrir uma janela de seleção de arquivos e retornar os arquivos selecionados
def selecionar_arquivos():
    root = tk.Tk()
    root.withdraw()  # Oculta a janela principal
    arquivos = filedialog.askopenfilenames(
        title="Selecione os arquivos Excel",
        filetypes=[("Arquivos Excel", "*.xlsx")]
    )
    return arquivos

# Função para processar múltiplos arquivos, agrupar resultados e calcular os percentuais
def processar_arquivos():
    arquivos = selecionar_arquivos()
    if not arquivos:
        print("Nenhum arquivo selecionado.")
        return
    
    # DataFrame para acumular todos os resultados
    resultado_acumulado = pd.DataFrame(columns=['Percentual Últimas 10', 'Acertos (Total)', 'Erros (Total)', 'Acertos (%)', 'Erros (%)'])

    for arquivo in arquivos:
        print(f"Processando o arquivo: {arquivo}")
        df = pd.read_excel(arquivo, sheet_name='Sheet1')  # Carregar a planilha
        resultado = calcular_acertos_erro_por_percentual(df)  # Calcular os percentuais
        resultado_acumulado = pd.concat([resultado_acumulado, resultado], ignore_index=True)
    
    # Agrupar os resultados acumulados por "Percentual Últimas 10"
    resultado_final = resultado_acumulado.groupby('Percentual Últimas 10', as_index=False).agg({
        'Acertos (Total)': 'sum',
        'Erros (Total)': 'sum',
        'Acertos (%)': 'mean',
        'Erros (%)': 'mean'
    })
    
    # Caminho para salvar o arquivo Excel na área de trabalho
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    output_file = os.path.join(desktop_path, "resultado_agrupado_com_totais.xlsx")
    
    # Salvar o DataFrame no arquivo Excel
    resultado_final.to_excel(output_file, index=False)
    
    print(f"\nResultado Agrupado salvo em: {output_file}")
    print("-" * 50)

# Chamar a função para processar os arquivos
processar_arquivos()
