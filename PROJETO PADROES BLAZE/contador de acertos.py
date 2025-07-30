import pandas as pd
import re
import os
from datetime import datetime

# === 1. Caminhos dos arquivos na Área de Trabalho ===
desktop = os.path.join(os.path.expanduser("~"), "Desktop")
xlsx_path = os.path.join(desktop, "historico_completo_2025-07-27.xlsx")
txt_path = os.path.join(desktop, "sequencias_alertadas.txt")
saida_path = os.path.join(desktop, "historico_resultado_final.xlsx")

# === 2. Carregar planilha Excel ===
df = pd.read_excel(xlsx_path)
df["Horário"] = pd.to_datetime(df["Horário"], format="%H:%M:%S").dt.time

# Colunas com os valores para identificar sequências
valores_100 = df["Probabilidade 100"].round(2).tolist()
valores_50 = df["Probabilidade 50"].round(2).tolist()

# === 3. Ler e extrair sequências do arquivo TXT ===
with open(txt_path, "r", encoding="ISO-8859-1") as f:
    linhas = f.readlines()

sequencias_extraidas = []
for linha in linhas:
    seq_match = re.search(r"Sequência: \[(.*?)\]", linha)
    hora_match = re.search(r"Hora: (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", linha)
    previsao_match = re.search(r"Previsão: (PRETO|VERMELHO)", linha)

    if seq_match and hora_match and previsao_match:
        valores = [round(float(n), 2) for n in seq_match.group(1).split(",")]
        hora = datetime.strptime(hora_match.group(1), "%Y-%m-%d %H:%M:%S").time()
        previsao = previsao_match.group(1)
        sequencias_extraidas.append((valores, hora, previsao))

# ✅ Inverter a ordem: processar da mais antiga para a mais recente
sequencias_extraidas.reverse()

# === 4. Marcar resultado da próxima jogada após cada sequência ===
df["Resultado Seguinte"] = ""

for seq, hora, previsao in sequencias_extraidas:
    tam = len(seq)
    marcado = False

    # Procurar na coluna "Probabilidade 100"
    for i in range(len(valores_100) - tam):
        if valores_100[i:i + tam] == seq:
            idx_resultado = i + tam
            if idx_resultado < len(df):
                cor_real = df.iloc[idx_resultado]["Resultado"]
                acerto = "Acerto" if cor_real == previsao or (cor_real == "BRANCO" and previsao == "PRETO") else "Erro"
                df.at[idx_resultado, "Resultado Seguinte"] = f"{acerto} (100)"
                marcado = True
            break

    # Se não foi marcada no 100, procurar na "Probabilidade 50"
    if not marcado:
        for i in range(len(valores_50) - tam):
            if valores_50[i:i + tam] == seq:
                idx_resultado = i + tam
                if idx_resultado < len(df):
                    cor_real = df.iloc[idx_resultado]["Resultado"]
                    acerto = "Acerto" if cor_real == previsao or (cor_real == "BRANCO" and previsao == "PRETO") else "Erro"
                    df.at[idx_resultado, "Resultado Seguinte"] = f"{acerto} (50)"
                break

# === 5. Salvar resultado no Excel final na Área de Trabalho ===
with pd.ExcelWriter(saida_path, engine="openpyxl") as writer:
    df.to_excel(writer, sheet_name="Com Resultados", index=False)

print(f"✅ Finalizado! Arquivo gerado: {saida_path}")
