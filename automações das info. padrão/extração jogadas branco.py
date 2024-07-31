import os

# Define o caminho para a pasta LOGS
caminho_pasta_logs = os.path.join(os.path.expanduser('~'), 'Desktop', 'LOGS')

# Define o caminho para o arquivo de log
caminho_arquivo = os.path.join(caminho_pasta_logs, 'log 48.txt')

# Função para extrair as linhas acima e abaixo do "Alarme acionado" quando há "white" na linha abaixo
def extrair_informacoes_alarmes(arquivo_log):
    informacoes_alarmes = []  # Lista para armazenar as informações extraídas
    contador_alarmes_acionados = 0
    with open(arquivo_log, 'r') as arquivo:
        linhas = arquivo.readlines()
        for i in range(len(linhas)):
            linha = linhas[i]
            if 'Alarme acionado' in linha:
                # Verifica se a próxima linha contém "white"
                if 'white' in linhas[i + 1]:
                    contador_alarmes_acionados += 1
                    informacoes = []
                    # Extrai as cinco linhas acima do "Alarme acionado"
                    for l in range(max(0, i - 5), i):
                        informacoes.append(linhas[l].strip())
                    # Adiciona a linha do "Alarme acionado"
                    informacoes.append(linha.strip())
                    # Extrai as dez linhas abaixo do "Alarme acionado"
                    for k in range(i + 1, min(i + 11, len(linhas))):
                        informacoes.append(linhas[k].strip())
                    informacoes_alarmes.append(informacoes)  # Adiciona as informações extraídas à lista

    return contador_alarmes_acionados, informacoes_alarmes


# Extrai as informações sobre os "Alarme acionado" e as linhas acima e abaixo, apenas quando há "white"
contador_alarmes, informacoes_alarmes = extrair_informacoes_alarmes(caminho_arquivo)

# Salva as informações em um arquivo chamado "resultados_branco_log.txt"
arquivo_saida = os.path.join(caminho_pasta_logs, 'branco log 48.txt')
with open(arquivo_saida, 'w') as saida:
    saida.write("Número de alarmes acionados com 'white' na linha abaixo: {}\n\n".format(contador_alarmes))
    for informacoes in informacoes_alarmes:
        for linha in informacoes:
            saida.write(linha + '\n')
        saida.write('\n')

print("As informações foram extraídas e salvas no arquivo 'resultados_branco_log.txt'.")