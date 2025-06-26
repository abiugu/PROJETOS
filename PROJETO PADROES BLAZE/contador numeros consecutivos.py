import os
import pandas as pd

# Caminho do arquivo Excel
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", "historico blaze.xlsx")

# Carregar os dados do arquivo Excel
df = pd.read_excel(desktop_path)

# Considerando que a coluna de números é chamada 'Número'
numeros = df['Número'].tolist()

# Função para realizar a análise
def contar_sequencias(nums):
    count_numeros = {i: 0 for i in range(15)}
    count_sequencias_vistas = {f"{i},{j}": 0 for i in range(15) for j in range(15)}
    max_sequencias_consecutivas = {f"{i},{j}": 0 for i in range(15) for j in range(15)}
    contador_ativos = {f"{i},{j}": 0 for i in range(15) for j in range(15)}

    # Contagem dos números individuais
    for num in nums:
        if num in count_numeros:
            count_numeros[num] += 1

    # Contagem de sequências e máximas consecutivas com a lógica correta
    for i in range(len(nums) - 1):
        atual_i = nums[i]
        atual_j = nums[i+1]
        chave = f"{atual_i},{atual_j}"

        # Contagem de aparições totais
        count_sequencias_vistas[chave] += 1

        # Incrementa o contador para a sequência atual
        contador_ativos[chave] += 1
        if contador_ativos[chave] > max_sequencias_consecutivas[chave]:
            max_sequencias_consecutivas[chave] = contador_ativos[chave]

        # Zera contadores de outras sequências que começam com o mesmo i e j ≠ atual_j
        for k in range(15):
            if k != atual_j:
                outra_chave = f"{atual_i},{k}"
                contador_ativos[outra_chave] = 0

    # Gerar resultado formatado
    resultado = []
    resultado.append("----- Contagem de Números -----\n")
    for num in range(15):
        resultado.append(f"Numero {num}: {count_numeros[num]} vez(es)\n")

    resultado.append("\n----- Contagem de Sequências (0,0 até 14,14) -----\n")
    for i in range(15):
        for j in range(15):
            chave = f"{i},{j}"
            vistas = count_sequencias_vistas[chave]
            max_consec = max_sequencias_consecutivas[chave]
            if vistas > 0 or max_consec > 0:
                resultado.append(f"\nSequência {chave}:")
                if vistas > 0:
                    resultado.append(f"  - Total de vezes vista: {vistas}")
                if max_consec > 0:
                    resultado.append(f"  - Maior sequência consecutiva: {max_consec}")

    return resultado

# Executar a análise
resultado_analise = contar_sequencias(numeros)

# Caminho do arquivo de saída na área de trabalho
output_path = os.path.join(os.path.expanduser("~"), "Desktop", "resultado_analise.txt")

# Salvar o resultado no arquivo txt
with open(output_path, "w") as file:
    for linha in resultado_analise:
        file.write(linha + "\n")

print(f"Análise concluída e salva em {output_path}")
