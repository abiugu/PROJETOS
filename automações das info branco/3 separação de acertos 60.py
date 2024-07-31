import os

# Define o caminho para o arquivo de log
caminho_arquivo = os.path.join(os.path.expanduser('~'), 'Desktop', 'LOGS', 'log 60 branco.txt')

# Função para extrair as linhas de acertos brancos
def extrair_acertos_brancos(arquivo_log):
    linhas_acertos_brancos = []
    acertos_brancos_anteriores = ""
    with open(arquivo_log, 'r') as arquivo:
        linhas = arquivo.readlines()
        for i in range(len(linhas)):
            if 'Acertos branco:' in linhas[i] and 'Acertos gale branco:' in linhas[i]:
                partes = linhas[i].split(',')
                valor_acertos_brancos = partes[0].split(':')[1].strip()
                if valor_acertos_brancos != acertos_brancos_anteriores and valor_acertos_brancos != '0':
                    linhas_acertos_brancos.extend(linhas[max(0, i-16):i+1])
                    linhas_acertos_brancos.append('\n')
                    acertos_brancos_anteriores = valor_acertos_brancos
    return linhas_acertos_brancos

# Função para extrair as linhas de acertos gale brancos
def extrair_acertos_gale_brancos(arquivo_log):
    linhas_acertos_gale_brancos = []
    acertos_gale_brancos_anteriores = ""
    with open(arquivo_log, 'r') as arquivo:
        linhas = arquivo.readlines()
        for i in range(len(linhas)):
            if 'Acertos branco:' in linhas[i] and 'Acertos gale branco:' in linhas[i]:
                partes = linhas[i].split(',')
                valor_acertos_gale_brancos = partes[1].split(':')[1].strip()
                if valor_acertos_gale_brancos != acertos_gale_brancos_anteriores and valor_acertos_gale_brancos != '0':
                    linhas_acertos_gale_brancos.extend(linhas[max(0, i-16):i+1])
                    linhas_acertos_gale_brancos.append('\n')
                    acertos_gale_brancos_anteriores = valor_acertos_gale_brancos
    return linhas_acertos_gale_brancos

# Função para salvar as linhas de acerto em um novo arquivo
def salvar_acertos(arquivo_saida, linhas_acertos):
    with open(arquivo_saida, 'w') as arquivo:
        for linha in linhas_acertos:
            arquivo.write(linha)

# Extrai as linhas de acerto do arquivo de log
linhas_acertos_brancos = extrair_acertos_brancos(caminho_arquivo)
linhas_acertos_gale_brancos = extrair_acertos_gale_brancos(caminho_arquivo)

# Define os caminhos para os arquivos de saída
caminho_saida_brancos = os.path.join(os.path.expanduser('~'), 'Desktop', 'LOGS', 'acertos', 'acertos_branco 60.txt')
caminho_saida_gale_brancos = os.path.join(os.path.expanduser('~'), 'Desktop', 'LOGS', 'acertos', 'acertos_gale_branco 60.txt')

# Salva as linhas de acerto em novos arquivos
salvar_acertos(caminho_saida_brancos, linhas_acertos_brancos)
salvar_acertos(caminho_saida_gale_brancos, linhas_acertos_gale_brancos)

print("Linhas de acertos branco e gale branco extraídas e salvas com sucesso!")
