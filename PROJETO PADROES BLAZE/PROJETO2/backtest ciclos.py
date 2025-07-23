import pandas as pd
from collections import Counter
import os
from datetime import datetime

# CONFIGURAÇÕES
CAMINHO_DESKTOP = os.path.join(os.path.expanduser("~"), "Desktop")
ARQUIVO_EXCEL = os.path.join(CAMINHO_DESKTOP, "historico blaze.xlsx")
NOME_ABA = 0

COR_MAPA = {"red": 1, "black": 2, "white": 0}
COR_TEXTO = {1: "VERMELHO", 2: "PRETO", 0: "BRANCO"}

def processar_todas_linhas(df):
    df = df.copy()
    df["Data"] = pd.to_datetime(df["Data"])
    df = df.sort_values("Data").reset_index(drop=True)
    df["CorInt"] = df["Cor"].map(COR_MAPA)

    linhas_detalhadas = []

    for i in range(100, len(df)):
        base_100 = df.iloc[i - 100:i]
        cores_base = base_100["CorInt"].tolist()
        cores_validas = [c for c in cores_base if c != 0]

        ciclos_preto = ciclos_vermelho = 0
        if cores_validas:
            atual = cores_validas[0]
            for cor in cores_validas[1:]:
                if cor != atual:
                    if atual == 1:
                        ciclos_vermelho += 1
                    elif atual == 2:
                        ciclos_preto += 1
                    atual = cor
            if atual == 1:
                ciclos_vermelho += 1
            elif atual == 2:
                ciclos_preto += 1

        previsao = 2 if ciclos_preto >= ciclos_vermelho else 1
        previsao_txt = COR_TEXTO[previsao]

        contagem = Counter(cores_validas)
        total_validas = len(cores_validas)
        prob = round((contagem[previsao] / total_validas) * 100, 2) if total_validas > 0 else 0.0

        cor_real = df.loc[i, "CorInt"]
        acertou = cor_real == previsao or cor_real == 0

        linhas_detalhadas.append({
            "Probabilidade (%)": prob,
            "Previsão": previsao_txt,
            "Ciclos Vermelho": ciclos_vermelho,
            "Ciclos Preto": ciclos_preto,
            "Acertou": "SIM" if acertou else "NÃO"
        })

    return linhas_detalhadas

def main():
    df = pd.read_excel(ARQUIVO_EXCEL, sheet_name=NOME_ABA)
    dados_detalhados = processar_todas_linhas(df)
    df_resultado = pd.DataFrame(dados_detalhados)

    agrupado = df_resultado.groupby(
        ["Probabilidade (%)", "Previsão", "Ciclos Vermelho", "Ciclos Preto"]
    ).agg(
        Total=("Acertou", "count"),
        Acertos=("Acertou", lambda x: (x == "SIM").sum()),
        Erros=("Acertou", lambda x: (x == "NÃO").sum()),
        Acerto_Porcento=("Acertou", lambda x: round((x == "SIM").sum() / len(x) * 100, 2))
    ).reset_index()

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    nome_txt = f"resultado_probabilidades_backtest_{timestamp}.txt"
    nome_xlsx = f"resultado_probabilidades_backtest_{timestamp}.xlsx"

    caminho_txt = os.path.join(CAMINHO_DESKTOP, nome_txt)
    caminho_xlsx = os.path.join(CAMINHO_DESKTOP, nome_xlsx)

    # 📄 TXT
    with open(caminho_txt, "w") as f:
        f.write(f"{'Probabilidade (%)':<18} | {'Previsão':<10} | {'Total':<6} | {'Acertos':<7} | {'Erros':<6} | {'Acerto (%)':<11} | {'Ciclos Vermelho':<16} | {'Ciclos Preto':<14}\n")
        f.write("-" * 110 + "\n")
        for _, linha in agrupado.iterrows():
            f.write(
                f"{linha['Probabilidade (%)']:<18.2f} | "
                f"{linha['Previsão']:<10} | "
                f"{int(linha['Total']):<6} | "
                f"{int(linha['Acertos']):<7} | "
                f"{int(linha['Erros']):<6} | "
                f"{linha['Acerto_Porcento']:<11.2f} | "
                f"{int(linha['Ciclos Vermelho']):<16} | "
                f"{int(linha['Ciclos Preto']):<14}\n"
            )

    # 📊 XLSX
    agrupado.to_excel(caminho_xlsx, index=False)

    print(f"\n✅ Arquivos salvos no Desktop:")
    print(f"📄 TXT : {caminho_txt}")
    print(f"📊 XLSX: {caminho_xlsx}")

if __name__ == "__main__":
    main()
