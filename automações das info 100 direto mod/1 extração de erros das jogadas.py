import os

# Define o caminho para o arquivo de log
caminho_arquivo = os.path.join(os.path.expanduser('~'), 'Desktop', 'LOGS', 'log 100 direto mod.txt')

# Função para extrair as linhas de erro
def extrair_erros(arquivo_log):
    linhas_erros = []
    erros_anteriores = -1  # Inicializa com um valor que nunca será o mesmo que a primeira quantidade de erros
    with open(arquivo_log, 'r') as arquivo:
        linhas = arquivo.readlines()
        for i in range(len(linhas)):
            # Verifica se a linha contém a palavra "Erros:"
            if 'Erros:' in linhas[i]:
                # Extrai a quantidade de erros
                erros = int(linhas[i].split('Erros: ')[1])
                # Verifica se a quantidade de erros é diferente de zero e se mudou
                if erros != 0 and erros != erros_anteriores:
                    # Se sim, adiciona as próximas 17 linhas ao total de erros
                    linhas_erro = linhas[i-11:i+1]
                    linhas_erros.append(''.join(linhas_erro))
                    # Atualiza o número de erros anterior
                    erros_anteriores = erros
                    # Adiciona uma linha vazia para separar os erros
                    linhas_erros.append('\n')
    return linhas_erros

# Função para salvar as linhas de erro em um novo arquivo
def salvar_erros(arquivo_saida, linhas_erros):
    with open(arquivo_saida, 'w') as arquivo:
        for linha in linhas_erros:
            arquivo.write(linha)

# Extrai as linhas de erro do arquivo de log
linhas_erros = extrair_erros(caminho_arquivo)

# Define o caminho para o arquivo de saída
caminho_saida = os.path.join(os.path.expanduser('~'), 'Desktop', 'LOGS','erros', 'erros log 100 direto mod.txt')

# Salva as linhas de erro em um novo arquivo
salvar_erros(caminho_saida, linhas_erros)

print("Linhas de erro extraídas e salvas com sucesso!")
