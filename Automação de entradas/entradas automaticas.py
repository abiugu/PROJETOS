from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from alerta1 import alarme_acionado, cor_oposta

# Configurando o serviço do Chrome
chrome_service = Service()  # Substitua pelo caminho do seu chromedriver

# Configurando as opções do Chrome
chrome_options = Options()
# chrome_options.add_argument("--headless")  # Executar em modo headless (sem interface gráfica)

# Inicializando o driver do Chrome
driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

cor_button = None

# Abrindo a página de login
driver.get("https://blaze1.space/pt/games/double?modal=auth&tab=login")

# Aguarda o login manual e a mudança de URL para a página do jogo
while "?modal=auth&tab=login" in driver.current_url:
    time.sleep(1)

print("Login realizado com sucesso. Iniciando monitoramento de apostas...")

try:
    while True:
        try:
            # Acessa a página principal do jogo para monitorar a cor da última jogada
            driver.get("https://blaze1.space/pt/games/double")

            if cor_oposta == "black":
                cor_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "div.black"))
                )
            elif cor_oposta == "red":
                cor_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "div.red"))
                )
            elif cor_oposta == "white":
                cor_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "div.white"))
                )
            if cor_button:
                cor_button.click()
                # Inserir o valor no campo de Quantia
                valor_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.input-field-wrapper input.input-field"))
                )
                driver.execute_script("arguments[0].value = '10.00';", valor_field)
                # Verificar se a página está no estado "waiting" antes de clicar no botão "Começar o jogo"
                while True:
                    page_div = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div#roulette"))
                    )
                    page_state = page_div.get_attribute("class")
                    
                    if "page waiting" in page_state:
                        try:
                            comecar_jogo_button = WebDriverWait(driver, 5).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, "div.place-bet button:not([disabled])"))
                            )
                            comecar_jogo_button.click()
                            print("Aposta realizada. Aguardando próxima rodada...")
                            break
                        except Exception as e:
                            print(f"Erro ao tentar clicar no botão 'Começar o jogo': {e}")
                            time.sleep(2)  # Esperar 2 segundos antes de tentar novamente
                    else:
                        print("A página não está no estado 'waiting'. Aguardando próximo estado.")
                        time.sleep(5)  # Esperar 5 segundos antes de verificar o estado novamente
                # Aguardar 60 segundos após clicar no botão de aposta
                time.sleep(60)
            else:
                print("Não foi possível encontrar o botão da cor oposta.")


        except Exception as e:
            print(f"Erro ao tentar realizar a entrada: {e}")

        # Aguardar 30 segundos antes de verificar novamente
        time.sleep(30)

except KeyboardInterrupt:
    print("\nPrograma encerrado pelo usuário.")

finally:
    # Manter o navegador aberto para verificação manual
    print("Manter o navegador aberto para verificação manual.")
    while True:
        pass
