import pandas as pd
from collections import defaultdict, Counter
import os
from datetime import datetime

# CONFIGURAÇÕES
CAMINHO_DESKTOP = os.path.join(os.path.expanduser("~"), "Desktop")
ARQUIVO_EXCEL = os.path.join(CAMINHO_DESKTOP, "historico blaze teste.xlsx")
NOME_ABA = 0

COR_MAPA = {"red": 1, "black": 2, "white": 0}

def processar_todas_linhas(df):
    df = df.copy()
    df["Data"] = pd.to_datetime(df["Data"])
    df = df.sort_values("Data").reset_index(drop=True)
    df["CorInt"] = df["Cor"].map(COR_MAPA)

    # Resumo para acumular acertos e erros de cada probabilidade
    resumo = defaultdict(lambda: {"total": 0, "acertos": 0, "erros": 0})

    for i in range(100, len(df)):
        # Pega as últimas 100 jogadas
        base_100 = df.iloc[i - 100:i]
        cores_base = base_100["CorInt"].tolist()
        cores_validas = [c for c in cores_base if c != 0]

        # Calcular a previsão com base nas probabilidades
        contagem = Counter(cores_validas)
        total_validas = len(cores_validas)
        previsao = 2 if contagem[2] >= contagem[1] else 1  # 2 = preto, 1 = vermelho
        prob = round((contagem[previsao] / total_validas) * 100, 2) if total_validas > 0 else 0.0
        chave = f"{prob:.2f}"

        cor_real = df.loc[i, "CorInt"]
        acertou = cor_real == previsao or cor_real == 0

        # Acumula o total de previsões, acertos e erros para cada probabilidade
        resumo[chave]["total"] += 1
        if acertou:
            resumo[chave]["acertos"] += 1
        else:
            resumo[chave]["erros"] += 1

    # Monta a lista final de resultados detalhados
    linhas_detalhadas = []
    for chave, stats in resumo.items():
        linhas_detalhadas.append({
            "Probabilidade (%)": chave,
            "Total": stats["total"],
            "Acertos": stats["acertos"],
            "Erros": stats["erros"],
            "Acerto (%)": round(stats["acertos"] / stats["total"] * 100, 2) if stats["total"] > 0 else 0.0
        })

    return linhas_detalhadas

def main():
    # Lê o arquivo Excel
    df = pd.read_excel(ARQUIVO_EXCEL, sheet_name=NOME_ABA)
    dados_ordenados = processar_todas_linhas(df)

    # Cria um DataFrame com os dados processados
    df_resultado = pd.DataFrame(dados_ordenados)

    # Define os nomes dos arquivos de saída
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    nome_txt = f"resultado_probabilidades_backtest_{timestamp}.txt"
    nome_xlsx = f"resultado_probabilidades_backtest_{timestamp}.xlsx"

    caminho_txt = os.path.join(CAMINHO_DESKTOP, nome_txt)
    caminho_xlsx = os.path.join(CAMINHO_DESKTOP, nome_xlsx)

    # 📄 Salvar .txt com os resultados
    with open(caminho_txt, "w") as f:
        f.write(f"{'Probabilidade (%)':<18} | {'Total':<5} | {'Acertos':<7} | {'Erros':<5} | {'Acerto (%)':<11}\n")
        f.write("-" * 60 + "\n")
        for linha in dados_ordenados:
            f.write(f"{linha['Probabilidade (%)']:<18} | {linha['Total']:<5} | {linha['Acertos']:<7} | {linha['Erros']:<5} | {linha['Acerto (%)']:<11}\n")

    # 📊 Salvar .xlsx com os resultados
    df_resultado.to_excel(caminho_xlsx, index=False)

    print(f"\n✅ Arquivos salvos no Desktop:")
    print(f"📄 TXT : {caminho_txt}")
    print(f"📊 XLSX: {caminho_xlsx}")

if __name__ == "__main__":
    main()
