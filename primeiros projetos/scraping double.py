from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time

# Configurações do ChromeDriver
service = Service()
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--disable-gpu')

# Caminho para a área de trabalho
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
txt_file_path = os.path.join(desktop_path, "resultados_double2.txt")

# Limitar o número de páginas a serem extraídas
limite_paginas = 1000  # Altere este valor conforme desejado

# Iniciar o WebDriver
driver = webdriver.Chrome(service=service, options=options)
wait = WebDriverWait(driver, 30)
try:
    # Navegar até a página inicial
    url = 'https://blaze.bet.br/pt/games/double?modal=double_history-v2_index&roomId=1'
    driver.get(url)
    print("Página carregada com sucesso.")

    # Fechar notificação "Eu tenho mais de 18 anos"
    try:
        botao_idade = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(text(), 'Eu tenho mais de 18 anos')]")))
        botao_idade.click()
        print("Botão 'Eu tenho mais de 18 anos' clicado.")
    except Exception as e:
        print("Botão 'Eu tenho mais de 18 anos' não encontrado ou já fechado.")

    # Fechar notificação "Aceitar todos os cookies"
    try:
        botao_cookies = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(text(), 'ACEITAR TODOS OS COOKIES')]")))
        botao_cookies.click()
        print("Botão 'Aceitar todos os cookies' clicado.")
    except Exception as e:
        print("Botão 'Aceitar todos os cookies' não encontrado ou já fechado.")

    # Avançar para a página final a partir da página inicial
    for i in range(limite_paginas - 1):
        try:
            botao_avanco = wait.until(EC.element_to_be_clickable((By.XPATH, "(//button[@class='pagination__button'])[2]")))
            botao_avanco.click()
            print(f"Avançando para a página {i + 2}")

        except Exception as e:
            print(f"Erro ao tentar avançar a página: {e}")
            break

    # Extrair dados e retroceder uma página por vez até a página inicial
    for pagina in range(limite_paginas):
        pagina_atual = limite_paginas - pagina  # Calcula a página atual de acordo com o loop
        print(f"Extraindo dados da página {pagina_atual}")

        # Espera até que o histórico de jogadas esteja carregado
        history_element = wait.until(EC.presence_of_element_located((By.ID, "history__double")))

        # Coleta todos os contêineres de jogadas
        container_elements = history_element.find_elements(By.CLASS_NAME, "history__double__container")
        container_elements.reverse()  # Inverte a ordem dos contêineres

        # Processa cada contêiner para extrair as informações de jogadas
        with open(txt_file_path, "a") as txt_file:
            for container_element in container_elements:
                try:
                    color_element = container_element.find_element(By.CLASS_NAME, "history__double__item")

                    # Identifica a cor com base na classe
                    color = "unknown"
                    if "history__double__item--black" in color_element.get_attribute("class"):
                        color = "black"
                    elif "history__double__item--white" in color_element.get_attribute("class"):
                        color = "white"
                    elif "history__double__item--red" in color_element.get_attribute("class"):
                        color = "red"

                    # Extrai o número e a hora
                    number = color_element.find_element(By.CLASS_NAME, "history__double__center").text
                    time_text = container_element.find_element(By.CLASS_NAME, "history__double__date").text.split('\n')[1]

                    # Concatenar os resultados e salvar no arquivo
                    result_line = f"Numero: {number}, Cor: {color} - {time_text}"
                    print(result_line)
                    txt_file.write(result_line + "\n")

                except Exception as e:
                    print(f"Erro ao extrair dados do contêiner: {e}")
                    continue

        # Retrocede para a página anterior, se não estiver na primeira página
        if pagina_atual > 1:
            try:
                botao_retrocesso = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "(//button[@class='pagination__button'])[1]")))
                botao_retrocesso.click()
                print(f"Retrocedendo para a página {pagina_atual - 1}")
                time.sleep(2)
            except Exception as e:
                print(f"Erro ao tentar retroceder a página: {e}")
                break

except Exception as e:
    print(f"Erro geral: {e}")

finally:
    driver.quit()
    print("Navegador fechado.")
