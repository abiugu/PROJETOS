import pandas as pd
import os

# Dados dos padrões
dados_padroes = [
    {"Padrão": "4626", "Win Direto": 58, "Gale 1": 26, "Gale 2": 15, "Loss": 7},
    {"Padrão": "5583", "Win Direto": 5, "Gale 1": 2, "Gale 2": 0, "Loss": 0},
    {"Padrão": "2420", "Win Direto": 5, "Gale 1": 1, "Gale 2": 0, "Loss": 0},
    {"Padrão": "3800", "Win Direto": 1, "Gale 1": 1, "Gale 2": 2, "Loss": 0},
    {"Padrão": "1985", "Win Direto": 63, "Gale 1": 30, "Gale 2": 5, "Loss": 11},
    {"Padrão": "4131", "Win Direto": 3, "Gale 1": 1, "Gale 2": 0, "Loss": 0},
    {"Padrão": "2817", "Win Direto": 2, "Gale 1": 0, "Gale 2": 1, "Loss": 0},
    {"Padrão": "6398", "Win Direto": 10, "Gale 1": 1, "Gale 2": 1, "Loss": 0},
    {"Padrão": "418", "Win Direto": 2, "Gale 1": 3, "Gale 2": 0, "Loss": 0},
    {"Padrão": "7615", "Win Direto": 3, "Gale 1": 1, "Gale 2": 1, "Loss": 1},
    {"Padrão": "8992", "Win Direto": 8, "Gale 1": 2, "Gale 2": 4, "Loss": 0},
    {"Padrão": "2885", "Win Direto": 20, "Gale 1": 11, "Gale 2": 5, "Loss": 1},
    {"Padrão": "6237", "Win Direto": 5, "Gale 1": 6, "Gale 2": 0, "Loss": 2},
    {"Padrão": "6972", "Win Direto": 1, "Gale 1": 2, "Gale 2": 1, "Loss": 0},
    {"Padrão": "7", "Win Direto": 17, "Gale 1": 10, "Gale 2": 4, "Loss": 1},
    {"Padrão": "8", "Win Direto": 17, "Gale 1": 7, "Gale 2": 5, "Loss": 2},
]

# Processar os dados para adicionar os percentuais
for padrao in dados_padroes:
    total_tentativas = padrao["Win Direto"] + padrao["Gale 1"] + padrao["Gale 2"] + padrao["Loss"]
    
    # Percentual acumulado
    padrao["Percentual Acerto Direto (%)"] = (padrao["Win Direto"] / total_tentativas * 100) if total_tentativas > 0 else 0
    padrao["Percentual Acerto Gale 1 (%)"] = ((padrao["Win Direto"] + padrao["Gale 1"]) / total_tentativas * 100) if total_tentativas > 0 else 0
    padrao["Percentual Acerto Gale 2 (%)"] = ((padrao["Win Direto"] + padrao["Gale 1"] + padrao["Gale 2"]) / total_tentativas * 100) if total_tentativas > 0 else 0
    
    # Percentual de erros
    padrao["Percentual Erro (%)"] = (padrao["Loss"] / total_tentativas * 100) if total_tentativas > 0 else 0


# Criar o DataFrame
df = pd.DataFrame(dados_padroes)

# Salvar em Excel
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
arquivo_excel = os.path.join(desktop_path, "resultados_padroes.xlsx")
df.to_excel(arquivo_excel, index=False)

print(f"Planilha criada com sucesso: {arquivo_excel}")
