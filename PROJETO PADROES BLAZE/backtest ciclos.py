import pandas as pd
from collections import defaultdict, Counter
import os
from datetime import datetime

# CONFIGURAÇÕES
CAMINHO_DESKTOP = os.path.join(os.path.expanduser("~"), "Desktop")
ARQUIVO_EXCEL = os.path.join(CAMINHO_DESKTOP, "historico blaze.xlsx")
NOME_ABA = 0

COR_MAPA = {"red": 1, "black": 2, "white": 0}

def processar_todas_linhas(df):
    df = df.copy()
    df["Data"] = pd.to_datetime(df["Data"])
    df = df.sort_values("Data").reset_index(drop=True)
    df["CorInt"] = df["Cor"].map(COR_MAPA)

    resumo = defaultdict(lambda: {"total": 0, "acertos": 0, "erros": 0})

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

        entrada_valor = 2 if ciclos_preto >= ciclos_vermelho else 1
        contagem = Counter(cores_validas)
        total_validas = len(cores_validas)
        prob = round((contagem[entrada_valor] / total_validas) * 100, 2) if total_validas > 0 else 0.0
        chave = f"{prob:.2f}"

        cor_real = df.loc[i, "CorInt"]
        acertou = cor_real == entrada_valor or cor_real == 0

        resumo[chave]["total"] += 1
        if acertou:
            resumo[chave]["acertos"] += 1
        else:
            resumo[chave]["erros"] += 1

    return resumo

def main():
    df = pd.read_excel(ARQUIVO_EXCEL, sheet_name=NOME_ABA)
    resumo_total = processar_todas_linhas(df)

    dados_ordenados = []
    for prob in sorted(resumo_total.keys(), key=lambda x: float(x)):
        total = resumo_total[prob]["total"]
        acertos = resumo_total[prob]["acertos"]
        erros = resumo_total[prob]["erros"]
        taxa = round(acertos / total * 100, 2) if total > 0 else 0.0
        dados_ordenados.append({
            "Probabilidade (%)": prob,
            "Total": total,
            "Acertos": acertos,
            "Erros": erros,
            "Acerto (%)": taxa
        })

    df_resultado = pd.DataFrame(dados_ordenados)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    nome_txt = f"resultado_probabilidades_backtest_{timestamp}.txt"
    nome_xlsx = f"resultado_probabilidades_backtest_{timestamp}.xlsx"

    caminho_txt = os.path.join(CAMINHO_DESKTOP, nome_txt)
    caminho_xlsx = os.path.join(CAMINHO_DESKTOP, nome_xlsx)

    with open(caminho_txt, "w") as f:
        f.write(f"{'Probabilidade (%)':<18} | {'Total':<5} | {'Acertos':<7} | {'Erros':<5} | {'Acerto (%)':<11}\n")
        f.write("-" * 60 + "\n")
        for linha in dados_ordenados:
            f.write(f"{linha['Probabilidade (%)']:<18} | {linha['Total']:<5} | {linha['Acertos']:<7} | {linha['Erros']:<5} | {linha['Acerto (%)']:<11}\n")

    df_resultado.to_excel(caminho_xlsx, index=False)

    print(f"\n✅ Arquivos salvos no Desktop:")
    print(f"📄 TXT : {caminho_txt}")
    print(f"📊 XLSX: {caminho_xlsx}")

if __name__ == "__main__":
    main()
