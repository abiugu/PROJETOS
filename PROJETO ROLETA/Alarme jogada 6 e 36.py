import os
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from playsound import playsound

# Obtém o caminho do desktop
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")

# Configuração do driver
driver_path = os.path.join(desktop_path, "chromedriver")  # Certifique-se de colocar o ChromeDriver no desktop
url = "https://gamblingcounting.com/pt-BR/immersive-roulette"

# Configuração do alarme
alarme_path = os.path.join(desktop_path, "alarme.mp3")  # Certifique-se de colocar o arquivo de alarme no desktop
jogada_especifica = "6", "36"  # Número que você está monitorando

def monitorar_roulette():
    driver = webdriver.Chrome(driver_path)
    driver.get(url)
    
    try:
        while True:
            # Localiza a jogada mais recente
            try:
                elemento = driver.find_element(By.CSS_SELECTOR, 
                    ".live-game-page__block__results .roulette-number")
                jogada_atual = elemento.text.strip()
                
                print(f"Jogada atual: {jogada_atual}")  # Para depuração
                
                # Verifica se a jogada atende à condição
                if jogada_atual in jogada_especifica:
                    print("Jogada específica detectada! Tocando alarme...")
                    playsound(alarme_path)
                    break  # Sai do loop após tocar o alarme

            except Exception as e:
                print(f"Erro ao obter a jogada: {e}")

            # Aguarda antes de verificar novamente
            time.sleep(1)
    finally:
        driver.quit()

# Inicia o monitoramento
if __name__ == "__main__":
    monitorar_roulette()
