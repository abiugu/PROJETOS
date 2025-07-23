import pandas as pd
import os

# Caminho da planilha
caminho_arquivo = os.path.expanduser("~/Desktop/historico blaze julho.xlsx")

# Leitura do arquivo
df = pd.read_excel(caminho_arquivo)
df.columns = [col.strip().lower() for col in df.columns]
df = df[['data', 'cor']]
df.columns = ['Data', 'Cor']
df['Data'] = pd.to_datetime(df['Data'])

# Traduz as cores para números
traducao = {'black': 2, 'red': 1, 'white': 0}
df['Cor'] = df['Cor'].map(traducao)

# Ordena do mais antigo para o mais recente
df = df.sort_values(by='Data', ascending=True).reset_index(drop=True)

# Estatísticas de combinação de ciclos
estatisticas = {}

# Loop: para cada jogada a partir de 101 (100 anteriores)
for i in range(100, len(df)):  # Começa a partir da 101ª jogada (índice 100)
    janela = df.iloc[i-100:i]  # Pega as 100 jogadas anteriores
    cores = janela['Cor'].tolist()

    # Conta ciclos ignorando os brancos
    preto = vermelho = 0
    anterior = None
    for cor in cores:
        if cor == 0:
            continue
        if cor != anterior:
            if anterior == 1:
                vermelho += 1
            elif anterior == 2:
                preto += 1
            anterior = cor
    if anterior == 1:
        vermelho += 1
    elif anterior == 2:
        preto += 1

    # Faz a previsão com base nos ciclos
    previsao = 2 if preto >= vermelho else 1  # 2=PRETO, 1=VERMELHO

    # A jogada atual (101ª jogada)
    cor_real = df.at[i, 'Cor']
    if cor_real == 0:
        continue  # Ignora brancos

    resultado_nome = "PRETO" if cor_real == 2 else "VERMELHO"
    acertou = previsao == cor_real

    chave = (preto, vermelho)
    if chave not in estatisticas:
        estatisticas[chave] = {'total': 0, 'acertos': 0}

    estatisticas[chave]['total'] += 1
    if acertou:
        estatisticas[chave]['acertos'] += 1

# Monta DataFrame com o resultado
linhas = []
for (preto, vermelho), stats in estatisticas.items():
    total = stats['total']
    acertos = stats['acertos']
    percentual = round((acertos / total) * 100, 2) if total > 0 else 0
    linhas.append({
        'Ciclos Preto': preto,
        'Ciclos Vermelho': vermelho,
        'Total': total,
        'Acertos': acertos,
        'Percentual de Acerto': percentual
    })

resultado_df = pd.DataFrame(linhas)
resultado_df = resultado_df.sort_values(by='Total', ascending=False)

# Salva no desktop
caminho_saida = os.path.expanduser("~/Desktop/estatisticas_combinacoes_ciclos.xlsx")
resultado_df.to_excel(caminho_saida, index=False)

print(f"Estatísticas geradas com sucesso! Salvo em:\n{caminho_saida}")
