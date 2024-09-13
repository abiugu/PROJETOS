import requests
import json

# URL da API
url = "https://blaze1.space/api/roulette_games/recent"

def api():
    try:
        # Solicita dados da API
        req = requests.get(url)
        req.raise_for_status()  # Verifica se houve erro na solicitação
        
        # Converte o conteúdo para um objeto Python
        data = req.json()
        
        # Extrai os valores de "id" e "color"
        results = [{'id': item['id'], 'color': item['color']} for item in data]
        
        return results
    except requests.exceptions.RequestException as e:
        print(f"Erro ao obter dados: {e}")
        return []

def save_colors(results):
    try:
        with open('colors.json', 'w') as file:
            file.write("results = ")
            json.dump(results, file, indent=4)
            file.write("\n")
        print("Dados salvos no arquivo colors.json")
    except IOError as e:
        print(f"Erro ao salvar o arquivo: {e}")

def main():
    results = api()
    if results:
        save_colors(results)
    else:
        print("Nenhum dado extraído.")

if __name__ == "__main__":
    main()
