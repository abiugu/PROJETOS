import os
import pandas as pd

# Caminho para o desktop
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")

# Carregar o arquivo Excel da planilha "historico blaze"
file_path = os.path.join(desktop_path, "historico blaze.xlsx")
print("Carregando os dados...")
data = pd.read_excel(file_path)
print("Dados carregados com sucesso!")

# Normalizar os valores da cor (preto, vermelho, branco)
def normalize_color(color):
    color = color.strip().lower()
    if color == 'black':
        return 'black'
    elif color == 'red':
        return 'red'
    elif color == 'white':
        return 'white'
    return color  # Caso a cor não seja reconhecida

data['Cor'] = data['Cor'].apply(normalize_color)  # Garantir que a cor esteja em inglês

# Filtrar as jogadas de cor 'branco'
branco_data = data[data['Cor'] == 'white']

# Verificar se a coluna de data e hora existe (caso contrário, extrair o tempo da coluna existente)
branco_data['Data'] = pd.to_datetime(branco_data['Data'])  # Converter para formato datetime, ajuste se necessário

# Extrair apenas a data (sem a hora) e a hora (sem minutos e segundos)
branco_data['Dia'] = branco_data['Data'].dt.date  # Extrair a data (sem hora)
branco_data['Hora'] = branco_data['Data'].dt.hour  # Extrair a hora (sem minutos)

# Contar as jogadas de branco por dia e hora
contagem_por_dia_hora = branco_data.groupby(['Dia', 'Hora']).size().reset_index(name='Quantidade')

# Criar DataFrame de todas as combinações de 'Dia' e 'Hora'
all_days = pd.date_range(start=contagem_por_dia_hora['Dia'].min(), end=contagem_por_dia_hora['Dia'].max(), freq='D')
all_hours = list(range(24))

# Criar uma lista com todas as combinações possíveis de 'Dia' e 'Hora'
all_combinations = pd.MultiIndex.from_product([all_days, all_hours], names=['Dia', 'Hora'])

# Criar um DataFrame com todas as combinações de 'Dia' e 'Hora'
full_data = pd.DataFrame(index=all_combinations).reset_index()

# Garantir que as colunas 'Dia' em ambos os DataFrames sejam do tipo datetime64
full_data['Dia'] = pd.to_datetime(full_data['Dia'])
contagem_por_dia_hora['Dia'] = pd.to_datetime(contagem_por_dia_hora['Dia'])

# Mesclar com os dados existentes (de jogadas de branco)
full_contagem_data = pd.merge(full_data, contagem_por_dia_hora, how='left', on=['Dia', 'Hora'])

# Preencher os valores faltantes com 0 (para horas onde não houve jogada de branco)
full_contagem_data['Quantidade'].fillna(0, inplace=True)

# Formatar a coluna 'Dia' para o formato desejado (DD/MM/YYYY) **apenas ao salvar no Excel**
full_contagem_data['Dia'] = full_contagem_data['Dia'].dt.strftime('%d/%m/%Y')

# Criar o arquivo Excel para salvar ambos os dados (dias e horas)
output_file_path = os.path.join(desktop_path, "contagem_branco_por_dia_hora_completo.xlsx")

# Salvar os resultados no mesmo arquivo Excel
full_contagem_data.to_excel(output_file_path, index=False)

print(f"Contagem de jogadas de branco por dia e hora salva em: {output_file_path}")
