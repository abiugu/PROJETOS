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
# Caso você tenha uma coluna de data e hora, como 'Data' ou 'Hora', use-a
branco_data['Data'] = pd.to_datetime(branco_data['Data'])  # Converter para formato datetime, ajuste se necessário

# Extrair apenas a data (sem a hora) e a hora (sem minutos e segundos)
branco_data['Dia'] = branco_data['Data'].dt.date  # Extrair a data (sem hora)
branco_data['Hora'] = branco_data['Data'].dt.hour  # Extrair a hora (sem minutos)

# Contar as jogadas de branco por dia e hora
contagem_por_dia_hora = branco_data.groupby(['Dia', 'Hora']).size().reset_index(name='Quantidade')

# Salvar os resultados em uma nova planilha
output_file_path = os.path.join(desktop_path, "contagem_branco_por_dia_hora.xlsx")
contagem_por_dia_hora.to_excel(output_file_path, index=False)

print(f"Contagem de jogadas de branco por dia e hora salva em: {output_file_path}")
