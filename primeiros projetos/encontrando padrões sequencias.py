import os

def ler_lista_cores():
    desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
    arquivo_path = os.path.join(desktop_path, 'resultados double.txt')
    with open(arquivo_path, "r") as arquivo:
        linhas = arquivo.readlines()
    lista_cores = []
    for linha in linhas:
        if 'Cor:' in linha:  
            cor = linha.strip().split("Cor:")[1].strip().split()[0].lower()  
            lista_cores.append(cor)
    return lista_cores

def solicitar_cor():
    while True:
        cor = input("Digite a cor desejada (b, w, r): ").lower()
        if cor in ['b', 'w', 'r']:
            return {'b': 'black', 'w': 'white', 'r': 'red'}[cor]
        else:
            print("Cor inválida. Por favor, digite 'b', 'w' ou 'r'.")

def encontrar_sequencias(lista_cores, tamanho_sequencia, cor_especifica):
    sequencias_encontradas = 0
    for i in range(len(lista_cores) - tamanho_sequencia + 1):
        sequencia = lista_cores[i:i+tamanho_sequencia]
        if sequencia == cor_especifica:
            sequencias_encontradas += 1
    return sequencias_encontradas

def main():
    lista_cores = ler_lista_cores()

    comprimento_sequencia = int(input("Digite o comprimento da sequência desejada: "))

    cor_especifica = []
    for i in range(comprimento_sequencia):
        cor = solicitar_cor()
        cor_especifica.append(cor)

    sequencias_encontradas = encontrar_sequencias(lista_cores, comprimento_sequencia, cor_especifica)

    if sequencias_encontradas > 0:
        print(f"Número de sequências de {comprimento_sequencia} cores iguais encontradas: {sequencias_encontradas}")
    else:
        print(f"Nenhuma sequência de {comprimento_sequencia} cores iguais encontrada.")

if __name__ == "__main__":
    main()
