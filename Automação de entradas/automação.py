import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import tkinter as tk
from tkinter import simpledialog

# Função para capturar email e senha usando uma janela do Tkinter
def get_login_details():
    root = tk.Tk()
    root.withdraw()  # Esconde a janela principal

    email = simpledialog.askstring("Login", "Digite seu email ou CPF:")
    senha = simpledialog.askstring("Senha", "Digite sua senha:", show='*')  # '*' para ocultar a senha durante a digitação

    return email, senha

# Função principal com Selenium
def realizar_login(email, senha):
 # Inicializando o serviço do Chrome
    service = Service()

    # Inicializa o navegador Chrome
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

# Obtém o email e senha através da janela Tkinter
email, senha = get_login_details()

# Realiza o login com os dados obtidos
realizar_login(email, senha)
time.sleep(5)
input("Login feito com sucesso !")

 # Inicializando o serviço do Chrome
service = Service()

    # Inicializa o navegador Chrome
options = webdriver.ChromeOptions()
driver = webdriver.Chrome(service=service, options=options)

# Após o alarme, realiza a aposta
# 1. Preencher o valor da entrada
valor_aposta = input("Digite o valor da entrada: ")

# Localiza o campo de valor de entrada e insere o valor
input_valor_aposta = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="number"]'))
)
input_valor_aposta.clear()
input_valor_aposta.send_keys(valor_aposta)

# 2. Selecionar a cor
cor_aposta = input("Selecione a cor (red, white, black): ").lower()

if cor_aposta == "red":
    cor_button = driver.find_element(By.CSS_SELECTOR, ".red")
elif cor_aposta == "white":
    cor_button = driver.find_element(By.CSS_SELECTOR, ".white")
elif cor_aposta == "black":
    cor_button = driver.find_element(By.CSS_SELECTOR, ".black")
else:
    print("Cor inválida!")
    driver.quit()
    exit()

# Clicar na cor escolhida
cor_button.click()

# 3. Clicar no botão de "Apostar"
apostar_button = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.CSS_SELECTOR, "div.place-bet button"))
)
apostar_button.click()

print("Aposta realizada com sucesso!")

# Mantém o navegador aberto por mais alguns segundos para verificar se a aposta foi feita
time.sleep(5)

# Fecha o navegador
driver.quit()
