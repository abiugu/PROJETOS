import pandas as pd
from tkinter import Tk, filedialog
import os

# --- Função para escolher o arquivo Excel ---
def escolher_arquivo():
    root = Tk()
    root.withdraw()
    caminho = filedialog.askopenfilename(
        title="Selecione o arquivo Excel",
        filetypes=[("Excel files", "*.xlsx")]
    )
    root.quit()
    return caminho

# --- Função para analisar sequências de cores ---
def analisar_sequencias(df, min_percentual=66, sequencias=[2,3,4,5]):
    df['Data'] = pd.to_datetime(df['Data'])
    df['Hora'] = df['Data'].dt.hour
    df['Minuto'] = df['Data'].dt.minute
    df['MinutoFinal'] = df['Minuto'] % 10
    df['Dia'] = df['Data'].dt.date

    resultados = []

    for seq_len in sequencias:
        for minuto_final in range(10):
            df_min = df[df['MinutoFinal'] == minuto_final].sort_values('Data')
            cores = df_min['Cor'].unique()
            
            for cor in cores:
                df_cor = df_min[df_min['Cor'] == cor].reset_index(drop=True)
                
                total_testes = 0
                acertos = 0
                
                # Percorrer o DataFrame procurando sequências
                for i in range(len(df_cor) - seq_len):
                    seq = df_cor.iloc[i:i+seq_len]
                    # Garantir que a sequência seja realmente consecutiva
                    seq_horas = seq['Hora'].values
                    seq_minutos = seq['Minuto'].values
                    seq_dias = seq['Dia'].values
                    minutos_diferenca = (seq['Data'].iloc[-1] - seq['Data'].iloc[0]).total_seconds() / 60
                    # Verifica se as jogadas estão uniformemente distribuídas por minuto final
                    if minutos_diferenca >= (seq_len - 1)*10 - 1 and minutos_diferenca <= (seq_len - 1)*10 + 1:
                        # Próximo minuto equivalente após a sequência
                        ultimo_data = seq['Data'].iloc[-1]
                        proximo_minuto = ultimo_data + pd.Timedelta(minutes=10)
                        df_next = df[
                            (df['Dia'] == proximo_minuto.date()) &
                            (df['Hora'] == proximo_minuto.hour) &
                            (df['Minuto'] == proximo_minuto.minute) &
                            (df['Cor'] == cor)
                        ]
                        total_testes += 1
                        if not df_next.empty:
                            acertos += 1
                
                if total_testes > 0:
                    percentual = (acertos / total_testes) * 100
                    if percentual >= min_percentual:
                        resultados.append({
                            'MinutoFinal': minuto_final,
                            'Cor': cor,
                            'Sequencia': seq_len,
                            'Acertos': acertos,
                            'TotalTestes': total_testes,
                            'Percentual': round(percentual, 2),
                            'TipoPadrao': f'Sequencia de {seq_len} cores repetidas no próximo minuto equivalente'
                        })
    return pd.DataFrame(resultados)

# --- Execução principal ---
caminho_arquivo = escolher_arquivo()
if caminho_arquivo and os.path.exists(caminho_arquivo):
    df = pd.read_excel(caminho_arquivo, engine='openpyxl')
    df_resultado = analisar_sequencias(df, min_percentual=66, sequencias=[2,3,4,5])

    # Salvar resultado no desktop
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", "padroes_ciclicos_sequencias.xlsx")
    df_resultado.to_excel(desktop_path, index=False)
    print(f"✅ Análise concluída! Arquivo salvo em: {desktop_path}")
else:
    print("❌ Nenhum arquivo selecionado ou caminho inválido.")
