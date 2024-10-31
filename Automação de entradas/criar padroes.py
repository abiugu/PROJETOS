padroes = {
    # Seus 65 padrões iniciais aqui

    # Novos padrões gerados
    "padrao 66": (["white", "black", "red", "white", "black"], ["black", "white"]),
    "padrao 67": (["black", "white", "red", "black", "white", "red"], ["red", "white"]),
    "padrao 68": (["red", "black", "white", "white", "black"], ["white", "red"]),
    "padrao 69": (["black", "red", "white", "black", "red"], ["red", "white"]),
    "padrao 70": (["white", "red", "black", "red", "white"], ["black", "white"]),
    "padrao 71": (["black", "white", "red", "red", "white", "black"], ["black", "white"]),
    "padrao 72": (["red", "black", "white", "red", "black"], ["white", "red"]),
    "padrao 73": (["white", "red", "black", "white", "black"], ["red", "white"]),
    "padrao 74": (["black", "black", "white", "red", "white"], ["black", "white"]),
    "padrao 75": (["red", "white", "black", "black", "red"], ["red", "white"]),
    "padrao 76": (["white", "black", "red", "white", "black"], ["red", "white"]),
    "padrao 77": (["black", "white", "red", "white", "black"], ["black", "white"]),
    "padrao 78": (["red", "black", "white", "red", "black"], ["red", "white"]),
    "padrao 79": (["black", "red", "white", "white", "black"], ["black", "white"]),
    "padrao 80": (["red", "white", "red", "black", "white"], ["white", "red"]),
    # ...
    # Continuar com a estrutura acima até padrao 300
    # Vou criar uma função para gerar automaticamente até 300, respeitando a estrutura

    # Exemplo de função para gerar 300 padrões sem repetição de sequências
}

from random import choice, sample

# Cores disponíveis
cores = ["black", "red", "white"]

# Função para gerar padrões
def gerar_padroes(num_padroes, padroes_existentes):
    padroes_gerados = padroes_existentes.copy()
    padroes_novos = len(padroes_existentes) + 1

    while len(padroes_gerados) < num_padroes:
        # Gera uma sequência de 3 a 6 cores aleatórias
        sequencia = [choice(cores) for _ in range(choice([3, 4, 5, 6]))]

        # Verifica se existe ao menos uma cor que não seja "white"
        cores_nao_brancas = [c for c in sequencia if c != "white"]

        # Garante que existe uma cor adicional além de "white" para definir como correta
        if cores_nao_brancas:
            cores_certas = ["white", choice(cores_nao_brancas)]

            # Garante que a sequência é única
            if sequencia not in [v[0] for v in padroes_gerados.values()]:
                padroes_gerados[f"padrao {padroes_novos}"] = (sequencia, cores_certas)
                padroes_novos += 1

    return padroes_gerados

# Executa a função para gerar até 300 padrões únicos
padroes = gerar_padroes(300, padroes)

# Exemplo de saída com 300 padrões
print(padroes)
