import os
import pandas as pd

# Caminho para o desktop
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")

# Carregar os dados do arquivo gerado
file_path = os.path.join(desktop_path, "contagem_branco_por_dia_hora.xlsx")
contagem_data = pd.read_excel(file_path)

# Calcular a diferença entre as jogadas de branco em dias consecutivos
contagem_data['Dia'] = pd.to_datetime(contagem_data['Dia'])
contagem_data.sort_values(by='Dia', inplace=True)

# Calcular a diferença da quantidade de branco entre dias consecutivos
contagem_data['Diferença de Branco'] = contagem_data['Quantidade'].diff()

# Verificar os dias com aumento de branco
dias_com_aumento = contagem_data[contagem_data['Diferença de Branco'] > 0]

# Analisar a compensação das horas com menos jogadas
# Vamos calcular a diferença entre as horas em um dia específico
contagem_data['Diferença de Branco por Hora'] = contagem_data.groupby('Dia')['Quantidade'].diff()

# Verificar horas com compensação significativa
horas_com_compensacao = contagem_data[contagem_data['Diferença de Branco por Hora'] > 0]

# Criar o arquivo Excel para salvar ambos os dados (dias e horas)
output_file_path = os.path.join(desktop_path, "resultado_analisado_brancos.xlsx")

# Salvar ambos os resultados no mesmo arquivo Excel
with pd.ExcelWriter(output_file_path) as writer:
    dias_com_aumento.to_excel(writer, index=False, sheet_name='Dias com aumento de branco')
    horas_com_compensacao.to_excel(writer, index=False, sheet_name='Horas com compensação de branco')

# Não há print, o arquivo foi salvo diretamente no desktop
print(f"Resultados analisados e salvos em: {output_file_path}")