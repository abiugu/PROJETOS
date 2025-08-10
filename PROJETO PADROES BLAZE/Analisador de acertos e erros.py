import pandas as pd
import ast
from datetime import datetime
import os
from tkinter import Tk, filedialog

# Abrir seletor de múltiplos arquivos
Tk().withdraw()
arquivos_xlsx = filedialog.askopenfilenames(
    title="Selecione um ou mais arquivos XLSX",
    filetypes=[("Arquivos Excel", "*.xlsx")]
)

if not arquivos_xlsx:
    print("Nenhum arquivo selecionado.")
    exit()

# Caminhos dos arquivos txt fixos no Desktop
desktop = os.path.join(os.path.expanduser("~"), "Desktop")
txt_100_path = os.path.join(desktop, "SEQUENCIAS_VALIDAS.txt")
txt_50_path = os.path.join(desktop, "SEQUENCIAS_VALIDAS_50.txt")

# Carregar sequências como set de tuplas
def carregar_set_de_sequencias(path):
    sequencias = set()
    with open(path, "r", encoding="utf-8") as file:
        for linha in file:
            try:
                seq = ast.literal_eval(linha.strip())
                if isinstance(seq, list):
                    sequencias.add(tuple(round(float(x), 2) for x in seq))
            except:
                continue
    return sequencias

# Carregar todos os arquivos XLSX e unificar dados
dfs = []
for caminho in arquivos_xlsx:
    df = pd.read_excel(caminho)
    df = df.iloc[::-1]  # inverter leitura
    dfs.append(df)

df_total = pd.concat(dfs, ignore_index=True)

def limpar_probabilidade(valor):
    try:
        valor_limpo = str(valor).replace(',', '.').strip()
        return round(float(valor_limpo), 2)
    except:
        return None

probs_100 = [limpar_probabilidade(x) for x in df_total["Probabilidade 100"]]
probs_50 = [limpar_probabilidade(x) for x in df_total["Probabilidade 50"]]

resultados = df_total["Resultado"].tolist()
previsoes = df_total["Previsão"].tolist()
horarios = df_total["Horário"].tolist()

# Carregar sequências válidas
set_100 = carregar_set_de_sequencias(txt_100_path)
set_50 = carregar_set_de_sequencias(txt_50_path)

# Função de análise
def analisar(probabilidades, set_sequencias, tipo):
    resultados_final = []
    max_len = max(len(s) for s in set_sequencias)

    for tam in range(2, max_len + 1):
        for i in range(len(probabilidades) - tam):
            trecho = tuple(probabilidades[i:i + tam])
            if None in trecho:
                continue
            if trecho in set_sequencias:
                idx1 = i + tam
                idx2 = idx1 + 1
                if idx2 >= len(resultados):
                    continue

                jog1 = resultados[idx1]
                jog2 = resultados[idx2]
                prev1 = previsoes[idx1]
                prev2 = previsoes[idx2]
                hora = horarios[idx1]

                if jog1 == prev1 or jog1 == "BRANCO":
                    resultado = "Acerto Direto"
                elif jog2 == prev2 or jog2 == "BRANCO":
                    resultado = "Acerto Gale"
                else:
                    resultado = "Erro"

                resultados_final.append({
                    "Linha": i,
                    "Tipo": tipo,
                    "Sequência Detectada": list(trecho),
                    "Horário da Jogada": hora,
                    "Previsão J1": prev1,
                    "Resultado J1": jog1,
                    "Previsão J2": prev2,
                    "Resultado J2": jog2,
                    "Resultado Final": resultado
                })
    return resultados_final

# Executar análise
analise_100 = analisar(probs_100, set_100, "100")
analise_50 = analisar(probs_50, set_50, "50")
todos_resultados = analise_100 + analise_50

# Criar nomes dos arquivos com data e hora
agora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
nome_excel = f"analise_resultados_sequencias_{agora}.xlsx"
nome_txt = f"resultado_analise_sequencias_{agora}.txt"

# Salvar Excel
df_resultado = pd.DataFrame(todos_resultados)
saida_excel = os.path.join(desktop, nome_excel)
df_resultado.to_excel(saida_excel, index=False)

# Mensagens finais
print(f"[✔] Análise concluída com sucesso!")
print(f"[✔] Excel salvo em: {saida_excel}")
