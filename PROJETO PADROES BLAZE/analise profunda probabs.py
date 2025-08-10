import pandas as pd
import ast
import tkinter
from tkinter import filedialog
from datetime import datetime
from pathlib import Path

CASAS_DECIMAIS = 2

def selecionar_arquivo_xlsx(titulo="Selecione a planilha .xlsx"):
    import matplotlib
    matplotlib.use('TkAgg')
    root = tkinter.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    caminho = filedialog.askopenfilename(title=titulo, filetypes=[("Excel files", "*.xlsx")])
    return caminho

def selecionar_arquivo_txt(titulo="Selecione o arquivo de sequências válidas"):
    import matplotlib
    matplotlib.use('TkAgg')
    root = tkinter.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    caminho = filedialog.askopenfilename(title=titulo, filetypes=[("Text files", "*.txt")])
    return caminho

def carregar_sequencias(path_txt):
    sequencias = set()
    with open(path_txt, "r", encoding="utf-8") as f:
        for linha in f:
            try:
                seq = ast.literal_eval(linha.strip())
                if isinstance(seq, list):
                    sequencias.add(tuple(round(float(n), CASAS_DECIMAIS) for n in seq))
            except:
                continue
    return sequencias

def detectar_sequencias(prob_list, sequencias_validas):
    max_len = max(len(s) for s in sequencias_validas)
    resultados = []

    prob_list = [round(float(x), CASAS_DECIMAIS) for x in prob_list if not pd.isna(x)]

    for tam in range(2, max_len + 1):
        for i in range(len(prob_list) - tam - 2):
            trecho = tuple(prob_list[i:i+tam])
            if trecho in sequencias_validas:
                resultados.append({
                    "Sequência": trecho,
                    "Tamanho": tam,
                    "Índice": i
                })
    return resultados

def avaliar_ocorrencias(df, sequencias_detectadas):
    previsoes = df["Previsão"].tolist()
    resultados = df["Cor Real"].tolist()
    horarios = df["DataHora"].tolist()
    probabilidades = df["Probabilidade"].tolist()

    ocorrencias = []
    ultima_ocorrencia = {}

    for det in sequencias_detectadas:
        idx_seq_start = det["Índice"]
        idx1 = idx_seq_start + det["Tamanho"]
        idx2 = idx1 + 1
        if idx2 >= len(resultados):
            continue

        seq = det["Sequência"]
        prev1 = previsoes[idx1]
        res1 = resultados[idx1]
        prev2 = previsoes[idx2]
        res2 = resultados[idx2]
        hora = horarios[idx1]

        if res1 == prev1 or res1 == "white":
            resultado_final = "Acerto Direto"
        elif res2 == prev2 or res2 == "white":
            resultado_final = "Acerto Gale"
        else:
            resultado_final = "Erro"

        # Resultado da última jogada da sequência
        ult_prev = previsoes[idx_seq_start + det["Tamanho"] - 1]
        ult_real = resultados[idx_seq_start + det["Tamanho"] - 1]
        ult_status = "Acertou" if ult_prev == ult_real or ult_real == "white" else "Errou"

        # Resultado da última vez que a mesma sequência apareceu
        resultado_anterior = ultima_ocorrencia.get(seq, "Primeira vez")
        ultima_ocorrencia[seq] = resultado_final

        ocorrencias.append({
            "Sequência": seq,
            "Tamanho": det["Tamanho"],
            "Horário": hora,
            "Previsão J1": prev1,
            "Resultado J1": res1,
            "Previsão J2": prev2,
            "Resultado J2": res2,
            "Resultado Final": resultado_final,
            "Última Jogada da Sequência": ult_status,
            "Resultado da Última Ocorrência da Mesma Sequência": resultado_anterior
        })

    return pd.DataFrame(ocorrencias)

# === EXECUÇÃO PRINCIPAL ===
print("🟡 Selecione a planilha de histórico (XLSX)...")
xlsx_path = selecionar_arquivo_xlsx()

print("🟡 Selecione o arquivo de sequências válidas (TXT)...")
sequencias_path = selecionar_arquivo_txt()

if not xlsx_path or not sequencias_path:
    print("❌ Cancelado pelo usuário.")
else:
    print("🔄 Processando...")

    df = pd.read_excel(xlsx_path)
    sequencias = carregar_sequencias(sequencias_path)
    sequencias_detectadas = detectar_sequencias(df["Probabilidade"].tolist(), sequencias)
    df_resultado = avaliar_ocorrencias(df, sequencias_detectadas)

    desktop = Path.home() / "Desktop"
    agora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    nome_saida = desktop / f"resultado_avaliacao_sequencias_{agora}.xlsx"
    df_resultado.to_excel(nome_saida, index=False)

    print(f"✅ Análise concluída com sucesso!")
    print(f"📁 Arquivo salvo como: {nome_saida}")
