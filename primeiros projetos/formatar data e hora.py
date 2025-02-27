import pandas as pd
import os

# Caminho para a planilha na área de trabalho
desktop = os.path.join(os.path.expanduser("~"), "Desktop")
caminho_arquivo = os.path.join(desktop, "historico_blaze.xlsx")

# Carregar a planilha
df = pd.read_excel(caminho_arquivo)

# Verificar a coluna que contém a data (substitua 'data' pelo nome correto da coluna)
coluna_data = "data"  # Altere para o nome exato da coluna, se for diferente

# Converter o formato da data
df[coluna_data] = pd.to_datetime(df[coluna_data]).dt.strftime("%d/%m/%Y %H:%M")

# Salvar a planilha modificada
df.to_excel(caminho_arquivo, index=False)

print(f"Planilha atualizada e salva em: {caminho_arquivo}")
