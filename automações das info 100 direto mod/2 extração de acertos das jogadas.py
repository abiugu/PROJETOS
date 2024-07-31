import os

# Define o caminho para o arquivo de log
caminho_arquivo = os.path.join(os.path.expanduser('~'), 'Desktop', 'LOGS', 'log 100 direto mod.txt')

# Função para extrair as linhas de acertos
def extrair_acertos(arquivo_log):
    linhas_acertos = []
    acertos_brancos_anteriores = ""
    acertos_direto_anteriores = ""
    with open(arquivo_log, 'r') as arquivo:
        linhas = arquivo.readlines()
        for i in range(len(linhas)):
            # Verifica se a linha contém as palavras "Acertos branco:" e "Acertos gale branco:"
            if 'Acertos branco:' in linhas[i] and 'Acertos direto:' in linhas[i]:
                # Extrai os valores dos acertos brancos e gale brancos
                partes = linhas[i].split(',')
                valor_acertos_brancos = partes[0].split(':')[1].strip()
                valor_acertos_direto = partes[1].split(':')[1].strip()
                # Verifica se algum dos valores mudou e não é zero
                if (valor_acertos_brancos != acertos_brancos_anteriores or valor_acertos_direto != acertos_direto_anteriores) and (valor_acertos_brancos != '0' or valor_acertos_direto != '0'):
                    # Adiciona as 16 linhas anteriores à linha de acertos
                    linhas_acertos.extend(linhas[max(0, i-11):i+1])  # Se i < 16, começa da linha 0
                    # Adiciona uma linha vazia para separar os acertos
                    linhas_acertos.append('\n')
                    # Atualiza os valores de acertos anteriores
                    acertos_brancos_anteriores = valor_acertos_brancos
                    acertos_direto_anteriores = valor_acertos_direto
    return linhas_acertos

# Função para salvar as linhas de acerto em um novo arquivo
def salvar_acertos(arquivo_saida, linhas_acertos):
    with open(arquivo_saida, 'w') as arquivo:
        for linha in linhas_acertos:
            arquivo.write(linha)

# Extrai as linhas de acerto do arquivo de log
linhas_acertos = extrair_acertos(caminho_arquivo)

# Define o caminho para o arquivo de saída
caminho_saida = os.path.join(os.path.expanduser('~'), 'Desktop', 'LOGS', 'acertos', 'acertos log 100 direto mod.txt')

# Salva as linhas de acerto em um novo arquivo
salvar_acertos(caminho_saida, linhas_acertos)

print("Linhas de acerto extraídas e salvas com sucesso!")
