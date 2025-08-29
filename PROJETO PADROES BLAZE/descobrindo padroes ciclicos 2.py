import pandas as pd
from tkinter import Tk, filedialog
import os
from tqdm import tqdm

def escolher_arquivo():
    root = Tk()
    root.withdraw()
    caminho = filedialog.askopenfilename(
        title="Selecione o arquivo Excel",
        filetypes=[("Excel files", "*.xlsx")]
    )
    root.quit()
    return caminho

def analisar_padroes_cores(df, min_percentual=70, intervalos=[1,5,10,15]):
    df['Data'] = pd.to_datetime(df['Data'])
    df['Dia'] = df['Data'].dt.date
    df['Hora'] = df['Data'].dt.hour
    df['Minuto'] = df['Data'].dt.minute

    # Agrupar por dia + hora + minuto
    df_minuto = df.groupby(['Dia','Hora','Minuto'])['Cor'].apply(lambda x: tuple(sorted(x.unique()))).reset_index()

    # Criar chave apenas para referência
    df_minuto['MinutoChave'] = df_minuto['Dia'].astype(str) + '-' + df_minuto['Hora'].astype(str) + '-' + df_minuto['Minuto'].astype(str)

    padroes_resultado = []

    for idx, row in tqdm(df_minuto.iterrows(), total=len(df_minuto), desc="Analisando padrões"):
        cores_atuais = row['Cor']
        dia_inicial = row['Dia']
        hora = row['Hora']
        minuto = row['Minuto']

        for intervalo in intervalos:
            df_next = df_minuto[
                (df_minuto['Dia'] > dia_inicial) &
                (df_minuto['Hora'] == hora) &
                (df_minuto['Minuto'] == minuto + intervalo)
            ]
            if df_next.empty:
                continue

            acertos = 0
            for _, next_row in df_next.iterrows():
                cores_next = next_row['Cor']
                if any(c in cores_next for c in cores_atuais):
                    acertos += 1

            total = len(df_next)
            percentual = (acertos / total) * 100 if total else 0

            if percentual >= min_percentual:
                padroes_resultado.append({
                    'MinutoChave': row['MinutoChave'],
                    'CoresAtuais': cores_atuais,
                    'IntervaloMinutos': intervalo,
                    'Acertos': acertos,
                    'Total': total,
                    'Percentual': round(percentual, 2),
                    'TipoPadrao': f'Repetição de cores no mesmo minuto após {intervalo} minutos'
                })

    return pd.DataFrame(padroes_resultado)

# --- Execução principal ---
caminho_arquivo = escolher_arquivo()
if caminho_arquivo and os.path.exists(caminho_arquivo):
    df = pd.read_excel(caminho_arquivo, engine='openpyxl')
    df_resultado = analisar_padroes_cores(df, min_percentual=70, intervalos=[1,5,10,15])

    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", "padroes_ciclicos_cores.xlsx")
    df_resultado.to_excel(desktop_path, index=False)
    print(f"✅ Análise concluída! Arquivo salvo em: {desktop_path}")
else:
    print("❌ Nenhum arquivo selecionado ou caminho inválido.")
