import requests
import time
import pygame
import sys
sys.stdout.reconfigure(encoding='utf-8')

# Inicialize o pygame
pygame.mixer.init()

# Configurações do Telegram
BOT_TOKEN = "7931524230:AAGCqqZLLi5F_SoT_cIs5wN9js36MiwHXlg"
CHAT_ID = "1139158385"  # ID correto

# URL da API
url = "https://blaze1.space/api/singleplayer-originals/originals/roulette_games/recent/1"

# Padrões predefinidos
padroes = {
    "PADRÃO teste1": (["black", "red"], ["black"]),
    "PADRÃO teste2": (["red", "black"], ["red"]),
    "PADRÃO 7": (["black", "black", "white", "red", "black"], ["black"]),
    "PADRÃO 8": (["red", "red", "white", "black", "red"], ["red"]),
    "PADRÃO 13": (["black", "black", "white", "red", "black", "black"], ["black"]),
    "PADRÃO 14": (["red", "red", "white", "black", "red", "red"], ["red"]),
    "PADRÃO 27": (["white", "black", "white"], ["black"]),
    "PADRÃO 68": (["black", "red", "red", "red", "white"], ["red"]),
    "PADRÃO 104": (["white", "red", "black", "red", "black"], ["red"]),
}

# Função para mapear os valores de cor
def mapear_cor(codigo_cor):
    return {0: "white", 1: "red", 2: "black"}.get(codigo_cor, "unknown")

# Função para enviar mensagem ao Telegram
def enviar_telegram(mensagem):
    url_telegram = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url_telegram, data={"chat_id": CHAT_ID, "text": mensagem})

# Função para buscar o JSON e extrair as cores
def obter_ultimas_cores():
    response = requests.get(url)
    data = response.json()
    return [mapear_cor(jogada["color"]) for jogada in data]

# Variáveis globais
ultimo_padrao = None
ultima_jogada_id = None  # Para armazenar o ID da última jogada
sequencia_anterior = []  # Para armazenar a sequência anterior
padroes_enviados_na_jogada = []  # Para armazenar padrões enviados por jogada

# Função para verificar os padrões
def verificar_padroes(cores):
    global ultimo_padrao, sequencia_anterior, padroes_enviados_na_jogada  # Variáveis globais para controle do fluxo

    # Resetando a lista de padrões enviados para cada nova jogada
    padroes_enviados_na_jogada = []

    for nome_padrao, (historico, entrada) in padroes.items():
        historico_tamanho = len(historico)

        # Verificação se o padrão foi completado
        if cores[:historico_tamanho][::-1] == historico and nome_padrao not in padroes_enviados_na_jogada:
            padroes_enviados_na_jogada.append(nome_padrao)  # Marca o padrão como enviado
            emoji_cor = {"red": "🟥", "black": "⬛", "white": "🤍"}.get(entrada[-1], "")
            mensagem = f"🚀 ALERTA DE SEQUÊNCIA 🚀\n\nFazer entrada !!\n\nEstratégia {nome_padrao} encontrada\nentrar na cor: {emoji_cor}\n"
            print(mensagem)
            enviar_telegram(mensagem)

            # Salva a sequência de jogadas
            sequencia_anterior = cores[:historico_tamanho]  # Armazena a sequência encontrada
            ultimo_padrao = nome_padrao  # Atualiza o último padrão encontrado
            return True  # Indica que um padrão foi encontrado
    return False

# Resetando a variável ao verificar novos resultados
def verificar_resultados(novas_cores):
    global ultima_jogada_id, sequencia_anterior, padroes_enviados_na_jogada

    # Verifica se a sequência mudou
    if len(novas_cores) > 0 and 'id' in novas_cores[0]:  # Verifica se existem novas cores e se 'id' é uma chave
        if ultima_jogada_id != novas_cores[0]['id']:  # Nova jogada
            ultima_jogada_id = novas_cores[0]['id']  # Atualiza o ID da última jogada
            ultima_cor = mapear_cor(novas_cores[0]['color'])  # Obtém a cor da nova jogada
            
            # Verifica se é um acerto
            if ultima_cor == sequencia_anterior[-1] or ultima_cor == "white":
                mensagem_win = f"WIN ✅✅ (acerto direto)" if ultima_cor == sequencia_anterior[-1] else f"WIN GALE ✅✅ (acerto gale)"
                print(mensagem_win)
                enviar_telegram(mensagem_win)
            else:
                mensagem_loss = f"LOSS ❌❌ (erro no gale)"
                print(mensagem_loss)
                enviar_telegram(mensagem_loss)

            # Reseta a lista de padrões enviados para a próxima jogada
            padroes_enviados_na_jogada = []

# Loop contínuo para monitoramento
while True:
    try:
        cores = obter_ultimas_cores()
        padrao_encontrado = verificar_padroes(cores)

        if padrao_encontrado:
            # Verifica resultados após encontrar um padrão
            while True:
                time.sleep(1)  # Espera 1 segundo antes de buscar a próxima cor
                novas_cores = obter_ultimas_cores()
                verificar_resultados(novas_cores)  # Aqui está a chamada corrigida
                if len(novas_cores) > 0 and novas_cores[0]['id'] != cores[0]['id']:  # Se a jogada mudou
                    break
        else:
            time.sleep(1)  # Atualiza a cada segundo caso nenhum padrão seja encontrado
    except Exception as e:
        print(f"Erro: {e}")
        time.sleep(5)
