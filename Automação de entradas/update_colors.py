import requests
import json
import time

# URL da API
url = "https://blaze1.space/api/roulette_games/recent"

# Função para obter os dados da API
def api():
    try:
        # Solicita dados da API
        req = requests.get(url)
        req.raise_for_status()  # Verifica se houve erro na solicitação
        
        # Converte o conteúdo para um objeto Python (lista de dicionários)
        data = req.json()
        
        # Extrai os valores de "id" e "color"
        results = [{'id': item['id'], 'color': item['color']} for item in data]
        
        return results
    except requests.exceptions.RequestException as e:
        print(f"Erro ao obter dados: {e}")
        return []

# Função para salvar os dados no arquivo colors.json
def save_colors(results):
    try:
        with open('colors.json', 'w') as file:
            json.dump(results, file, indent=4)
        print("Dados atualizados no arquivo colors.json")
    except IOError as e:
        print(f"Erro ao salvar o arquivo: {e}")

# Função para ler o estado do alarme do arquivo estado_alarme.json
def ler_estado_alarme():
    try:
        with open('estado_alarme.json', 'r') as f:
            estado = json.load(f)
            alarme_acionado2 = estado.get('alarme_acionado2', False)
            return alarme_acionado2
    except FileNotFoundError:
        print("Arquivo estado_alarme.json não encontrado.")
        return False

# Função para atualizar o estado do alarme (desativá-lo, por exemplo)
def atualizar_estado_alarme(alarme_acionado2):
    estado = {
        'alarme_acionado2': alarme_acionado2
    }
    with open('estado_alarme.json', 'w') as f:
        json.dump(estado, f, indent=4)
    print(f"Estado do alarme atualizado: alarme_acionado2={alarme_acionado2}")

# Função para monitorar a mudança de cor e ID e fazer a ação desejada
def monitorar_jogadas():
    ultimo_id = None
    ultima_cor = None

    while True:
        # Atualiza o colors.json com os dados da API
        results = api()
        if results:
            save_colors(results)

            # Lê o estado do alarme
            alarme_acionado2 = ler_estado_alarme()

            # Se o alarme estiver acionado
            if alarme_acionado2:
                print("Alarme acionado, verificando a próxima jogada...")

                # Pega o último jogo salvo no colors.json (último resultado da API)
                id_atual = results[0]['id']
                cor_atual = results[0]['color']

                # Verifica se o ID é diferente do anterior e a cor é igual à anterior
                if ultimo_id and id_atual != ultimo_id and cor_atual == ultima_cor:
                    print(f"Condição atendida! ID anterior: {ultimo_id}, ID atual: {id_atual}, Cor repetida: {cor_atual}")
                    # Aqui você pode adicionar a lógica para fazer a "entrada" ou outra ação automatizada

                    # Após a ação, desative o alarme
                    atualizar_estado_alarme(False)

                # Atualiza o ID e a cor anteriores
                ultimo_id = id_atual
                ultima_cor = cor_atual
            else:
                print("Alarme não acionado.")
        
        # Aguarda 1 segundo antes de verificar novamente
        time.sleep(1)

if __name__ == "__main__":
    try:
        monitorar_jogadas()  # Executa o loop principal
    except KeyboardInterrupt:
        print("\nExecução interrompida manualmente.")
