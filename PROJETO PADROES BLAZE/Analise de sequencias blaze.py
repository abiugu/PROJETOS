import os
import pandas as pd
from tqdm import tqdm  # Importando a biblioteca tqdm para barras de progresso
from collections import Counter

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

# Barra de progresso para normalizar as cores
print("Normalizando as cores...")
data['Cor'] = data['Cor'].apply(normalize_color)  # Garantir que a cor esteja em inglês

# Perguntar ao usuário o número mínimo e máximo de jogadas
min_seq_length = int(input("Digite o número mínimo de jogadas para analisar (ex: 4): "))
max_seq_length = int(input("Digite o número máximo de jogadas para analisar (ex: 6): "))  # Ajustado para permitir sequências maiores

# Função para gerar as sequências com combinações de cor
def generate_color_sequences(data, min_seq_length, max_seq_length):
    sequences_with_next = []
    
    for seq_length in range(min_seq_length, max_seq_length + 1):  # Considera sequências de X até Y jogadas
        for i in tqdm(range(len(data) - seq_length), desc=f'Gerando sequências de tamanho {seq_length}', unit='sequência'):
            # Gerar sequência de cor
            sequence = []
            for j in range(seq_length):
                sequence.append(data['Cor'].iloc[i + j])  # Cor
            next_color = data['Cor'].iloc[i + seq_length]  # Cor da próxima jogada após a sequência
            sequences_with_next.append((tuple(sequence), next_color))
    
    return sequences_with_next

# Função para verificar a assertividade (80% de previsão correta)
def find_perfect_sequences(data, min_seq_length, max_seq_length, threshold=0.8, min_repetitions=10):
    print("Analisando as sequências de cores...")
    # Gerar sequências de cores
    color_sequences_with_next = generate_color_sequences(data, min_seq_length, max_seq_length)
    
    # Contar as ocorrências de sequências e os padrões seguintes
    color_sequence_counts = Counter(color_sequences_with_next)
    
    perfect_sequences = []
    
    # Analisando sequências de cor
    for seq, count in tqdm(color_sequence_counts.items(), desc="Analisando sequências", unit="sequência"):
        if count < min_repetitions:
            continue  # Ignorar sequências com menos de 10 repetições
        
        sequence, next_color = seq
        color_counts = {'black': 0, 'red': 0, 'white': 0}
        
        # Contar quantas vezes cada cor ocorre após a sequência
        for seq_item, seq_next_color in color_sequences_with_next:
            if seq_item == sequence:
                color_counts[seq_next_color] += 1
        
        total_next = sum(color_counts.values())
        
        # Verificar se alguma cor tem 80% de assertividade
        for color, color_count in color_counts.items():
            if total_next > 0 and (color_count / total_next) >= threshold:
                perfect_sequences.append((sequence, color, color_count, total_next, (color_count / total_next) * 100))
    
    return perfect_sequences

# Encontrar sequências perfeitas
perfect_sequences = find_perfect_sequences(data, min_seq_length, max_seq_length, threshold=0.8, min_repetitions=10)

# Verificar se há resultados
if not perfect_sequences:
    print("Nenhuma sequência com assertividade de 80% ou mais foi encontrada.")
else:
    # Ordenar os resultados pela quantidade total de sequências em ordem decrescente
    perfect_sequences.sort(key=lambda x: x[3], reverse=True)

    # Salvar os resultados em um arquivo .txt na área de trabalho
    output_file_path = os.path.join(desktop_path, "resultados_sequencias_80_porcento_blaze.txt")
    with open(output_file_path, 'w') as file:
        for seq, next_color, count, total_count, accuracy in perfect_sequences:
            file.write(f"Sequência: {seq}, Próxima Cor: {next_color}, Repetições: {count}, Total Sequências: {total_count}, Assertividade: {accuracy:.2f}%\n")

    print("Análise concluída. Resultados salvos em:", output_file_path)
# Fim do códigon deve ter 