import os

# Define o caminho para o arquivo de log
caminho_arquivo = os.path.join(os.path.expanduser('~'), 'Desktop', 'LOGS', 'log 60 branco.txt')

# Função para extrair as linhas de acertos
def extrair_acertos(arquivo_log):
    linhas_acertos = []
    acertos_brancos_anteriores = ""
    acertos_gale_brancos_anteriores = ""
    with open(arquivo_log, 'r') as arquivo:
        linhas = arquivo.readlines()
        for i in range(len(linhas)):
            # Verifica se a linha contém as palavras "Acertos branco:" e "Acertos gale branco:"
            if 'Acertos branco:' in linhas[i] and 'Acertos gale branco:' in linhas[i]:
                # Extrai os valores dos acertos brancos e gale brancos
                partes = linhas[i].split(',')
                valor_acertos_brancos = partes[0].split(':')[1].strip()
                valor_acertos_gale_brancos = partes[1].split(':')[1].strip()
                # Verifica se algum dos valores mudou e não é zero
                if (valor_acertos_brancos != acertos_brancos_anteriores or valor_acertos_gale_brancos != acertos_gale_brancos_anteriores) and (valor_acertos_brancos != '0' or valor_acertos_gale_brancos != '0'):
                    # Adiciona as 16 linhas anteriores à linha de acertos
                    linhas_acertos.extend(linhas[max(0, i-16):i+1])  # Se i < 16, começa da linha 0
                    # Adiciona uma linha vazia para separar os acertos
                    linhas_acertos.append('\n')
                    # Atualiza os valores de acertos anteriores
                    acertos_brancos_anteriores = valor_acertos_brancos
                    acertos_gale_brancos_anteriores = valor_acertos_gale_brancos
    return linhas_acertos

# Função para salvar as linhas de acerto em um novo arquivo
def salvar_acertos(arquivo_saida, linhas_acertos):
    with open(arquivo_saida, 'w') as arquivo:
        for linha in linhas_acertos:
            arquivo.write(linha)

# Extrai as linhas de acerto do arquivo de log
linhas_acertos = extrair_acertos(caminho_arquivo)

# Define o caminho para o arquivo de saída
caminho_saida = os.path.join(os.path.expanduser('~'), 'Desktop', 'LOGS', 'acertos', 'acertos log 60 branco.txt')

# Salva as linhas de acerto em um novo arquivo
salvar_acertos(caminho_saida, linhas_acertos)

print("Linhas de acerto extraídas e salvas com sucesso!")
