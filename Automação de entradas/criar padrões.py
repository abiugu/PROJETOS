import random

# Cores possíveis
cores_possiveis = ["black", "red", "white"]

# Função para gerar um padrão aleatório
def gerar_padrao():
    # Primeira parte do padrão, de 6 a 8 cores
    primeira_parte = tuple(random.choices(cores_possiveis, k=random.randint(4, 8)))
    
    # Segunda parte do padrão, sempre ["white", "red"] ou ["white", "black"]
    segunda_parte = tuple(random.choice([["white", "red"], ["white", "black"]]))
    
    return (primeira_parte, segunda_parte)

# Conjunto para garantir que os padrões sejam únicos
padroes_gerados = set()

# Lista para armazenar os padrões finais
padroes = {}

# Gerar 1000 padrões únicos
while len(padroes) < 10000:
    novo_padrao = gerar_padrao()
    
    # Adicionar ao conjunto e à lista, se for único
    if novo_padrao not in padroes_gerados:
        padroes_gerados.add(novo_padrao)
        padroes[f"padrao {len(padroes) + 1}"] = novo_padrao

# Exibir todos os 1000 padrões
for i in range(10000):
    print(f"padrao {i+1}: {padroes[f'padrao {i+1}']}")
