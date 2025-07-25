import pandas as pd
import os
from datetime import datetime
from collections import Counter

# CONFIGURAÇÕES
CAMINHO_DESKTOP = os.path.join(os.path.expanduser("~"), "Desktop")
ARQUIVO_EXCEL = os.path.join(CAMINHO_DESKTOP, "historico blaze julho.xlsx")
NOME_ABA = 0

COR_MAPA = {"red": 1, "black": 2, "white": 0}
COR_INVERSA = {1: "red", 2: "black", 0: "white"}

def analisar_sequencias_probabilidades(df):
    df = df.copy()
    df["Data"] = pd.to_datetime(df["Data"])
    df = df.sort_values("Data").reset_index(drop=True)
    df["CorInt"] = df["Cor"].map(COR_MAPA)

    resultados_detalhados = []

    for i in range(50, len(df)):
        base_100 = df.iloc[i - 50:i]
        cores_base = base_100["CorInt"].tolist()
        cores_validas = [c for c in cores_base if c != 0]

        contagem = Counter(cores_validas)
        total_validas = len(cores_validas)

        if total_validas == 0:
            continue

        previsao = 2 if contagem[2] >= contagem[1] else 1  # 2 = preto, 1 = vermelho
        prob = round((contagem[previsao] / total_validas) * 100, 2)

        cor_real = df.loc[i, "CorInt"]
        acertou = cor_real == previsao or cor_real == 0

        resultados_detalhados.append({
            "DataHora": df.loc[i, "Data"],
            "Previsão": COR_INVERSA[previsao],
            "Probabilidade (%)": prob,
            "Cor Real": COR_INVERSA[cor_real],
            "Acertou": "✅" if acertou else "❌"
        })

    return pd.DataFrame(resultados_detalhados)

def main():
    df = pd.read_excel(ARQUIVO_EXCEL, sheet_name=NOME_ABA)
    df_resultado = analisar_sequencias_probabilidades(df)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    nome_xlsx = f"sequencia_probabilidades_{timestamp}.xlsx"
    caminho_xlsx = os.path.join(CAMINHO_DESKTOP, nome_xlsx)

    df_resultado["DataHora"] = df_resultado["DataHora"].dt.tz_localize(None)
    df_resultado.to_excel(caminho_xlsx, index=False)


    print(f"\n✅ Resultado salvo no Desktop:")
    print(f"📊 {caminho_xlsx}")

if __name__ == "__main__":
    main()
