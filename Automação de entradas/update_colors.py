import time
import json
import requests
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv

# URL da API Blaze
url = "https://blaze1.space/api/roulette_games/recent"

# Função para obter os dados da API
def api():
    try:
        req = requests.get(url)
        req.raise_for_status()
        data = req.json()
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
            cor_oposta = estado.get('cor_oposta', None)
            return alarme_acionado2, cor_oposta
    except FileNotFoundError:
        print("Arquivo estado_alarme.json não encontrado.")
        return False, None

# Função para atualizar o estado do alarme (desativá-lo, por exemplo)
def atualizar_estado_alarme(alarme_acionado2, cor_oposta):
    estado = {
        'alarme_acionado2': alarme_acionado2,
        'cor_oposta': cor_oposta
    }
    with open('estado_alarme.json', 'w') as f:
        json.dump(estado, f, indent=4)
    print(f"Estado do alarme atualizado: alarme_acionado2={alarme_acionado2}, cor_oposta={cor_oposta}")

# Função para realizar login no site Blaze
def realizar_login(email, senha):
    service = Service()
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(service=service, options=options)

    driver.get("https://blaze1.space/pt/games/double?modal=auth&tab=login")

    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "username")))
    email_input = driver.find_element(By.NAME, "username")
    email_input.send_keys(email)

    password_input = driver.find_element(By.NAME, "password")
    password_input.send_keys(senha)
    password_input.send_keys(Keys.RETURN)

    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="number"]')))
    return driver

# Função para realizar a aposta
def realizar_aposta(driver, valor_aposta, cor_aposta):
    try:
        # Localiza o campo de valor de entrada e insere o valor
        input_valor_aposta = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="number"]'))
        )
        input_valor_aposta.clear()
        input_valor_aposta.send_keys(valor_aposta)

        # Seleciona a cor correta
        cor_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, f'div.{cor_aposta}'))
        )
        cor_button.click()

        # Clicar no botão de "Apostar"
        apostar_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div.place-bet button"))
        )
        apostar_button.click()

        print(f"Aposta de {valor_aposta} na cor {cor_aposta} realizada com sucesso!")

    except Exception as e:
        # Imprime uma mensagem de erro e continua a execução
        print(f"Não foi possível realizar a aposta. Erro: {e}")



# Função principal que monitora as jogadas e realiza as apostas
def monitorar_jogadas(driver):
    ultimo_id = None
    ultima_cor = None

    while True:
        results = api()
        if results:
            save_colors(results)

            alarme_acionado2, cor_oposta = ler_estado_alarme()

            if alarme_acionado2:
                print("Alarme acionado, verificando a próxima jogada...")

                id_atual = results[0]['id']
                cor_atual = results[0]['color']

                # Define cor_oposta com base na cor_atual
                if cor_atual == 1:
                    cor_oposta = 'black'
                elif cor_atual == 2:
                    cor_oposta = 'red'
                else:
                    cor_oposta = None

                if ultimo_id and id_atual != ultimo_id and cor_atual == ultima_cor:
                    print(f"Condição atendida! ID anterior: {ultimo_id}, ID atual: {id_atual}, Cor repetida: {cor_atual}")

                    if cor_oposta:
                        realizar_aposta(driver, "2", cor_oposta)
                        realizar_aposta(driver, "0.5", "white")

                    atualizar_estado_alarme(False, cor_oposta)

                ultimo_id = id_atual
                ultima_cor = cor_atual
            else:
                print("Alarme não acionado.")

        time.sleep(1)

if __name__ == "__main__":
    load_dotenv(dotenv_path='C:/Users/abiug/PROJETOS/Login.Env')
    EMAIL = os.getenv('EMAIL')
    SENHA = os.getenv('SENHA')

    driver = realizar_login(EMAIL, SENHA)

    try:
        monitorar_jogadas(driver)
    except KeyboardInterrupt:
        print("\nExecução interrompida manualmente.")
    finally:
        driver.quit()
