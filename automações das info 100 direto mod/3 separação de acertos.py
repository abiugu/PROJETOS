import os

# Define o caminho para o arquivo de log
caminho_arquivo = os.path.join(os.path.expanduser('~'), 'Desktop', 'LOGS', 'log 100 direto mod.txt')

# Função para extrair as linhas de acertos brancos
def extrair_acertos_brancos(arquivo_log):
    linhas_acertos_brancos = []
    acertos_brancos_anteriores = ""
    with open(arquivo_log, 'r') as arquivo:
        linhas = arquivo.readlines()
        for i in range(len(linhas)):
            if 'Acertos branco:' in linhas[i] and 'Acertos direto:' in linhas[i]:
                partes = linhas[i].split(',')
                valor_acertos_brancos = partes[0].split(':')[1].strip()
                if valor_acertos_brancos != acertos_brancos_anteriores and valor_acertos_brancos != '0':
                    linhas_acertos_brancos.extend(linhas[max(0, i-11):i+1])
                    linhas_acertos_brancos.append('\n')
                    acertos_brancos_anteriores = valor_acertos_brancos
    return linhas_acertos_brancos

# Função para extrair as linhas de acertos diretos
def extrair_acertos_diretos(arquivo_log):
    linhas_acertos_diretos = []
    acertos_direto_anteriores = ""
    with open(arquivo_log, 'r') as arquivo:
        linhas = arquivo.readlines()
        for i in range(len(linhas)):
            if 'Acertos branco:' in linhas[i] and 'Acertos direto:' in linhas[i]:
                partes = linhas[i].split(',')
                valor_acertos_direto = partes[1].split(':')[1].strip()
                if valor_acertos_direto != acertos_direto_anteriores and valor_acertos_direto != '0':
                    linhas_acertos_diretos.extend(linhas[max(0, i-11):i+1])
                    linhas_acertos_diretos.append('\n')
                    acertos_direto_anteriores = valor_acertos_direto
    return linhas_acertos_diretos

# Função para salvar as linhas de acerto em um novo arquivo
def salvar_acertos(arquivo_saida, linhas_acertos):
    with open(arquivo_saida, 'w') as arquivo:
        for linha in linhas_acertos:
            arquivo.write(linha)

# Extrai as linhas de acerto do arquivo de log
linhas_acertos_brancos = extrair_acertos_brancos(caminho_arquivo)
linhas_acertos_diretos = extrair_acertos_diretos(caminho_arquivo)

# Define os caminhos para os arquivos de saída
caminho_saida_brancos = os.path.join(os.path.expanduser('~'), 'Desktop', 'LOGS', 'acertos', 'acertos_branco 100 mod.txt')
caminho_saida_diretos = os.path.join(os.path.expanduser('~'), 'Desktop', 'LOGS', 'acertos', 'acertos_direto 100 mod.txt')

# Salva as linhas de acerto em novos arquivos
salvar_acertos(caminho_saida_brancos, linhas_acertos_brancos)
salvar_acertos(caminho_saida_diretos, linhas_acertos_diretos)

print("Linhas de acerto brancos e diretos extraídas e salvas com sucesso!")
