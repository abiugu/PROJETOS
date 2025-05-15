import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import os

# Função para atribuir cor e paridade aos números
def get_cor_paridade_v2(num):
    if num == 0:
        return 'Verde', 'N/A'  # Verde é N/A para paridade
    vermelho = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
    cor = 'Vermelho' if num in vermelho else 'Preto'
    paridade = 'Par' if num % 2 == 0 else 'Ímpar'
    return cor, paridade

# Função para verificar e carregar os dados do arquivo
def carregar_dados(file_path):
    # Carregar o arquivo Excel
    df = pd.read_excel(file_path)
    
    # Exibir as primeiras linhas para diagnóstico
    print("Primeiras linhas do arquivo:\n", df.head())
    
    # Aplicar a função de cor e paridade à coluna 'Número'
    df['Cor'], df['Paridade'] = zip(*df['Número'].apply(get_cor_paridade_v2))
    
    return df

# Função para gerar sequências de jogadas para análise
def gerar_sequencias(df, n_min, n_max):
    sequencias = []
    alvos = []
    
    for n in range(n_min, n_max + 1):
        for i in range(len(df) - n):
            # Extrair sequência de números, cores e paridades
            sequencia = list(df.iloc[i:i + n, 0])  # Números
            cor_paridade_seq = list(zip(df.iloc[i:i + n, 1], df.iloc[i:i + n, 2]))  # Cor e paridade
            
            # A próxima jogada será o alvo
            alvo = df.iloc[i + n, 0]
            
            # Garantir que cada sequência tenha o mesmo comprimento
            sequencias.append(sequencia + cor_paridade_seq)  # Combinação de números, cores e paridades
            alvos.append(alvo)
    
    # Aqui vamos garantir que cada sequência tenha o mesmo comprimento, preenchendo com valores padrão ou cortando
    sequencias = [seq[:n_max] if len(seq) > n_max else seq + [None] * (n_max - len(seq)) for seq in sequencias]
    alvos = np.array(alvos)  # Definir os alvos como um array NumPy
    
    # Garantir que as sequências sejam convertidas em uma estrutura homogênea
    sequencias = np.array(sequencias)
    
    return sequencias, alvos

# Função para treinar o modelo de IA e analisar padrões
def treinar_e_analisar_modelo(tamanho_sequencia):
    # Definir o caminho do arquivo no desktop
    desktop_path = os.path.expanduser("~/Desktop")  # Caminho do desktop do usuário
    file_name = "historico roleta immersive (cor e paridade).xlsx"
    file_path = os.path.join(desktop_path, file_name)
    
    # Verificar se o arquivo existe antes de tentar carregá-lo
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"O arquivo {file_name} não foi encontrado no diretório {desktop_path}. Verifique o caminho e o nome do arquivo.")
    
    # Carregar os dados
    df = carregar_dados(file_path)

    # Gerar as sequências com o tamanho escolhido
    sequencias, alvos = gerar_sequencias(df, n_min=tamanho_sequencia, n_max=tamanho_sequencia)

    # Dividir os dados em treinamento e teste
    X_train, X_test, y_train, y_test = train_test_split(sequencias[:, :-1], sequencias[:, -1], test_size=0.3, random_state=42)

    # Treinar um modelo de Floresta Aleatória
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train, y_train)

    # Avaliar o modelo
    y_pred = clf.predict(X_test)
    acuracia = accuracy_score(y_test, y_pred)
    
    # Analisar os padrões
    padroes_percentual, padroes_contagem = analisar_padroes_cor_paridade(df, tamanho_minimo=3, tamanho_maximo=10, minimo_ocorrencias=5)

    return acuracia, padroes_percentual, padroes_contagem

# Função para analisar padrões de cor e paridade com a condição de ocorrerem pelo menos 5 vezes
def analisar_padroes_cor_paridade(df, tamanho_minimo=3, tamanho_maximo=10, minimo_ocorrencias=5):
    padroes = {
        "cor_paridade": {}
    }
    padroes_contagem = {
        "cor_paridade": {}
    }
    
    # Percorrer o DataFrame para analisar padrões
    for tamanho_sequencia in range(tamanho_minimo, tamanho_maximo + 1):
        for i in range(len(df) - tamanho_sequencia):
            sequencia_cor_paridade = tuple(zip(df.iloc[i:i + tamanho_sequencia, 1], df.iloc[i:i + tamanho_sequencia, 2]))  # Combinação de cor e paridade
            
            seguinte_cor_paridade = (df.iloc[i + tamanho_sequencia, 1], df.iloc[i + tamanho_sequencia, 2])
            
            # Contabilizar as sequências
            if sequencia_cor_paridade not in padroes["cor_paridade"]:
                padroes["cor_paridade"][sequencia_cor_paridade] = {'total': 0, 'seguindo': 0}
                padroes_contagem["cor_paridade"][sequencia_cor_paridade] = 0
            padroes["cor_paridade"][sequencia_cor_paridade]['total'] += 1
            padroes_contagem["cor_paridade"][sequencia_cor_paridade] += 1
            if seguinte_cor_paridade == sequencia_cor_paridade[-1]:
                padroes["cor_paridade"][sequencia_cor_paridade]['seguindo'] += 1
    
    # Calcular a assertividade para cada padrão, mas apenas para padrões com ocorrências >= 5
    padroes_percentual = {
        "cor_paridade": {seq: (info['seguindo'] / info['total']) * 100
                         for seq, info in padroes["cor_paridade"].items() if info['total'] >= minimo_ocorrencias}
    }
    
    return padroes_percentual, padroes_contagem

# Solicitar ao usuário o tamanho mínimo e máximo da sequência
x = int(input("Qual o tamanho mínimo da sequência? (De 2 até 20): "))
y = int(input("Qual o tamanho máximo da sequência? (De 2 até 20): "))

# Validar os inputs
while x < 2 or x > 20 or y < 2 or y > 20 or x > y:
    print("Os tamanhos da sequência devem ser entre 2 e 20, e o tamanho mínimo deve ser menor ou igual ao tamanho máximo.")
    x = int(input("Qual o tamanho mínimo da sequência? (De 2 até 20): "))
    y = int(input("Qual o tamanho máximo da sequência? (De 2 até 20): "))

# Criar o caminho do arquivo de texto na Área de Trabalho com o número da sequência
desktop_path = os.path.expanduser("~/Desktop")
arquivo_txt = os.path.join(desktop_path, f"resultado_analise_roleta_{x}_{y}_jogadas.txt")

# Inicializar uma lista para armazenar todos os resultados
all_padroes = []

# Analisar as sequências de todos os tamanhos de x até y
for tamanho_sequencia in range(x, y + 1):
    acuracia, padroes_percentual, padroes_contagem = treinar_e_analisar_modelo(tamanho_sequencia)
    
    # Adicionar os resultados à lista
    all_padroes.append(f"\nResultado para tamanho da sequência {tamanho_sequencia}:\n")
    all_padroes.append(f"Acurácia do modelo: {acuracia}\n")
    all_padroes.append("Padrões mais assertivos (acima de 70% de assertividade e mais de 10 ocorrências):\n")
    
    # Filtrar padrões com assertividade > 70% e com mais de 10 ocorrências
    filtered_padroes = {
        seq: percentual for seq, percentual in padroes_percentual["cor_paridade"].items()
        if percentual > 70 and padroes_contagem["cor_paridade"][seq] > 10
    }

    # Ordenar os padrões de cor e paridade por assertividade em ordem decrescente
    sorted_padroes = sorted(filtered_padroes.items(), key=lambda x: x[1], reverse=True)
    
    for seq, percentual in sorted_padroes:
        count = padroes_contagem["cor_paridade"][seq]  # Quantidade de vezes que a sequência apareceu
        all_padroes.append(f"Sequência: {seq} - Assertividade: {percentual}% - Ocorrências: {count} vezes\n")

# Salvar todos os resultados no arquivo de texto
with open(arquivo_txt, "w") as f:
    f.writelines(all_padroes)

print(f"Os resultados foram salvos no arquivo '{arquivo_txt}'.")
