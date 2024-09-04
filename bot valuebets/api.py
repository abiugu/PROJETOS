import requests
import time
import os

# Configurações da API
API_KEY = os.getenv('API_KEY')
BASE_URL = 'https://api.the-odds-api.com/v4/sports/upcoming/odds/'
REGIONS = 'uk'
MARKETS = 'h2h'
ODDS_FORMAT = 'decimal'
THRESHOLD_VALUE = 0.05  # Valor mínimo para considerar uma *value bet*

# Função para fazer a chamada à API e obter as odds


def obter_odds():
    params = {
        'regions': REGIONS,
        'markets': MARKETS,
        'apiKey': API_KEY,
        'oddsFormat': ODDS_FORMAT
    }
    response = requests.get(BASE_URL, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print('Erro ao buscar dados:', response.status_code)
        return []

# Função para calcular a probabilidade implícita a partir da odd


def calc_probabilidade_implicita(odd):
    return 1 / odd

# Estimar probabilidade real (simplificada)


def estimar_probabilidade_real():
    # Aqui, você pode integrar um modelo mais complexo
    return 0.55  # Exemplo: 55% de chance de vitória

# Função para identificar *value bets*


def identificar_value_bets(jogos):
    value_bets = []
    for jogo in jogos:
        for bookmaker in jogo['bookmakers']:
            for outcome in bookmaker['markets'][0]['outcomes']:
                odd = outcome['price']
                probabilidade_implicita = calc_probabilidade_implicita(odd)
                probabilidade_real = estimar_probabilidade_real()
                valor = calcular_valor(odd, probabilidade_real)

                if valor > THRESHOLD_VALUE:
                    value_bets.append({
                        'evento': jogo['home_team'] + ' vs ' + jogo['away_team'],
                        'bookmaker': bookmaker['title'],
                        'outcome': outcome['name'],
                        'odd': odd,
                        'valor': valor
                    })
    return value_bets

# Função para calcular o valor de uma *value bet*


def calcular_valor(odd, probabilidade_real):
    return (probabilidade_real * odd) - 1

# Loop principal para verificar as odds periodicamente


def executar_bot():
    while True:
        jogos = obter_odds()
        value_bets = identificar_value_bets(jogos)

        if value_bets:
            for bet in value_bets:
                print(f"Value Bet encontrada: {bet['evento']} - {bet['outcome']} com odd {
                      bet['odd']} na {bet['bookmaker']}. Valor: {bet['valor']:.2f}")
        else:
            print("Nenhuma Value Bet encontrada.")

        time.sleep(60)  # Verifica novamente a cada 60 segundos


# Executa o bot
executar_bot()
