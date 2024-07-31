from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

# Configuração do WebDriver (certifique-se de ter o WebDriver instalado e configurado)
service = Service()
options = webdriver.ChromeOptions()
#options.add_argument("--headless")  # Executar em modo headless
options.add_argument("--start-maximized")  # Maximizar a janela do navegador
driver = webdriver.Chrome(service=service, options=options)

# Abrir o site
entrar_button = driver.find_element(By.XPATH, "//a[contains(text(), 'Entrar')]")
entrar_button.click()

# Esperar um pouco para a página carregar
time.sleep(3)

# Preencher o campo de CPF ou Endereço de Email
cpf_email_field = driver.find_element(By.CSS_SELECTOR, ".input-style-1.undefined.status-visible.false.undefined")
cpf_email_field.clear()  # Limpa o campo
cpf_email_field.send_keys('abiugu@gmail.com')

# Preencher o campo de senha
senha_field = driver.find_element(By.XPATH, "//input[@placeholder='Senha']")
senha_field.clear()  # Limpa o campo
senha_field.send_keys('Abiugu0203@')

# Esperar um pouco para garantir que todos os dados sejam inseridos antes de enviar
time.sleep(2)

# Submeter o formulário (pressionar Enter no campo de senha)
senha_field.submit()

# Esperar alguns segundos para a página carregar após o login
time.sleep(5)

# Fechar o navegador quando terminar
driver.quit()