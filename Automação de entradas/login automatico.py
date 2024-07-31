from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Configurando o serviço do Chrome
chrome_service = Service()  # Substitua pelo caminho do seu chromedriver

# Configurando as opções do Chrome
chrome_options = Options()
# chrome_options.add_argument("--headless")  # Executar em modo headless (sem interface gráfica)

# Inicializando o driver do Chrome
driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

try:
    while True:
        # Abrindo a página do jogo
        driver.get("https://blaze1.space/pt/games/double")

        # Aguardando até que o elemento da última jogada esteja presente na página
        last_play_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".entries.main .entry .roulette-tile .sm-box"))
        )

        # Obtendo o estilo de cor do elemento
        style_attribute = last_play_element.get_attribute("style")

        # Verificando a cor baseada no estilo
        if "red" in style_attribute:
            cor_ultima_jogada = "red"
        elif "black" in style_attribute:
            cor_ultima_jogada = "black"
        elif "white" in style_attribute:
            cor_ultima_jogada = "white"
        else:
            cor_ultima_jogada = "cor não reconhecida"

        if cor_ultima_jogada == "red":
            # Escolher a cor preta
            cor_black_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "div.black.selected")))
            cor_black_button.click()

        elif cor_ultima_jogada == "black":
            # Escolher a cor vermelha
            cor_red_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "div.red.selected")))
            cor_red_button.click()

        # Inserir o valor no campo de Quantia
        valor_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.input-field-wrapper input.input-field")))
        driver.execute_script("arguments[0].setAttribute('value', '1.00');", valor_field)

        # Clicar no botão "Começar o jogo"
        comecar_jogo_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div.place-bet button")))
        comecar_jogo_button.click()

        # Aguardar um tempo antes de repetir o loop (opcional)
        time.sleep(10)  # Aguarda 10 segundos antes de verificar novamente

except KeyboardInterrupt:
    print("\nPrograma encerrado pelo usuário.")

except Exception as e:
    print(f"Erro ao tentar realizar a entrada: {e}")

# Manter o navegador aberto para verificação manual
while True:
    pass
