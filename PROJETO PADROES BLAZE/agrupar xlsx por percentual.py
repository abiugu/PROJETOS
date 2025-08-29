import pandas as pd
import tkinter as tk
from tkinter import filedialog
from openpyxl import load_workbook
import os
from alarms import ALARM_PROB100, ALARM_PROB50, ALARM_PROB100_PROB50

# Função para calcular o percentual das 10 últimas jogadas, agora para baixo (a partir da linha atual e considerando as 10 próximas)
def calcular_percentual_ultimas_10_alarme(df):
    df['Percentual Últimas 10'] = ''
    
    for i in range(len(df)):
        # Só calcula se houver algum alarme nesta linha
        if "Alarme" in df.at[i, 'Sinalização']:
            # Determinar os índices das próximas 10 jogadas após a linha atual
            start_idx = i + 1  # A linha atual não deve ser incluída, começa da próxima linha
            end_idx = min(i + 11, len(df))  # Garantir que não ultrapasse o final do DataFrame
            
            ultimas_10 = df.loc[start_idx:end_idx-1, 'Acertou']  # Considera as 10 linhas seguintes
            
            acertos = sum(ultimas_10 == "Sim")
            total_jogadas = len(ultimas_10)
            
            percentual = (acertos / total_jogadas * 100) if total_jogadas > 0 else 0
            df.at[i, 'Percentual Últimas 10'] = f"{percentual:.0f}%"
    
    return df

# Função para sinalizar as colunas com base nas listas de probabilidades
def sinalizar_probabilidades(df):
    # Criar a nova coluna 'Sinalização' que irá indicar a correspondência com as probabilidades
    df['Sinalização'] = ''
    
    # Verificar Probabilidade 100
    df.loc[df['Probabilidade 100'].astype(str).isin(ALARM_PROB100), 'Sinalização'] += 'Alarme Prob100; '
    
    # Verificar Probabilidade 50
    df.loc[df['Probabilidade 50'].astype(str).isin(ALARM_PROB50), 'Sinalização'] += 'Alarme Prob50; '
    
    # Verificar combinação de Probabilidade 100 e Probabilidade 50
    for prob_100, prob_50 in ALARM_PROB100_PROB50:
        df.loc[(df['Probabilidade 100'].astype(str) == prob_100) & 
               (df['Probabilidade 50'].astype(str) == prob_50), 'Sinalização'] += 'Alarme Prob100+Prob50; '
    
    # Lógica para diferenciar "Acerto Direto" e "Acerto Gale"
    df['Tipo de Acerto'] = 'Erro'  # Inicializa como erro por padrão
    for i in range(2, len(df)):
        if df.at[i-1, 'Acertou'] == "Sim":
            df.at[i, 'Tipo de Acerto'] = "Acerto Direto"
        elif df.at[i-2, 'Acertou'] == "Sim" and df.at[i-1, 'Acertou'] == "Não":
            df.at[i, 'Tipo de Acerto'] = "Acerto Gale"
    
    # Adicionar o percentual de acertos nas últimas 10 jogadas apenas para alarmes
    df = calcular_percentual_ultimas_10_alarme(df)
    
    return df

# Função para abrir diretamente o explorador de arquivos
def abrir_arquivo():
    # Abrir o explorador de arquivos para selecionar múltiplos arquivos
    file_paths = filedialog.askopenfilenames(title="Selecionar arquivos Excel", filetypes=[("Excel files", "*.xlsx")])
    
    if file_paths:
        # Processar cada arquivo
        for file_path in file_paths:
            # Carregar o arquivo Excel
            df = pd.read_excel(file_path)
            
            # Aplicar a função para sinalizar as probabilidades
            df_sinalizado = sinalizar_probabilidades(df)
            
            # Salvar as informações de cada arquivo no resumo geral
            salvar_resumo(df_sinalizado, file_path)


# Função para contar sequências de "Acerto Direto", "Acerto Gale" e "Erro"
# Função para contar sequências de "Acerto Direto", "Acerto Gale" e "Erro"
def contar_sequencias(df_sinalizado):
    acertos_seguidos_de_erro = 0
    acertos_seguidos_de_acerto_gale = 0
    acertos_seguidos_de_acerto_direto = 0
    erros_seguidos_de_erro = 0
    erros_seguidos_de_acerto_gale = 0
    erros_seguidos_de_acerto_direto = 0

    # Itera sobre o DataFrame para identificar transições entre jogadas
    for i in range(1, len(df_sinalizado)):
        # Verifica se a jogada atual é sinalizada com "Alarme"
        if "Alarme" in df_sinalizado.iloc[i]['Sinalização']:
            prev_tipo = df_sinalizado.iloc[i-1]['Tipo de Acerto']  # Tipo da jogada anterior
            tipo_atual = df_sinalizado.iloc[i]['Tipo de Acerto']     # Tipo da jogada atual

            # Contar sequências de acertos seguidos de erro
            if prev_tipo == 'Acerto Direto' and tipo_atual == 'Erro':
                acertos_seguidos_de_erro += 1
            elif prev_tipo == 'Acerto Gale' and tipo_atual == 'Erro':
                acertos_seguidos_de_erro += 1
            elif prev_tipo == 'Acerto Direto' and tipo_atual == 'Acerto Gale':
                acertos_seguidos_de_acerto_gale += 1
            elif prev_tipo == 'Acerto Direto' and tipo_atual == 'Acerto Direto':
                acertos_seguidos_de_acerto_direto += 1

            # Contar sequências de erros seguidos de erro
            if prev_tipo == 'Erro' and tipo_atual == 'Erro':
                erros_seguidos_de_erro += 1
            elif prev_tipo == 'Erro' and tipo_atual == 'Acerto Gale':
                erros_seguidos_de_acerto_gale += 1
            elif prev_tipo == 'Erro' and tipo_atual == 'Acerto Direto':
                erros_seguidos_de_acerto_direto += 1

    return acertos_seguidos_de_erro, acertos_seguidos_de_acerto_gale, acertos_seguidos_de_acerto_direto, \
           erros_seguidos_de_erro, erros_seguidos_de_acerto_gale, erros_seguidos_de_acerto_direto


# Função para salvar as informações do resumo em um arquivo de texto
def salvar_resumo(df_sinalizado, file_path):
    # Obter o diretório do arquivo original
    directory = os.path.dirname(file_path)
    
    # Nome do arquivo
    file_name = os.path.basename(file_path)
    
    # Contabilizando todos os tipos de acerto para as jogadas sinalizadas com alerta
    acertos_diretos = df_sinalizado[df_sinalizado['Sinalização'].str.contains('Alarme', na=False) & (df_sinalizado['Tipo de Acerto'] == 'Acerto Direto')].shape[0]
    acertos_gale = df_sinalizado[df_sinalizado['Sinalização'].str.contains('Alarme', na=False) & (df_sinalizado['Tipo de Acerto'] == 'Acerto Gale')].shape[0]
    erros = df_sinalizado[df_sinalizado['Sinalização'].str.contains('Alarme', na=False) & (df_sinalizado['Tipo de Acerto'] == 'Erro')].shape[0]
    
    # Contar as sequências de jogadas (acertos seguidos de erro, acertos seguidos de acerto gale, etc.)
    acertos_seguidos_de_erro, acertos_seguidos_de_acerto_gale, acertos_seguidos_de_acerto_direto, \
    erros_seguidos_de_erro, erros_seguidos_de_acerto_gale, erros_seguidos_de_acerto_direto = contar_sequencias(df_sinalizado)
    
    # Gerar texto de resumo para esse arquivo
    resumo = (f"{file_name} | Acertos Diretos: {acertos_diretos} | Acertos Gale: {acertos_gale} | Erros: {erros} | "
              f"Percentual de Acertos: {((acertos_diretos + acertos_gale) / (acertos_diretos + acertos_gale + erros) * 100):.2f}%\n"
              f"Acertos seguidos de Erro: {acertos_seguidos_de_erro}\n"
              f"Acertos seguidos de Acerto Gale: {acertos_seguidos_de_acerto_gale}\n"
              f"Acertos seguidos de Acerto Direto: {acertos_seguidos_de_acerto_direto}\n"
              f"Erros seguidos de Erro: {erros_seguidos_de_erro}\n"
              f"Erros seguidos de Acerto Gale: {erros_seguidos_de_acerto_gale}\n"
              f"Erros seguidos de Acerto Direto: {erros_seguidos_de_acerto_direto}\n")
    
    # Salvar o resumo em um arquivo .txt individual na mesma pasta dos arquivos .xlsx
    resumo_individual_path = os.path.join(directory, f"resumo_{file_name}.txt")
    
    with open(resumo_individual_path, 'w') as file:
        file.write(resumo)
        
    print(f"[INFO] Resumo salvo em: {resumo_individual_path}")
    
    # Acumular os valores para o resumo geral
    return acertos_diretos, acertos_gale, erros, acertos_seguidos_de_erro, acertos_seguidos_de_acerto_gale, \
           acertos_seguidos_de_acerto_direto, erros_seguidos_de_erro, erros_seguidos_de_acerto_gale, \
           erros_seguidos_de_acerto_direto, directory

# Função para criar o resumo geral com a soma dos valores de todos os arquivos processados
def gerar_resumo_geral(resumos):
    total_acertos_diretos = sum(resumo[0] for resumo in resumos)
    total_acertos_gale = sum(resumo[1] for resumo in resumos)
    total_erros = sum(resumo[2] for resumo in resumos)
    
    total_acertos_seguidos_de_erro = sum(resumo[3] for resumo in resumos)
    total_acertos_seguidos_de_acerto_gale = sum(resumo[4] for resumo in resumos)
    total_acertos_seguidos_de_acerto_direto = sum(resumo[5] for resumo in resumos)
    total_erros_seguidos_de_erro = sum(resumo[6] for resumo in resumos)
    total_erros_seguidos_de_acerto_gale = sum(resumo[7] for resumo in resumos)
    total_erros_seguidos_de_acerto_direto = sum(resumo[8] for resumo in resumos)
    
    resumo_geral = (f"Acertos Diretos: {total_acertos_diretos} | Acertos Gale: {total_acertos_gale} | Erros: {total_erros} | "
                    f"Percentual de Acertos: {((total_acertos_diretos + total_acertos_gale) / (total_acertos_diretos + total_acertos_gale + total_erros) * 100):.2f}%\n"
                    f"Acertos seguidos de Erro: {total_acertos_seguidos_de_erro}\n"
                    f"Acertos seguidos de Acerto Gale: {total_acertos_seguidos_de_acerto_gale}\n"
                    f"Acertos seguidos de Acerto Direto: {total_acertos_seguidos_de_acerto_direto}\n"
                    f"Erros seguidos de Erro: {total_erros_seguidos_de_erro}\n"
                    f"Erros seguidos de Acerto Gale: {total_erros_seguidos_de_acerto_gale}\n"
                    f"Erros seguidos de Acerto Direto: {total_erros_seguidos_de_acerto_direto}\n")
    
    # Salvar o resumo geral
    resumo_geral_path = os.path.join(resumos[0][-1], "resumo_geral.txt")
    with open(resumo_geral_path, 'w') as file:
        file.write(resumo_geral)
        
    print(f"[INFO] Resumo Geral salvo em: {resumo_geral_path}")

# Criar a janela do Tkinter sem a interface do usuário
root = tk.Tk()
root.withdraw()  # Esconde a janela principal

# Iniciar a lista de resumos
resumos = []

# Chama diretamente a função para abrir o explorador de arquivos
file_paths = filedialog.askopenfilenames(title="Selecionar arquivos Excel", filetypes=[("Excel files", "*.xlsx")])
for file_path in file_paths:
    # Carregar o arquivo Excel
    df = pd.read_excel(file_path)
    
    # Aplicar a função para sinalizar as probabilidades
    df_sinalizado = sinalizar_probabilidades(df)
    
    # Salvar as informações de cada arquivo no resumo geral
    resumos.append(salvar_resumo(df_sinalizado, file_path))

# Gerar o resumo geral
gerar_resumo_geral(resumos)
