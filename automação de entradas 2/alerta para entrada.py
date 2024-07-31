import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import pygame

def verificar_stop():
    stop_path = os.path.join(desktop_path, "stop.txt")
    return os.path.exists(stop_path)

# Inicializando o serviço do Chrome
service = Service()

# Configurando as opções do Chrome
options = webdriver.ChromeOptions()
#options.add_argument("--headless")  # Executar em modo headless
options.add_argument("--start-maximized")  # Maximizar a janela do navegador

# Inicializando o driver do Chrome
driver = webdriver.Chrome(service=service, options=options)

pygame.mixer.init()

# Carrega o arquivo de som
sound_file_path = "MONEY ALARM.mp3"

# Carrega o som
alarm_sound = pygame.mixer.Sound(sound_file_path)

# Variável global para contar os alarmes
count_alarm = 0

# Caminho da área de trabalho
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")


# Função para extrair as porcentagens das cores
def extrair_cores(driver, valor):
    # Abrir o site se ainda não estiver aberto
    if driver.current_url != "https://blaze1.space/pt/games/double?modal=double_history_index":
        driver.get(
            "https://blaze1.space/pt/games/double?modal=double_history_index")
        # Aguarda até 5 segundos para elementos aparecerem
        driver.implicitly_wait(5)

        # Esperar até que a div "tabs-crash-analytics" esteja visível
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located(
            (By.CLASS_NAME, "tabs-crash-analytics")))

        # Clicar no botão "Padrões" dentro da div "tabs-crash-analytics"
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
            (By.XPATH, ".//button[text()='Padrões']"))).click()

        # Esperar até que o botão "Padrões" se torne ativo
        WebDriverWait(driver, 10).until(EC.presence_of_element_located(
            (By.XPATH, "//button[@class='tab active']")))

    select_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//select[@tabindex='0']")))
    select = Select(select_element)
    time.sleep(1)
    select.select_by_value(str(valor))
    time.sleep(1)

    text_elements_present = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.TAG_NAME, "text")))
    text_elements_visible = WebDriverWait(driver, 10).until(
        EC.visibility_of_all_elements_located((By.TAG_NAME, "text")))

    # Extrair apenas os valores de porcentagem e remover o símbolo '%'
    valores = [element.get_attribute("textContent") for element in text_elements_present
               if element.get_attribute("y") == "288" and "SofiaPro" in element.get_attribute("font-family")]
    percentuais = [float(valor.split('%')[0]) for valor in valores]

    return percentuais
# Função principal
def main():
    global count_alarm

    try:
        url = 'https://blaze-7.com/pt/games/double'
        driver.get(url)

        while not verificar_stop():
            recent_results_element = driver.find_element(By.ID, "roulette-recent")
            box_elements = recent_results_element.find_elements(By.CLASS_NAME, "sm-box")

            # Analisa as 15 últimas cores disponíveis
            sequencia = [box_element.get_attribute("class").split()[-1] for box_element in box_elements[:15]]
            
            percentuais50 = extrair_cores(driver, 50)
            percentuais25 = extrair_cores(driver, 25)    

            # Verifica se há uma sequência de 3 cores iguais
            if len(set(sequencia[:3])) == 1:
                cor_atual = sequencia[0]
                cor_oposta = 'black' if cor_atual == 'red' else 'red'
                cor_atual_percentual_25 = int(percentuais25[['white', 'black', 'red'].index(cor_atual)])

                if cor_atual_percentual_25 is not None and cor_atual_percentual_25 <= 48:
                    alarm_sound.play()
                    count_alarm += 1
                    print(f"Alarme acionado. Contagem: {count_alarm}")
                    print(f"PADRAO ENCONTRADO: Três cores iguais ({cor_atual})")

            time.sleep(1)

    except Exception as e:
        print(f"Erro: {e}")

    finally:
        # Finalizando o driver
        if driver:
            driver.quit()

# Chamando a função principal
if __name__ == "__main__":
    main()
