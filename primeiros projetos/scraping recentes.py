from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import os
import time

# Configurações do ChromeDriver
service = Service()
options = webdriver.ChromeOptions()

# Executar em modo headless (sem interface gráfica)
options.add_argument('--headless')
options.add_argument('--disable-gpu')

# Desativar carregamento de imagens para acelerar o processo
prefs = {"profile.managed_default_content_settings.images": 2}
options.add_experimental_option("prefs", prefs)

# Caminho para a área de trabalho
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")

# Caminho completo do arquivo .txt na área de trabalho
txt_file_path = os.path.join(desktop_path, "resultados_recentes.txt")

try:

    # Iniciar o WebDriver
    driver = webdriver.Chrome(service=service, options=options)

    # Navegar até a página principal do jogo "Double"
    url = 'https://blaze-7.com/pt/games/double'
    driver.get(url)

    # Adicionar lógica para encerrar o loop quando o arquivo "stop.txt" estiver presente
    while not os.path.exists(os.path.join(desktop_path, "stop.txt")):
        # Encontrar o elemento pelo ID 'roulette-recent'
        recent_results_element = driver.find_element(By.ID, "roulette-recent")

        # Encontrar todos os contêineres 'sm-box' dentro do elemento 'roulette-recent'
        box_elements = recent_results_element.find_elements(
            By.CLASS_NAME, "sm-box")

        # Processar cada contêiner para extrair informações
        with open(txt_file_path, "w") as txt_file:
            for i, box_element in enumerate(box_elements[:15]):
                # Verificar a classe do elemento para determinar a cor
                if "black" in box_element.get_attribute("class"):
                    color = "preto"
                elif "red" in box_element.get_attribute("class"):
                    color = "vermelho"
                elif "white" in box_element.get_attribute("class"):
                    color = "branco"
                else:
                    color = "desconhecido"

                # Encontrar o número dentro da classe 'number' se a cor não for branca
                if color != "branco":
                    number_element = box_element.find_element(
                        By.CLASS_NAME, "number")
                    number = number_element.text
                else:
                    number = "N/A"

                # Obter a data e hora atual
                current_datetime = time.strftime("%Y-%m-%d %H:%M:%S")

                # Concatenar os resultados em uma única linha
                result_line = f"Número: {number}, Cor: {
                    color}, Data e Hora: {current_datetime}"

                # Escrever no arquivo .txt
                txt_file.write(result_line + "\n")

                def verificar_stop():
                    # Verificar se o arquivo "stop.txt" existe no desktop
                    desktop_path = os.path.join(
                        os.path.expanduser("~"), "Desktop")
                    stop_file_path = os.path.join(desktop_path, "stop.txt")
                    return os.path.exists(stop_file_path)

        # Aguardar um intervalo de tempo antes de recomeçar o loop
        time.sleep(20)  # Espera 20 segundos antes de recomeçar

except Exception as e:
    print(f"Erro: {e}")

finally:
    # Fechar o navegador
    driver.quit()
