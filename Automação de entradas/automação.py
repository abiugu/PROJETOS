import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
import os

# Carregar variáveis de ambiente do arquivo .env
load_dotenv(dotenv_path='C:/Users/abiug/PROJETOS/Login.Env')

# Obter variáveis de ambiente
EMAIL = os.getenv('EMAIL')
SENHA = os.getenv('SENHA')


# Função para realizar login
def realizar_login(email, senha):
    # Inicializando o serviço do Chrome
    service = Service()  # Atualize o caminho para o seu chromedriver
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(service=service, options=options)

    # Acessa a página de login no Blaze
    driver.get("https://blaze1.space/pt/games/double?modal=auth&tab=login")

    # Espera a página de login carregar
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "username"))
    )

    # Preenche o login e a senha
    email_input = driver.find_element(By.NAME, "username")
    email_input.send_keys(email)

    password_input = driver.find_element(By.NAME, "password")
    password_input.send_keys(senha)

    # Pressiona Enter ou clica no botão de login
    password_input.send_keys(Keys.RETURN)

    # Espera até que o login seja realizado (pode-se ajustar o tempo de espera)
    time.sleep(5)

    return driver

# Realiza o login com os dados obtidos do arquivo .env
driver = realizar_login(EMAIL, SENHA)

# Após o login, continue com o restante do código
valor_aposta = input("Digite o valor da entrada: ")

# Localiza o campo de valor de entrada e insere o valor
input_valor_aposta = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="number"]'))
)
input_valor_aposta.clear()
input_valor_aposta.send_keys(valor_aposta)

# Selecionar a cor
cor_aposta = input("Selecione a cor (red, white, black): ").lower()

if cor_aposta == "red":
    cor_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'input-wrapper') and .//div[text()='x2' and @style='background-color: rgb(241, 44, 76);']]"))
    )
elif cor_aposta == "white":
    cor_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'input-wrapper') and .//div[text()='x14' and @style='background-color: rgb(255, 255, 255);']]"))
    )
elif cor_aposta == "black":
    cor_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'input-wrapper') and .//div[text()='x2' and @style='background-color: rgb(0, 0, 0);']]"))
    )
else:
    print("Cor inválida!")
    driver.quit()
    exit()

# Clicar na cor escolhida
cor_button.click()

# Clicar no botão de "Apostar"
apostar_button = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.CSS_SELECTOR, "div.place-bet button"))
)
apostar_button.click()

print("Aposta realizada com sucesso!")

# Mantém o navegador aberto por mais alguns segundos para verificar se a aposta foi feita
time.sleep(5)

# Fecha o navegador
driver.quit()
