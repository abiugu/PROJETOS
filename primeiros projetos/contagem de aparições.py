import os

def ler_lista_numeros():
    desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
    arquivo_path = os.path.join(desktop_path, 'resultados double.txt')
    with open(arquivo_path, "r") as arquivo:
        linhas = arquivo.readlines()
    lista_numeros = []
    for linha in linhas:
        numero = int(linha.strip().split(",")[0].split(":")[1].strip())
        lista_numeros.append(numero)
    return lista_numeros

def contar_aparicoes(lista_numeros):
    contagem = {}
    for numero in lista_numeros:
        if numero in contagem:
            contagem[numero] += 1
        else:
            contagem[numero] = 1
    return contagem

def encontrar_maior_tempo_sem_aparicao(lista_numeros):
    maior_tempo_sem_aparicao = {}
    ultima_aparicao = {}

    for numero in range(15):  # Números de 0 a 14
        maior_tempo_sem_aparicao[numero] = 0
        ultima_aparicao[numero] = -1

    for i, numero in enumerate(lista_numeros):
        if ultima_aparicao[numero] != -1:
            tempo_sem_aparicao = i - ultima_aparicao[numero] - 1
            if tempo_sem_aparicao > maior_tempo_sem_aparicao[numero]:
                maior_tempo_sem_aparicao[numero] = tempo_sem_aparicao
        ultima_aparicao[numero] = i

    return maior_tempo_sem_aparicao

def main():
    lista_numeros = ler_lista_numeros()

    # Contagem de vezes que cada número aparece na lista
    contagem = contar_aparicoes(lista_numeros)

    # Maior tempo sem aparição de cada número
    maior_tempo_sem_aparicao = encontrar_maior_tempo_sem_aparicao(lista_numeros)

    # Imprime a contagem de cada número de 0 a 14 em ordem
    print("Contagem de vezes que cada número aparece na lista:")
    for numero in range(15):  # Números de 0 a 14
        vezes_visto = contagem.get(numero, 0)
        print(f"Número {numero}: Vezes visto na lista: {vezes_visto}")

    # Imprime o maior tempo sem aparição de cada número de 0 a 14 em ordem
    print("\nMaior tempo sem aparição de cada número:")
    for numero in range(15):  # Números de 0 a 14
        tempo_sem_aparicao = maior_tempo_sem_aparicao[numero]
        print(f"Número {numero}: Maior tempo sem aparição: {tempo_sem_aparicao}")

if __name__ == "__main__":
    main()
