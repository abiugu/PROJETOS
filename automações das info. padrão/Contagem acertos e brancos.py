import os

# Define o caminho para o arquivo de log
caminho_arquivo = os.path.join(os.path.expanduser(
    '~'), 'Desktop', 'LOGS', 'log 48.txt')

# Função para extrair os maiores valores de acertos diretos e acertos de gale de cada sequência de buscas
def extrair_maiores_acertos_e_contar_white(arquivo_log):
    maiores_acertos_diretos = []
    maiores_acertos_gale = []
    contador_white_apos_alarme = 0
    contador_alarmes_acionados = 0  # Adicionando o contador de alarmes acionados
    acertos_direto_sequencia = []
    acertos_gale_sequencia = []
    with open(arquivo_log, 'r') as arquivo:
        linhas = arquivo.readlines()
        for i in range(len(linhas)):
            linha = linhas[i]
            if 'Acertos direto:' in linha and 'Acertos gale:' in linha:  # Corrigindo a condição de busca
                acertos_direto = int(linha.split(
                    'Acertos direto: ')[1].split(',')[0])
                if acertos_direto > 0:
                    acertos_direto_sequencia.append(acertos_direto)
                else:
                    if acertos_direto_sequencia:
                        maiores_acertos_diretos.append(
                            max(acertos_direto_sequencia))
                        acertos_direto_sequencia = []
                acertos_gale = int(linha.split(
                    'Acertos gale: ')[1].split(',')[0])
                if acertos_gale > 0:
                    acertos_gale_sequencia.append(acertos_gale)
                else:
                    if acertos_gale_sequencia:
                        maiores_acertos_gale.append(
                            max(acertos_gale_sequencia))
                        acertos_gale_sequencia = []
            elif 'Alarme acionado' in linha:
                contador_alarmes_acionados += 1
                # Verifica a presença de "white" dentro das próximas sete linhas
                limite_superior = min(i + 7, len(linhas))
                white_encontrado = False  # Flag para indicar se "white" foi encontrado
                for j in range(i + 1, limite_superior):
                    if 'white' in linhas[j]:
                        white_encontrado = True
                        break  # Se encontrar, para a busca
                # Incrementa o contador apenas se "white" foi encontrado
                if white_encontrado:
                    contador_white_apos_alarme += 1

        # Adiciona o último valor antes de ser zerado
        if acertos_direto_sequencia:
            maiores_acertos_diretos.append(max(acertos_direto_sequencia))
        if acertos_gale_sequencia:
            maiores_acertos_gale.append(max(acertos_gale_sequencia))
    return maiores_acertos_diretos, maiores_acertos_gale, contador_alarmes_acionados, contador_white_apos_alarme


# Extrai os maiores valores de acertos diretos e acertos de gale de cada sequência de buscas
# e conta os "white" após cada "Alarme acionado"
maiores_acertos_diretos, maiores_acertos_gale, contador_alarmes_acionados, contador_white_apos_alarme = extrair_maiores_acertos_e_contar_white(
    caminho_arquivo)

# Soma os maiores valores de acertos diretos e acertos de gale
total_maiores_acertos_diretos = sum(maiores_acertos_diretos)
total_maiores_acertos_gale = sum(maiores_acertos_gale)

# Imprime o total dos maiores valores de acertos diretos e acertos de gale, e a contagem de "white"
print("Total dos maiores valores de acertos diretos:",
      total_maiores_acertos_diretos)
print("Total dos maiores valores de acertos de gale:", total_maiores_acertos_gale)
print("Número de alarmes acionados:", contador_alarmes_acionados)
print("Número de vezes que 'white' foi visto após um alarme:",
      contador_white_apos_alarme)
