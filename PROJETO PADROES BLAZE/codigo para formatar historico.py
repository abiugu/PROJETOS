import pandas as pd
import os
from tkinter import Tk, filedialog
import sys
import time

def calcular_probabilidade(ultimas_cores):
    filtrado = [c for c in ultimas_cores if c != 0]
    total = len(filtrado)
    if total == 0:
        return 0.0
    pretos = filtrado.count(2)
    return round((pretos / total) * 100, 2)

def contar_ciclos(cores, cor_alvo):
    ciclos = 0
    anterior = None
    for cor in cores:
        if cor == 0:
            continue
        if cor == cor_alvo and anterior != cor_alvo:
            ciclos += 1
        anterior = cor
    return ciclos

def mostrar_progresso(atual, total, prefixo='Progresso', tamanho=40):
    porcentagem = int((atual / total) * 100)
    barra = '█' * int(tamanho * porcentagem / 100)
    espacos = ' ' * (tamanho - len(barra))
    sys.stdout.write(f'\r{prefixo}: |{barra}{espacos}| {porcentagem}% ({atual}/{total})')
    sys.stdout.flush()
    if atual == total:
        sys.stdout.write('\n')

def processar_arquivo_excel(caminho_arquivo):
    df = pd.read_excel(caminho_arquivo)

    cor_map = {"red": 1, "black": 2, "white": 0}
    df['CorMap'] = df['Cor'].map(cor_map)

    df['Red'] = df['CorMap'].apply(lambda x: 1 if x == 1 else 0)
    df['Black'] = df['CorMap'].apply(lambda x: 1 if x == 2 else 0)
    df['White'] = df['CorMap'].apply(lambda x: 1 if x == 0 else 0)

    janelas = [200, 100, 50, 25, 10]
    resultados = {f'Probabilidade {j}': [] for j in janelas}
    resultados.update({f'Ciclos PRETO {j}': [] for j in janelas})
    resultados.update({f'Ciclos VERMELHO {j}': [] for j in janelas})

    total_linhas = len(df)
    print(f"🔄 Iniciando processamento de {total_linhas} linhas...\n")

    # Loop principal com progresso
    for i in range(total_linhas):
        for j in janelas:
            cores_j = df['CorMap'].iloc[max(0, i - j):i].tolist()
            resultados[f'Probabilidade {j}'].append(calcular_probabilidade(cores_j))
            resultados[f'Ciclos PRETO {j}'].append(contar_ciclos(cores_j, 2))
            resultados[f'Ciclos VERMELHO {j}'].append(contar_ciclos(cores_j, 1))

        # Atualizar barra de progresso a cada 1%
        if i % max(1, total_linhas // 100) == 0 or i == total_linhas - 1:
            mostrar_progresso(i + 1, total_linhas, prefixo="📊 Processando")

    print("\n✅ Cálculos concluídos!\n")

    # Adicionar resultados
    for nome_coluna, valores in resultados.items():
        df[nome_coluna] = valores

    df['Combinação'] = df[['Red', 'Black', 'White']].agg('sum', axis=1).astype(str)
    combinacoes_contagem = df['Combinação'].value_counts().to_dict()

    previsoes = []
    for i in range(len(df)):
        if i == 0:
            previsoes.append("")
        else:
            if df.loc[i-1, 'Ciclos PRETO 100'] >= df.loc[i-1, 'Ciclos VERMELHO 100']:
                previsoes.append("PRETO")
            else:
                previsoes.append("VERMELHO")

    df['Previsão'] = previsoes
    df.drop(columns=['CorMap'], inplace=True)

    return df, combinacoes_contagem

def escolher_arquivo():
    root = Tk()
    root.withdraw()
    caminho = filedialog.askopenfilename(
        title="Selecione o arquivo Excel",
        filetypes=[("Excel files", "*.xlsx")]
    )
    return caminho

# Execução principal
if __name__ == "__main__":
    caminho_arquivo = escolher_arquivo()

    if caminho_arquivo and os.path.exists(caminho_arquivo):
        df_resultado, combinacoes_contagem = processar_arquivo_excel(caminho_arquivo)

        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", "saida_completa.xlsx")
        df_resultado.to_excel(desktop_path, index=False)
        print(f"💾 Arquivo salvo em: {desktop_path}\n")

        print("🧩 Contagem das combinações de cores:")
        for combinacao, contagem in combinacoes_contagem.items():
            print(f" - {combinacao}: {contagem} ocorrências")
    else:
        print("❌ Nenhum arquivo selecionado ou caminho inválido.")
