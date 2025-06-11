import os
import pandas as pd

# Caminho para o desktop
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")

# Carregar os dados do arquivo gerado
file_path = os.path.join(desktop_path, "contagem_branco_por_dia_hora.xlsx")
contagem_data = pd.read_excel(file_path)

# Garantir que as colunas 'Dia' e 'Hora' estão nos tipos corretos
contagem_data['Dia'] = pd.to_datetime(contagem_data['Dia'], errors='coerce')
contagem_data['Hora'] = contagem_data['Hora'].astype(int)

# Substituir valores ausentes (NaT) ou valores inválidos por um valor padrão
contagem_data['Dia'] = contagem_data['Dia'].fillna(pd.to_datetime('1900-01-01'))  # Substitui NaT por uma data padrão
contagem_data['Hora'] = contagem_data['Hora'].fillna(0).astype(int)  # Substitui valores ausentes em 'Hora' por 0

# Criar uma coluna combinada de 'Data_Hora' para facilitar a análise
contagem_data['Data_Hora'] = pd.to_datetime(contagem_data['Dia'].dt.date.astype(str) + ' ' + contagem_data['Hora'].astype(str) + ':00', format='%Y-%m-%d %H:%M')

# Ordenar os dados por 'Data_Hora', garantindo que a ordem cronológica seja mantida
contagem_data.sort_values(by='Data_Hora', inplace=True)

# Preencher as horas faltantes (de 0 a 23) para cada dia, caso não existam dados para determinadas horas
all_hours = list(range(24))

# Vamos criar um novo DataFrame para garantir que todas as horas estejam representadas
all_dates = pd.date_range(start=contagem_data['Dia'].min(), end=contagem_data['Dia'].max(), freq='D')

# Inicializar uma lista para preencher os dados completos
full_data = []

# Preencher as horas apenas quando não houver dados existentes
for date in all_dates:
    for hour in all_hours:
        # Verificar se já existe dado para aquele dia e hora
        filtered_data = contagem_data[(contagem_data['Dia'].dt.date == date.date()) & (contagem_data['Hora'] == hour)]
        
        if not filtered_data.empty:
            # Se já existe a informação, adiciona
            full_data.append(filtered_data.iloc[0])
        else:
            # Caso não exista, preenche com valores nulos ou zero para aquela hora
            full_data.append({
                'Dia': date.date(),  # Define a data (sem hora)
                'Hora': hour,
                'Quantidade': 0  # Define a quantidade como zero
            })

# Criar um novo DataFrame com os dados completos (com todas as horas)
full_contagem_data = pd.DataFrame(full_data)

# Calcular a diferença da quantidade de branco entre horas consecutivas
full_contagem_data['Diferença de Branco por Hora'] = full_contagem_data.groupby(['Dia'])['Quantidade'].diff()

# Comparar com o dia anterior (mesma hora)
# Aqui, vamos comparar as jogadas da **mesma hora do dia anterior**
def calcular_diferenca_com_dia_anterior(row, data):
    dia_atual = row['Dia']
    hora_atual = row['Hora']
    
    # Ajustar a comparação para garantir que a data e hora sejam comparadas corretamente
    data_dia_anterior = data[(data['Dia'] == dia_atual - pd.Timedelta(days=1)) & (data['Hora'] == hora_atual)]
    
    if not data_dia_anterior.empty:
        return row['Quantidade'] - data_dia_anterior.iloc[0]['Quantidade']
    else:
        return 0  # Se não houver dados para o dia anterior na mesma hora, retorna 0

# Aplicar a função para calcular a diferença com o dia anterior
full_contagem_data['Diferença com Dia Anterior'] = full_contagem_data.apply(calcular_diferenca_com_dia_anterior, axis=1, data=full_contagem_data)

# Formatar a coluna 'Dia' para o formato desejado (DD/MM/YYYY)
full_contagem_data['Dia'] = full_contagem_data['Dia'].dt.strftime('%d/%m/%Y')

# Criar o arquivo Excel para salvar ambos os dados (dias e horas)
output_file_path = os.path.join(desktop_path, "resultado_analisado_brancos_completo.xlsx")

# Salvar os resultados no mesmo arquivo Excel
with pd.ExcelWriter(output_file_path) as writer:
    full_contagem_data.to_excel(writer, index=False, sheet_name='Análise de Brancos')

# O arquivo será salvo diretamente no desktop
print(f"Resultados analisados e salvos em: {output_file_path}")
