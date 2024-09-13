import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
import os
import json

# Função para carregar o estado do arquivo JSON
def ler_estado_alarme():
    try:
        with open('estado_alarme.json', 'r') as f:
            estado = json.load(f)
            alarme_acionado2 = estado['alarme_acionado2']
            cor_oposta = estado['cor_oposta']
            print(f"Alarme acionado: {alarme_acionado2}, Cor oposta: {cor_oposta}")  # Adiciona o print
            return alarme_acionado, cor_oposta
    except FileNotFoundError:
        print("Arquivo JSON não encontrado.")  # Exibe uma mensagem se o arquivo não for encontrado
        return False, None
    

# Função para realizar login
def realizar_login(email, senha):
    # Inicializando o serviço do Chrome
    service = Service()
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(service=service, options=options)

    # Acessa a página de login no Blaze
    driver.get("https://blaze1.space/pt/games/double?modal=auth&tab=login")

    # Espera a página de login carregar e faz o login
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "username"))
    )
    email_input = driver.find_element(By.NAME, "username")
    email_input.send_keys(email)

    password_input = driver.find_element(By.NAME, "password")
    password_input.send_keys(senha)
    password_input.send_keys(Keys.RETURN)

    # Espera o login ser concluído
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="number"]'))
    )

    return driver

# Função para realizar a aposta
def realizar_aposta(driver, valor_aposta, cor_aposta):
    # Localiza o campo de valor de entrada e insere o valor
    input_valor_aposta = WebDriverWait(driver, 2).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="number"]'))
    )
    input_valor_aposta.clear()
    input_valor_aposta.send_keys(valor_aposta)

    # Seleciona a cor correta
    cor_button = WebDriverWait(driver, 2).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, f'div.{cor_aposta}'))
    )
    cor_button.click()

    # Clicar no botão de "Apostar"
    apostar_button = WebDriverWait(driver, 2).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "div.place-bet button"))
    )
    apostar_button.click()

    print(f"Aposta de {valor_aposta} na cor {cor_aposta} realizada com sucesso!")

# Carregar variáveis de ambiente (login e senha)
load_dotenv(dotenv_path='C:/Usuários/abiug/PROJETOS/Login.Env')
EMAIL = os.getenv('EMAIL')
SENHA = os.getenv('SENHA')

# Realiza o login no site
driver = realizar_login(EMAIL, SENHA)

# Loop principal para verificar o estado do alarme e realizar as apostas
while True:
    # Lê o estado do arquivo JSON
    alarme_acionado, cor_oposta = ler_estado_alarme()

    if alarme_acionado:
        # Realiza a aposta na cor oposta com R$10
        realizar_aposta(driver, "2", cor_oposta)
        # Realiza a aposta no branco com R$1
        realizar_aposta(driver, "0,5", "white")

        print("Aguardando o próximo acionamento do alarme...")

    # Aguarda um tempo antes de verificar novamente
    time.sleep(2)

    # Mantém o navegador aberto para inspeção
    print("Navegador aberto. Pressione Enter para fechar...")
    input()
    
    # Fecha o navegador após o teste
    driver.quit()