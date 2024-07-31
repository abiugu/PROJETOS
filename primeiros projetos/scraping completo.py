from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import os
import time

# Configurações do ChromeDriver
service = Service()  # Substitua pelo caminho do seu chromedriver
options = Options()
# options.headless = True  # Executar em modo headless (sem interface gráfica)
options.add_argument('--disable-gpu')

# Desativar carregamento de imagens para acelerar o processo
prefs = {"profile.managed_default_content_settings.images": 2}
options.add_experimental_option("prefs", prefs)

# URL base
base_url = 'https://blaze1.space/pt/games/crash?modal=crash_history_index'

# Caminho para a área de trabalho
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")

# Caminho completo do arquivo .txt na área de trabalho
txt_file_path = os.path.join(desktop_path, "resultados_bets.txt")

# Iniciar o WebDriver
driver = webdriver.Chrome(service=service, options=options)

try:
    # Navegar até a página inicial do histórico de apostas
    driver.get(base_url)

    # Aguardar o carregamento completo da página
    driver.implicitly_wait(10)  # Espera implícita de até 10 segundos

    # Avançar até a página 10 (índice 9)
    for _ in range(0):
        prev_button = driver.find_element(By.CSS_SELECTOR, 'button.pagination__button svg[style*="rotate(180deg)"]')
        prev_button.click()
        time.sleep(1)  # Aguardar o carregamento completo da próxima página

    # Retroceder e extrair dados de cada página
    backward_pages = 2  # Retroceder até a primeira página
    while backward_pages > 0:
        # Encontrar todos os elementos de aposta 'bet'
        bet_elements = driver.find_elements(By.CSS_SELECTOR, 'div#history div.bet')

        # Inverter a lista de elementos para ler de baixo para cima
        bet_elements.reverse()

        # Processar cada elemento de aposta para extrair informações
        with open(txt_file_path, "a", encoding="utf-8") as txt_file:
            for bet_element in bet_elements:
                try:
                    # Encontrar o elemento de multiplicador (valor decimal)
                    multiplier_element = bet_element.find_element(By.CSS_SELECTOR, 'div.bet-amount')
                    multiplier = multiplier_element.text.strip()  # Remover espaços em branco

                    # Encontrar o elemento de data e hora
                    datetime_element = bet_element.find_element(By.TAG_NAME, 'p')
                    datetime_text = datetime_element.text.strip()  # Remover espaços em branco

                    # Concatenar os resultados em uma única linha
                    result_line = f"Multiplicador: {multiplier} - {datetime_text}"

                    # Escrever no arquivo .txt
                    txt_file.write(result_line + "\n")

                    # Imprimir no console para verificação
                    print(result_line)
                except Exception as e:
                    print(f"Erro ao processar aposta: {e}")

        # Verificar se há um botão de retrocesso
        if backward_pages > 1:
            next_button = driver.find_element(By.CSS_SELECTOR, 'button.pagination__button svg[style*="rotate(0deg)"]')
            next_button.click()
            time.sleep(1)  # Aguardar o carregamento completo da página anterior

        backward_pages -= 1

except Exception as e:
    print(f"Erro ao acessar a página: {e}")

finally:
    # Fechar o navegador
    driver.quit()
