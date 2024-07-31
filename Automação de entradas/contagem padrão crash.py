import os
import re
from datetime import datetime
from collections import defaultdict
from openpyxl import Workbook
from openpyxl.utils import get_column_letter

# Função para ler o arquivo e extrair os dados
def ler_arquivo(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        linhas = file.readlines()
    return linhas

# Função para extrair os dados da linha
def extrair_dados(linha):
    pattern = r'Multiplicador: ([\d,\.]+) x - (\d{2}/\d{2}/\d{4}) \| (\d{2}:\d{2}:\d{2})'
    match = re.match(pattern, linha.strip())
    if match:
        try:
            multiplicador_str = match.group(1).replace('.', '').replace(',', '.')
            multiplicador = float(multiplicador_str)
            data = datetime.strptime(f"{match.group(2)} {match.group(3)}", '%d/%m/%Y %H:%M:%S')
            return multiplicador, data
        except ValueError:
            print(f"Erro ao converter multiplicador: {match.group(1)}")
            return None, None
    return None, None

# Função para analisar os dados e encontrar padrões
def analisar_dados(dados):
    multiplicadores = [dado[0] for dado in dados if dado[0] is not None]
    ocorrencias = len(multiplicadores)
    acima_de_2 = [m for m in multiplicadores if m > 2.00]
    total_acima_de_2 = len(acima_de_2)
    
    padroes_3 = defaultdict(lambda: {'total': 0, 'acima_2': 0})
    padroes_2 = defaultdict(lambda: {'total': 0, 'acima_2': 0})
    padroes_1 = defaultdict(lambda: {'total': 0, 'acima_2': 0})
    
    for i in range(3, len(multiplicadores)):
        padrao_3 = tuple(multiplicadores[i-3:i])
        padrao_2 = tuple(multiplicadores[i-2:i])
        padrao_1 = tuple(multiplicadores[i-1:i])
        
        padroes_3[padrao_3]['total'] += 1
        padroes_2[padrao_2]['total'] += 1
        padroes_1[padrao_1]['total'] += 1
        
        if multiplicadores[i] > 2.00:
            padroes_3[padrao_3]['acima_2'] += 1
            padroes_2[padrao_2]['acima_2'] += 1
            padroes_1[padrao_1]['acima_2'] += 1
    
    # Calcular a assertividade de cada padrão
    padroes_3 = {padrao: {'assertividade': (info['acima_2'] / info['total']) * 100 if info['total'] > 0 else 0, 'total': info['total'], 'acima_2': info['acima_2']} for padrao, info in padroes_3.items()}
    padroes_2 = {padrao: {'assertividade': (info['acima_2'] / info['total']) * 100 if info['total'] > 0 else 0, 'total': info['total'], 'acima_2': info['acima_2']} for padrao, info in padroes_2.items()}
    padroes_1 = {padrao: {'assertividade': (info['acima_2'] / info['total']) * 100 if info['total'] > 0 else 0, 'total': info['total'], 'acima_2': info['acima_2']} for padrao, info in padroes_1.items()}
    
    # Ordenar os padrões por porcentagem de assertividade em ordem decrescente
    padroes_3 = dict(sorted(padroes_3.items(), key=lambda item: item[1]['assertividade'], reverse=True))
    padroes_2 = dict(sorted(padroes_2.items(), key=lambda item: item[1]['assertividade'], reverse=True))
    padroes_1 = dict(sorted(padroes_1.items(), key=lambda item: item[1]['assertividade'], reverse=True))
    
    # Preparar os dados para a planilha Excel
    resultados = []
    
    # Adicionar os padrões de 3 anteriores
    resultados.append(["Padrão de 3 anteriores", "Quantidade Vista", "Quantidade de Acertos", "% de Assertividade"])
    for padrao, info in padroes_3.items():
        resultados.append([str(padrao), info['total'], info['acima_2'], f"{info['assertividade']:.2f}%"])
    
    # Espaço em branco
    resultados.append([])
    
    # Adicionar os padrões de 2 anteriores
    resultados.append(["Padrão de 2 anteriores", "Quantidade Vista", "Quantidade de Acertos", "% de Assertividade"])
    for padrao, info in padroes_2.items():
        resultados.append([str(padrao), info['total'], info['acima_2'], f"{info['assertividade']:.2f}%"])
    
    # Espaço em branco
    resultados.append([])
    
    # Adicionar os padrões de 1 anterior
    resultados.append(["Padrão de 1 anterior", "Quantidade Vista", "Quantidade de Acertos", "% de Assertividade"])
    for padrao, info in padroes_1.items():
        resultados.append([str(padrao), info['total'], info['acima_2'], f"{info['assertividade']:.2f}%"])
    
    # Espaço em branco
    resultados.append([])
    
    # Adicionar os top 3 padrões mais assertivos de cada tipo
    resultados.append(["Top 3 padrões mais assertivos de 3 anteriores", "", "", ""])
    top_3_padroes_3 = list(padroes_3.items())[:3]
    for padrao, info in top_3_padroes_3:
        resultados.append([str(padrao), info['total'], info['acima_2'], f"{info['assertividade']:.2f}%"])
    
    # Espaço em branco
    resultados.append([])
    
    resultados.append(["Top 3 padrões mais assertivos de 2 anteriores", "", "", ""])
    top_3_padroes_2 = list(padroes_2.items())[:3]
    for padrao, info in top_3_padroes_2:
        resultados.append([str(padrao), info['total'], info['acima_2'], f"{info['assertividade']:.2f}%"])
    
    # Espaço em branco
    resultados.append([])
    
    resultados.append(["Top 3 padrões mais assertivos de 1 anterior", "", "", ""])
    top_3_padroes_1 = list(padroes_1.items())[:3]
    for padrao, info in top_3_padroes_1:
        resultados.append([str(padrao), info['total'], info['acima_2'], f"{info['assertividade']:.2f}%"])
    
    return resultados

# Função para salvar os resultados em um arquivo Excel
def salvar_resultados_excel(resultados, filepath):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Resultados de Análise"
    
    for linha in resultados:
        sheet.append(linha)
    
    # Ajustar a largura das colunas
    for col in sheet.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(cell.value)
            except:
                pass
        adjusted_width = (max_length + 2)
        sheet.column_dimensions[column].width = adjusted_width
    
    workbook.save(filepath)
    print(f"Resultados salvos em: {filepath}")

# Função principal
def main():
    # Constrói o caminho para o arquivo na área de trabalho do usuário
    desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
    input_filepath = os.path.join(desktop, 'resultados_bets.txt')
    output_filepath = os.path.join(desktop, 'resultados_analise.xlsx')
    
    # Verifica se o arquivo de entrada existe
    if not os.path.isfile(input_filepath):
        print(f"O arquivo {input_filepath} não foi encontrado.")
        return
    
    linhas = ler_arquivo(input_filepath)
    dados = [extrair_dados(linha) for linha in linhas]
    resultados = analisar_dados(dados)
    
    # Salvar os resultados em um arquivo Excel
    salvar_resultados_excel(resultados, output_filepath)

if __name__ == "__main__":
    main()
