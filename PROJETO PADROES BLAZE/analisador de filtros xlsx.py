import pandas as pd
import itertools
from tkinter import Tk, filedialog
import os

def escolher_arquivo():
    root = Tk()
    root.withdraw()
    caminho = filedialog.askopenfilename(title="Selecione o arquivo Excel", filetypes=[("Excel files", "*.xlsx")])
    return caminho

def analisar_combinacoes(df):
    combinacoes_resultado = []

    previsoes = df['Previsão'].dropna().unique()
    cores = df['Cor'].dropna().unique()
    status_100 = df['status 100'].dropna().unique()
    status_50 = df['status 50'].dropna().unique()
    status_prob = df['status prob'].dropna().unique()

    todas_combinacoes = list(itertools.product(previsoes, cores, status_100, status_50, status_prob))

    for prev, cor, s100, s50, sprob in todas_combinacoes:
        filtrado = df[
            (df['Previsão'] == prev) &
            (df['Cor'] == cor) &
            (df['status 100'] == s100) &
            (df['status 50'] == s50) &
            (df['status prob'] == sprob)
        ]

        total = len(filtrado)
        acerto_direto = filtrado['Verificação'].eq("Acerto Direto").sum()
        acerto_gale = filtrado['Verificação'].eq("Acerto Gale").sum()
        erro = filtrado['Verificação'].eq("Erro").sum()

        perc_direto = round((acerto_direto / total) * 100, 2) if total else 0.0
        perc_gale = round((acerto_gale / total) * 100, 2) if total else 0.0
        assertividade = round(((acerto_direto + acerto_gale) / total) * 100, 2) if total else 0.0

        combinacoes_resultado.append({
            "Previsão": prev,
            "Cor": cor,
            "Status 100": s100,
            "Status 50": s50,
            "Status Prob": sprob,
            "Total Entradas": total,
            "Acertos Diretos": acerto_direto,
            "Acertos Gale": acerto_gale,
            "Erros": erro,
            "Acerto Direto (%)": perc_direto,
            "Acerto Gale (%)": perc_gale,
            "Assertividade Geral (%)": assertividade
        })

    return pd.DataFrame(combinacoes_resultado)

# Execução principal
caminho_arquivo = escolher_arquivo()

if caminho_arquivo and os.path.exists(caminho_arquivo):
    df = pd.read_excel(caminho_arquivo, engine="openpyxl")
    df_resultado = analisar_combinacoes(df)

    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", "resultado_combinacoes.xlsx")
    df_resultado.to_excel(desktop_path, index=False)
    print(f"✅ Arquivo salvo com sucesso em: {desktop_path}")
else:
    print("❌ Nenhum arquivo selecionado ou caminho inválido.")
