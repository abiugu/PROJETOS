import pandas as pd
import tkinter as tk
from tkinter import filedialog
import os
import unicodedata
from tqdm import tqdm  # barra de progresso

# === Abrir arquivo via Tkinter ===
def abrir_arquivo():
    root = tk.Tk()
    root.withdraw()
    arquivo = filedialog.askopenfilename(
        title="Selecione o arquivo .xlsx",
        filetypes=[("Arquivos Excel", "*.xlsx")]
    )
    return arquivo

# === Normalizar colunas ===
def normalizar_colunas(df):
    def normalizar(texto):
        texto = str(texto).strip().lower()
        texto = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('utf-8')
        texto = texto.replace(' ', '').replace('_', '')
        return texto
    df.columns = [normalizar(col) for col in df.columns]
    return df

# === Calcular assertividade e ciclos ===
def calcular_assertividade_progressiva(df, tipo='100'):
    resultados = []
    col_prob = f'probabilidade{tipo}'

    if col_prob not in df.columns:
        print(f"⚠️ Coluna {col_prob} não encontrada — pulando {tipo}.")
        return pd.DataFrame()

    tamanho_janela = int(tipo)

    for i in tqdm(range(len(df) - tamanho_janela), desc=f"🔹 Janela {tipo}", ncols=80):
        prob = df.iloc[i][col_prob]
        janela = df.iloc[i + 1:i + 1 + tamanho_janela]

        # === Calcular ciclos de preto e vermelho ===
        cores = janela['cor'].tolist()
        ciclo_preto = 0
        ciclo_vermelho = 0
        cor_anterior = None

        for cor in cores:
            if cor != cor_anterior:
                if cor == 'black':
                    ciclo_preto += 1
                elif cor == 'red':
                    ciclo_vermelho += 1
            cor_anterior = cor

        # === Calcular acertos progressivos (até 3 jogadas seguintes) ===
        proximas = janela.iloc[:3]
        acertos = {'Black': [0, 0, 0], 'Red': [0, 0, 0], 'White': [0, 0, 0]}

        for j in range(len(proximas)):
            cor_jogada = proximas.iloc[j]['cor']
            if cor_jogada.lower() in ['black', 'red', 'white']:
                for l in range(j, 3):
                    acertos[cor_jogada.title()][l] = 1

        resultados.append({
            f'Prob{tipo}': prob,
            f'Ciclo Preto {tipo}': ciclo_preto,
            f'Ciclo Vermelho {tipo}': ciclo_vermelho,
            **{f'Acertos Black {j+1}': acertos['Black'][j] for j in range(3)},
            **{f'Acertos Red {j+1}': acertos['Red'][j] for j in range(3)},
            **{f'Acertos White {j+1}': acertos['White'][j] for j in range(3)},
        })

    if not resultados:
        return pd.DataFrame()

    df_resultado = pd.DataFrame(resultados)

    # === Agrupar por probabilidade ===
    cols_black = [f'Acertos Black {i+1}' for i in range(3)]
    cols_red   = [f'Acertos Red {i+1}' for i in range(3)]
    cols_white = [f'Acertos White {i+1}' for i in range(3)]

    resumo = df_resultado.groupby(f'Prob{tipo}').agg(
        Contagem=('Prob{tipo}', 'count'),
        Media_Ciclo_Preto=(f'Ciclo Preto {tipo}', 'mean'),
        Media_Ciclo_Vermelho=(f'Ciclo Vermelho {tipo}', 'mean'),
        **{col: (col, 'sum') for col in cols_black + cols_red + cols_white}
    ).reset_index()

    # === Calcular percentuais progressivos ===
    for idx, col in enumerate(cols_black):
        resumo[f'Percentual Black {idx+1}'] = (resumo[col] / resumo['Contagem'] * 100).round(2)
    for idx, col in enumerate(cols_red):
        resumo[f'Percentual Red {idx+1}'] = (resumo[col] / resumo['Contagem'] * 100).round(2)
    for idx, col in enumerate(cols_white):
        resumo[f'Percentual White {idx+1}'] = (resumo[col] / resumo['Contagem'] * 100).round(2)

    return resumo

# === Salvar resultado no Desktop com abas separadas ===
def salvar_resultado(resumos):
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    arquivo_saida = os.path.join(desktop, "resultado_prob_completo.xlsx")

    with pd.ExcelWriter(arquivo_saida) as writer:
        for tipo, resumo in resumos.items():
            if resumo.empty:
                continue

            resumo.to_excel(writer, index=False, sheet_name=f"Resumo {tipo}")

            for cor in ['Black', 'Red', 'White']:
                cols = [f'Prob{tipo}', 'Contagem', f'Media_Ciclo_Preto', f'Media_Ciclo_Vermelho'] + \
                       [f'Acertos {cor} {i+1}' for i in range(3)] + \
                       [f'Percentual {cor} {i+1}' for i in range(3)]

                cols_existentes = [c for c in cols if c in resumo.columns]
                resumo[cols_existentes].to_excel(
                    writer, index=False, sheet_name=f'{cor} {tipo}'
                )

    print(f"\n✅ Resultado salvo com sucesso em:\n{arquivo_saida}")

# === Função principal ===
def main():
    arquivo = abrir_arquivo()
    if not arquivo:
        print("❌ Nenhum arquivo selecionado.")
        return

    df = pd.read_excel(arquivo)
    df = normalizar_colunas(df)

    tipos = ['200', '100', '50', '25']
    colunas_necessarias = ['cor'] + [f'probabilidade{t}' for t in tipos]

    for col in colunas_necessarias:
        if col not in df.columns:
            print(f"⚠️ Aviso: coluna '{col}' não encontrada.")

    resumos = {}
    for tipo in tipos:
        resumo = calcular_assertividade_progressiva(df, tipo=tipo)
        resumos[tipo] = resumo

    salvar_resultado(resumos)

if __name__ == "__main__":
    main()
