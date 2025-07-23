import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import os

# Função para atribuir cor aos números
def get_cor(num):
    # Mapeamento dos números para suas cores
    if num == 0:
        return 'White'  # 0 é White
    elif 1 <= num <= 7:
        return 'Red'  # Números de 1 a 7 são Red
    elif 8 <= num <= 14:
        return 'Black'  # Números de 8 a 14 são Black

# Função para carregar o histórico de jogo Blaze
def carregar_dados(file_path):
    # Carregar o arquivo Excel
    df = pd.read_excel(file_path)
    
    # Aplicar a função de cor à coluna 'Número'
    df['Cor'] = df['Número'].apply(get_cor)
    
    return df

# Função para gerar sequências de jogadas para análise
def gerar_sequencias(df, n_min, n_max):
    sequencias = []
    alvos = []
    
    # Gerar sequências de números e cores para todos os tamanhos entre n_min e n_max
    for n in range(n_min, n_max + 1):
        for i in range(len(df) - n):
            # Extrair sequência de números e cores
            sequencia_numeros = list(df.iloc[i:i + n, 2])  # Números (coluna 'Número')
            sequencia_cores = list(df.iloc[i:i + n, 1])  # Cores (coluna 'Cor')
            
            # O próximo número será o alvo (próximo número)
            alvo = df.iloc[i + n, 2]
            
            # Garantir que cada sequência tenha o mesmo comprimento
            sequencias.append(sequencia_numeros + sequencia_cores)  # Combinação de números e cores
            alvos.append(alvo)
    
    # Aqui vamos garantir que cada sequência tenha o mesmo comprimento, preenchendo com valores padrão ou cortando
    sequencias = [seq[:n_max] if len(seq) > n_max else seq + [None] * (n_max - len(seq)) for seq in sequencias]
    alvos = np.array(alvos)  # Definir os alvos como um array NumPy
    
    # Garantir que as sequências sejam convertidas em uma estrutura homogênea
    sequencias = np.array(sequencias)
    
    return sequencias, alvos

# Função para treinar o modelo de IA e analisar padrões
def treinar_e_analisar_modelo(df, tamanho_sequencia):
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
    padroes_percentual, padroes_contagem = analisar_padroes(df, tamanho_minimo=3, tamanho_maximo=10, minimo_ocorrencias=5)

    return acuracia, padroes_percentual, padroes_contagem

# Função para analisar padrões de cor e número com a condição de ocorrerem pelo menos 5 vezes
def analisar_padroes(df, tamanho_minimo=3, tamanho_maximo=10, minimo_ocorrencias=5):
    padroes = {
        "cor_numero": {}
    }
    padroes_contagem = {
        "cor_numero": {}
    }
    
    # Percorrer o DataFrame para analisar padrões
    for tamanho_sequencia in range(tamanho_minimo, tamanho_maximo + 1):
        for i in range(len(df) - tamanho_sequencia):
            sequencia_cor_numero = tuple(zip(df.iloc[i:i + tamanho_sequencia, 1], df.iloc[i:i + tamanho_sequencia, 2]))  # Combinação de cor e número
            
            seguinte_cor_numero = (df.iloc[i + tamanho_sequencia, 1], df.iloc[i + tamanho_sequencia, 2])
            
            # Contabilizar as sequências
            if sequencia_cor_numero not in padroes["cor_numero"]:
                padroes["cor_numero"][sequencia_cor_numero] = {'total': 0, 'seguindo': 0}
                padroes_contagem["cor_numero"][sequencia_cor_numero] = 0
            padroes["cor_numero"][sequencia_cor_numero]['total'] += 1
            padroes_contagem["cor_numero"][sequencia_cor_numero] += 1
            if seguinte_cor_numero == sequencia_cor_numero[-1]:
                padroes["cor_numero"][sequencia_cor_numero]['seguindo'] += 1
    
    # Calcular a assertividade para cada padrão, mas apenas para padrões com ocorrências >= 5
    padroes_percentual = {
        "cor_numero": {seq: (info['seguindo'] / info['total']) * 100
                         for seq, info in padroes["cor_numero"].items() if info['total'] >= minimo_ocorrencias}
    }
    
    return padroes_percentual, padroes_contagem

# Função para salvar os resultados no arquivo de texto
def salvar_resultados(arquivo_txt, resultados):
    with open(arquivo_txt, "w") as f:
        f.writelines(resultados)

# Função principal para a análise
def realizar_analise():
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
    arquivo_txt = os.path.join(desktop_path, f"resultado_analise_blaze_{x}_{y}_jogadas.txt")

    # Definir o caminho do arquivo do histórico
    file_path = os.path.join(desktop_path, "historico blaze.xlsx")
    
    # Carregar os dados
    df = carregar_dados(file_path)

    # Inicializar uma lista para armazenar todos os resultados
    all_padroes = []

    # Analisar as sequências de todos os tamanhos de x até y
    for tamanho_sequencia in range(x, y + 1):
        acuracia, padroes_percentual, padroes_contagem = treinar_e_analisar_modelo(df, tamanho_sequencia)
        
        # Adicionar os resultados à lista
        all_padroes.append(f"\nResultado para tamanho da sequência {tamanho_sequencia}:\n")
        all_padroes.append(f"Acurácia do modelo: {acuracia}\n")
        all_padroes.append("Padrões mais assertivos (acima de 70% de assertividade e mais de 10 ocorrências):\n")
        
        # Filtrar padrões com assertividade > 70% e com mais de 10 ocorrências
        filtered_padroes = {
            seq: percentual for seq, percentual in padroes_percentual["cor_numero"].items()
            if percentual > 60 and padroes_contagem["cor_numero"][seq] > 5
        }

        # Ordenar os padrões de cor e número por assertividade em ordem decrescente
        sorted_padroes = sorted(filtered_padroes.items(), key=lambda x: x[1], reverse=True)
        
        for seq, percentual in sorted_padroes:
            count = padroes_contagem["cor_numero"][seq]  # Quantidade de vezes que a sequência apareceu
            all_padroes.append(f"Sequência: {seq} - Assertividade: {percentual}% - Ocorrências: {count} vezes\n")

    # Salvar os resultados no arquivo de texto
    salvar_resultados(arquivo_txt, all_padroes)

    print(f"Os resultados foram salvos no arquivo '{arquivo_txt}'.")

# Chamar a função principal para realizar a análise
realizar_analise()
