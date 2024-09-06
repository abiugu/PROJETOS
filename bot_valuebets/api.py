import requests
import json

# Sua chave de API
API_KEY = 'd12248201deb6c89b973388462b6ad86'
REGIONS = ['uk', 'eu', 'au', 'us']

def obter_esportes(api_key):
    url = 'https://api.the-odds-api.com/v4/sports'
    params = {'apiKey': api_key}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as err:
        print(f"Erro ao buscar esportes: {err}")
        return []

def obter_odds_por_esporte(api_key, esporte, regions, markets='h2h'):
    odds = []
    for region in regions:
        url = f'https://api.the-odds-api.com/v4/sports/{esporte}/odds'
        params = {'regions': region, 'markets': markets, 'apiKey': api_key}
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            dados = response.json()
            # Adiciona uma mensagem para inspecionar a estrutura dos dados
            print(f"Dados recebidos para o esporte {esporte} na região {region}:")
            print(json.dumps(dados, indent=2))
            odds.extend(dados)
        except requests.exceptions.HTTPError as err:
            print(f"Erro ao buscar odds para o esporte {esporte} na região {region}: {err}")
    return odds

def calcular_percentual_acima_da_media(maior_odd, odds_media):
    if odds_media == 0:
        return 0
    return round(((maior_odd - odds_media) / odds_media) * 100, 2)

def processar_odds(eventos):
    resultados = []
    for evento in eventos:
        try:
            nome_evento = evento['home_team'] + ' vs ' + evento['away_team']
            odds_casas = []
            for bookmaker in evento.get('bookmakers', []):
                odds_bookmaker = bookmaker.get('markets', [{}])[0].get('outcomes', [])
                for outcome in odds_bookmaker:
                    odd = outcome.get('price')
                    if odd and odd < 5:  # Filtra odds menores que 5
                        odds_casas.append({
                            'bookmaker': bookmaker.get('title', 'Desconhecido'),
                            'outcome': outcome.get('name', 'Desconhecido'),
                            'odd': odd
                        })
            if odds_casas:
                maior_odd = max(odds_casas, key=lambda x: x['odd'])
                odds_media = sum(casa['odd'] for casa in odds_casas) / len(odds_casas)
                percentual_acima_media = calcular_percentual_acima_da_media(maior_odd['odd'], odds_media)
                print(f"Evento: {nome_evento}, Maior Odd: {maior_odd['odd']}, Percentual Acima da Média: {percentual_acima_media}%")
                if percentual_acima_media > 50:  # Filtra percentuais acima de 50%
                    resultados.append({
                        'evento': nome_evento,
                        'maior_odd': maior_odd['odd'],
                        'bookmaker': maior_odd['bookmaker'],
                        'percentual_acima_media': percentual_acima_media
                    })
            else:
                print(f"Nenhuma odd válida para o evento: {nome_evento}")
        except Exception as e:
            print(f"Erro ao processar evento: {evento}. Erro: {e}")
    return sorted(resultados, key=lambda x: x['percentual_acima_media'], reverse=True)[:100]

def salvar_em_arquivo(nome_arquivo, conteudo):
    with open(nome_arquivo, 'w', encoding='utf-8') as f:
        json.dump(conteudo, f, ensure_ascii=False, indent=4)

def main():
    try:
        esportes = obter_esportes(API_KEY)
        if not esportes:
            print("Nenhum esporte disponível ou erro na consulta.")
            return

        resultados = []
        for esporte in esportes:
            nome_esporte = esporte['key']
            print(f"Obtendo odds para o esporte: {nome_esporte}")
            odds_por_regiao = obter_odds_por_esporte(API_KEY, nome_esporte, REGIONS)
            eventos = [evento for odds in odds_por_regiao for evento in odds]
            print(f"Total de eventos encontrados para {nome_esporte}: {len(eventos)}")
            if not eventos:
                continue
            top_100_resultados = processar_odds(eventos)
            resultados.extend(top_100_resultados)
        salvar_em_arquivo('top_100_odds.json', resultados)
        print("Resultados salvos em top_100_odds.json")
    except Exception as e:
        print(f"Erro ao buscar dados: {e}")

if __name__ == "__main__":
    main()
