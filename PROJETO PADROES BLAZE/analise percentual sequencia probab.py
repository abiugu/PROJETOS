import pandas as pd
import os
from collections import defaultdict
from datetime import datetime

# Caminho do arquivo
CAMINHO_DESKTOP = os.path.join(os.path.expanduser("~"), "Desktop")
ARQUIVO_EXCEL = os.path.join(CAMINHO_DESKTOP, "historico probabilidades julho 50 rodadas.xlsx")

def encontrar_sequencias_probabilidade(df, tamanho_seq=3, limite_acerto=70.0):
    df = df.copy()

    # Normaliza colunas
    df.columns = df.columns.str.replace('\u00A0', ' ', regex=False).str.strip()
    df.columns = df.columns.str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')

    # Garante que as colunas necessárias existem
    if not all(col in df.columns for col in ["Probabilidade", "Acertou"]):
        print("❌ Colunas obrigatórias ('Probabilidade', 'Acertou') não encontradas.")
        print("🔍 Colunas disponíveis:", df.columns.tolist())
        return pd.DataFrame()

    # Converte probabilidades (vírgula -> ponto) e remove caracteres inválidos
    try:
        df["Probabilidade"] = (
            df["Probabilidade"]
            .astype(str)
            .str.replace(",", ".", regex=False)
            .str.replace(r"[^\d\.]", "", regex=True)
            .astype(float)
        )
    except Exception as e:
        print("❌ Erro ao converter a coluna 'Probabilidade' para float.")
        print("🔍 Primeiros valores:", df["Probabilidade"].head(10).tolist())
        print("Detalhes:", e)
        return pd.DataFrame()

    # Normaliza valores da coluna Acertou
    df["Acertou"] = df["Acertou"].astype(str).str.strip()

    # Dicionário para armazenar estatísticas das sequências
    sequencias = defaultdict(lambda: {"ocorrencias": 0, "acertos": 0})

    for i in range(len(df) - tamanho_seq):
        try:
            seq = tuple(round(df.loc[i + j, "Probabilidade"], 2) for j in range(tamanho_seq))
            proxima = df.loc[i + tamanho_seq]
            acertou = proxima["Acertou"] == "✅"
            sequencias[seq]["ocorrencias"] += 1
            if acertou:
                sequencias[seq]["acertos"] += 1
        except Exception:
            continue

    # Monta dataframe final com taxa de acerto
    resultados = []
    for seq, stats in sequencias.items():
        if stats["ocorrencias"] < 2:
            continue
        taxa_acerto = round((stats["acertos"] / stats["ocorrencias"]) * 100, 2)
        if taxa_acerto >= limite_acerto:
            resultados.append({
                "Sequência de Probabilidades": ', '.join([f"{p:.2f}" for p in seq]),
                "Ocorrências": stats["ocorrencias"],
                "Acertos": stats["acertos"],
                "Taxa de Acerto (%)": taxa_acerto
            })

    return pd.DataFrame(resultados).sort_values(by="Taxa de Acerto (%)", ascending=False)

def main():
    try:
        df = pd.read_excel(ARQUIVO_EXCEL, dtype=str)
        print(f"📥 Planilha carregada com {len(df)} linhas.")

        tamanho = int(input("📊 Digite o tamanho da sequência (ex: 2, 3, 4): "))

        resultado = encontrar_sequencias_probabilidade(df, tamanho_seq=tamanho)

        if resultado.empty:
            print("⚠️ Nenhuma sequência com acerto ≥ 70% foi encontrada.")
        else:
            nome_saida = f"sequencias_{tamanho}_acima_70_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.xlsx"
            caminho_saida = os.path.join(CAMINHO_DESKTOP, nome_saida)
            resultado.to_excel(caminho_saida, index=False)
            print(f"✅ Resultado salvo em: {caminho_saida}")

    except Exception as e:
        print("❌ Erro ao processar a planilha:")
        print(e)

if __name__ == "__main__":
    main()
