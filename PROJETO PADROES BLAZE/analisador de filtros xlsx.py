import pandas as pd
import itertools
from tkinter import Tk, filedialog
import os
import time
from tqdm import tqdm  # Barra de progresso

# Função para escolher o arquivo Excel
def escolher_arquivo():
    root = Tk()
    root.withdraw()  # Oculta a janela principal do Tkinter
    caminho = filedialog.askopenfilename(title="Selecione o arquivo Excel", filetypes=[("Excel files", "*.xlsx")])
    root.quit()  # Fecha o Tkinter após a escolha do arquivo
    return caminho

def processar_combinacao(comb, df):
    # Desempacotando a combinação
    p100, p50 = comb
    
    # Filtrando o DataFrame com a combinação de Probabilidade 100 e Probabilidade 50
    filtrado = df[(
        (df['Probabilidade 100'] == p100) & 
        (df['Probabilidade 50'] == p50)
    )]
    
    # Verifica se a combinação tem jogadas (ignora se não houver jogadas)
    if filtrado.empty:
        return None  # Ignora esta combinação, pois não tem jogadas

    total = len(filtrado)
    acerto_direto = filtrado['Verificação'].eq("Acerto Direto").sum()
    acerto_gale = filtrado['Verificação'].eq("Acerto Gale").sum()

    # Ignorar combinações que não têm 90% de acertos ou mais
    if (acerto_direto + acerto_gale) / total < 0.9:
        return None  # Ignora esta combinação se a assertividade for menor que 90%

    # Verifica se há mais de 1 erro consecutivo
    erros_consecutivos = 0
    for i in range(1, len(filtrado)):
        # Se ocorrer erro consecutivo, aumentamos o contador
        if filtrado['Verificação'].iloc[i] == "Erro" and filtrado['Verificação'].iloc[i-1] == "Erro":
            erros_consecutivos += 1
            if erros_consecutivos >= 1:  # Se houver 2 erros consecutivos, descartamos
                return None  # Ignora esta combinação se houver mais de 1 erro consecutivo
        else:
            erros_consecutivos = 0  # Reseta o contador de erros consecutivos

    erro = filtrado['Verificação'].eq("Erro").sum()

    perc_direto = round((acerto_direto / total) * 100, 2) if total else 0.0
    perc_gale = round((acerto_gale / total) * 100, 2) if total else 0.0
    assertividade = round(((acerto_direto + acerto_gale) / total) * 100, 2) if total else 0.0

    return {
        "Probabilidade 100": p100,
        "Probabilidade 50": p50,
        "Total Entradas": total,
        "Acertos Diretos": acerto_direto,
        "Acertos Gale": acerto_gale,
        "Erros": erro,
        "Acerto Direto (%)": perc_direto,
        "Acerto Gale (%)": perc_gale,
        "Assertividade Geral (%)": assertividade
    }


def analisar_combinacoes(df):
    combinacoes_resultado = []

    # Obtendo valores únicos para as colunas 'Probabilidade 100' e 'Probabilidade 50'
    prob_100 = df['Probabilidade 100'].dropna().unique()
    prob_50 = df['Probabilidade 50'].dropna().unique()

    # Gerando todas as combinações possíveis para 'Probabilidade 100' e 'Probabilidade 50'
    todas_combinacoes = list(itertools.product(prob_100, prob_50))

    # Barra de progresso com o número total de combinações
    with tqdm(total=len(todas_combinacoes), desc="Processando combinações", unit="combinação", ncols=100) as pbar:
        for comb in todas_combinacoes:
            result = processar_combinacao(comb, df)

            if result:
                combinacoes_resultado.append(result)

            pbar.update(1)  # Atualiza a barra de progresso após cada combinação processada

    return pd.DataFrame(combinacoes_resultado)

# Execução principal
start_time = time.time()  # Marca o início da execução

# A função de escolher o arquivo só é chamada no processo principal
caminho_arquivo = escolher_arquivo()  # Solicita ao usuário para escolher o arquivo

if caminho_arquivo and os.path.exists(caminho_arquivo):
    df = pd.read_excel(caminho_arquivo, engine="openpyxl")  # Lê o arquivo Excel
    df_resultado = analisar_combinacoes(df)  # Processa as combinações

    # Salva os resultados em um novo arquivo Excel
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", "resultado_combinacoes_prob100_prob50_90p_erro1.xlsx")
    df_resultado.to_excel(desktop_path, index=False)
    
    # Calcula e exibe o tempo de execução
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"✅ Arquivo salvo com sucesso em: {desktop_path}")
    print(f"Tempo de execução: {elapsed_time:.2f} segundos")
else:
    print("❌ Nenhum arquivo selecionado ou caminho inválido.")
