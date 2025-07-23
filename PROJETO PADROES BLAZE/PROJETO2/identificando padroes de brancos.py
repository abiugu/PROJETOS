import os
import pandas as pd

# Caminho para o desktop
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")

# Carregar os dados do arquivo gerado
file_path = os.path.join(desktop_path, "contagem_branco_por_dia_hora.xlsx")
contagem_data = pd.read_excel(file_path)

# Garantir que a coluna 'Dia' esteja em formato datetime
contagem_data['Dia'] = pd.to_datetime(contagem_data['Dia'])

# Ordenar os dados por 'Dia' e 'Hora'
contagem_data.sort_values(by=['Dia', 'Hora'], inplace=True)

# Inicializar um dicionário para armazenar os padrões
patterns = []

# Função para analisar padrões de quantidade de brancos
def analyze_patterns(data, threshold=0.8):
    for hour in range(24):  # Para cada hora (de 0 a 23)
        for quantity in range(0, data['Quantidade'].max() + 1):  # Para cada quantidade possível de brancos
            # Filtrar os dados onde a quantidade de brancos nesta hora é igual a 'quantity'
            filtered_data = data[data['Hora'] == hour]
            filtered_data = filtered_data[filtered_data['Quantidade'] == quantity]
            
            if len(filtered_data) > 0:
                # Para cada dia, verificar se o padrão se repete no dia seguinte
                next_day_data = data[data['Hora'] == hour]
                next_day_data = next_day_data[next_day_data['Dia'].shift(-1) == next_day_data['Dia']]  # Próximo dia
                
                # Verificar quantas vezes o padrão se mantém
                pattern_count = len(next_day_data)
                
                if pattern_count / len(filtered_data) > threshold:
                    patterns.append({
                        'Padrão': f'Quantidade de {quantity} brancos às {hour}:00',
                        'Probabilidade': pattern_count / len(filtered_data),
                        'Quantidade de Ocorrências': pattern_count,
                        'Total de Ocorrências': len(filtered_data)
                    })

# Analisar os padrões
analyze_patterns(contagem_data)

# Criar um DataFrame com os padrões encontrados
patterns_df = pd.DataFrame(patterns)

# Verificar se a coluna 'Probabilidade' existe antes de tentar ordená-la
if 'Probabilidade' in patterns_df.columns:
    # Ordenar os padrões por probabilidade (maior primeiro)
    patterns_df = patterns_df.sort_values(by='Probabilidade', ascending=False)
else:
    print("A coluna 'Probabilidade' não foi encontrada.")

# Criar o arquivo Excel para salvar os resultados
output_file_path = os.path.join(desktop_path, "resultados_padroes_brancos.xlsx")

# Salvar os resultados no arquivo Excel
patterns_df.to_excel(output_file_path, index=False)

# O arquivo será salvo diretamente no desktop
print(f"Padrões analisados e salvos em: {output_file_path}")
