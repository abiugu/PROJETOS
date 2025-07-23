import pandas as pd
import os

# Caminho para o desktop
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")

# Carregar os dados do arquivo gerado
file_path = os.path.join(desktop_path, "resultado_diferenca_brancos.xlsx")
data = pd.read_excel(file_path)

# Garantir que a coluna 'Dia' esteja no formato datetime (com data)
data['Dia'] = pd.to_datetime(data['Dia'], format='%d/%m/%Y')

# Calcular a diferença de brancos por hora (Diferença da Hora Anterior)
data['Diferença da Hora Anterior'] = data.groupby(['Dia'])['Qtd brancos'].diff()

# Calcular a diferença de brancos por dia (Diferença com Dia Anterior)
data['Diferença com Dia Anterior'] = data.groupby(['Hora'])['Qtd brancos'].diff()

# Função para calcular a assertividade de um padrão
def calcular_assertividade(padrao_coluna):
    """
    Calcular a assertividade de um padrão dado uma coluna que contém as diferenças de brancos.
    A assertividade é definida como a frequência de um padrão se repetindo.
    """
    total = len(padrao_coluna)
    padrao_count = padrao_coluna.value_counts()  # Contar quantas vezes cada valor (padrão) se repete
    assertividade = (padrao_count / total) * 100  # Calcular assertividade como porcentagem
    return assertividade

# Função para filtrar os padrões com 70% ou mais de assertividade
def filtrar_padroes_70_porcento(data, threshold=70):
    # Padrões por hora - analisando a diferença por hora
    patterns_hour = data.groupby(['Dia', 'Hora'])['Diferença da Hora Anterior'].apply(calcular_assertividade)
    
    # Padrões por dia - analisando a diferença por dia
    patterns_day = data.groupby(['Dia', 'Hora'])['Diferença com Dia Anterior'].apply(calcular_assertividade)
    
    # Filtrar os padrões que têm mais de 70% de assertividade
    hour_patterns_70 = patterns_hour[patterns_hour >= threshold]
    day_patterns_70 = patterns_day[patterns_day >= threshold]
    
    return hour_patterns_70, day_patterns_70

# Aplicar a função
hour_patterns_70, day_patterns_70 = filtrar_padroes_70_porcento(data)

# Criar o arquivo Excel para salvar ambos os dados (padrões por hora e por dia)
output_file_path = os.path.join(desktop_path, "padroes_70_porcento_brancos.xlsx")

# Salvar os resultados no arquivo Excel
with pd.ExcelWriter(output_file_path) as writer:
    hour_patterns_70.to_excel(writer, sheet_name='Padrões por Hora', header=True)
    day_patterns_70.to_excel(writer, sheet_name='Padrões por Dia', header=True)

# O arquivo será salvo diretamente no desktop
print(f"Resultados analisados e salvos em: {output_file_path}")
