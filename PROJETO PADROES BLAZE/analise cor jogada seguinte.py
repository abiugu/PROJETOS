import os
import pandas as pd

# Função para analisar o arquivo XLSX
def analisar_probabilidades(file_path):
    # Carregar a planilha
    df = pd.read_excel(file_path, engine='openpyxl')

    # Filtrando as colunas relevantes
    df = df[['DataHora', 'Previsão', 'Probabilidade', 'Cor Real', 'Acertou']]

    # Inicializar dicionário para contar acertos e totais
    resultados = {}

    for i in range(len(df) - 1):  # Loop até o penúltimo valor
        prob_atual = df.iloc[i]['Probabilidade']
        cor_atual = df.iloc[i]['Cor Real']
        cor_seguinte = df.iloc[i + 1]['Cor Real']
        
        if prob_atual not in resultados:
            resultados[prob_atual] = {'total': 0, 'acertos': 0}

        resultados[prob_atual]['total'] += 1
        # Verifica se a cor da linha seguinte é a mesma que a da linha atual
        if cor_atual == cor_seguinte or cor_seguinte == 'white':
            resultados[prob_atual]['acertos'] += 1

    # Preparar os dados para salvar em um DataFrame
    dados = []
    for probabilidade, resultado in resultados.items():
        assertividade = (resultado['acertos'] / resultado['total']) * 100
        dados.append({
            'Probabilidade': probabilidade,
            'Total de Aparições': resultado['total'],
            'Total de Repetições da Cor': resultado['acertos'],
            'Percentual de Repetição (%)': assertividade
        })

    # Criar um DataFrame com os resultados
    df_resultados = pd.DataFrame(dados)

    # Caminho para salvar o arquivo
    output_dir = os.path.dirname(file_path)
    output_file = os.path.join(output_dir, 'resultados probabilidades 100 rodadas mesma cor.xlsx')
    
    # Salvar os resultados no arquivo Excel
    df_resultados.to_excel(output_file, index=False)

    print(f"Resultados salvos em: {output_file}")

# Caminho para o arquivo XLSX no Desktop
file_path = os.path.expanduser("~/Desktop/historico probabilidades julho.xlsx")

# Verifica se o arquivo existe
if os.path.exists(file_path):
    # Analisar o arquivo
    analisar_probabilidades(file_path)
else:
    print(f"Arquivo não encontrado: {file_path}")
