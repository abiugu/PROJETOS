import os


def ler_lista_cores():
    desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
    arquivo_path = os.path.join(desktop_path, 'resultados double.txt')
    with open(arquivo_path, "r") as arquivo:
        linhas = arquivo.readlines()
    lista_cores = []
    for linha in linhas:
        cor = linha.strip().split(",")[1].split(":")[1].strip()
        lista_cores.append(cor)
    return lista_cores


2


def contar_acertos_erros(lista_cores, tamanho_sequencia):
    acertos = 0
    erros = 0
    for i in range(len(lista_cores) - tamanho_sequencia):
        sequencia = lista_cores[i:i+tamanho_sequencia]
        if len(set(sequencia)) == 1:  # Verifica se todas as cores na sequência são iguais
            proxima_cor = lista_cores[i+tamanho_sequencia]
            if proxima_cor == sequencia[0]:
                erros += 1
            else:
                acertos += 1
    return acertos, erros


def calcular_proporcao(acertos, erros):
    proporcao = (acertos / (acertos + erros)) * 100
    return proporcao


def main():
    lista_cores = ler_lista_cores()
    tamanho_sequencia = int(
        input("Digite o tamanho da sequência de cores que deseja analisar: "))
    acertos, erros = contar_acertos_erros(lista_cores, tamanho_sequencia)

    print(f"Contagem de acertos e erros após sequências de {
          tamanho_sequencia} cores iguais:")
    print(f"Acertos: {acertos}")
    print(f"Erros: {erros}")

    proporcao = calcular_proporcao(acertos, erros)
    print(f"Proporção de acertos: {proporcao:.2f}%")


if __name__ == "__main__":
    main()
