import pandas as pd
import os

# Caminho para a planilha na área de trabalho
desktop = os.path.join(os.path.expanduser("~"), "Desktop")
caminho_arquivo = os.path.join(desktop, "historico blaze.xlsx")

# Carregar a planilha
df = pd.read_excel(caminho_arquivo)

# Nome da coluna que contém a data (verifique se é 'data' mesmo)
coluna_data = "data"

# Converter para datetime corretamente
df[coluna_data] = pd.to_datetime(df[coluna_data], format="%Y-%m-%dT%H:%M:%S.%fZ", errors="coerce")

# Remover valores inválidos (caso tenha erro na conversão)
df = df.dropna(subset=[coluna_data])

# Ajustar para o formato correto sem fuso horário
df[coluna_data] = df[coluna_data].dt.strftime("%d/%m/%Y %H:%M:%S")

# Salvar a planilha modificada
novo_caminho = os.path.join(desktop, "historico blaze corrigido.xlsx")
df.to_excel(novo_caminho, index=False)

print(f"Planilha corrigida e salva em: {novo_caminho}")
