import os
import time
import datetime
import pytz
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import pygame

# Inicializando o serviço do Chrome
servico = Service()

# Configurando as opções do Chrome
opcoes = webdriver.ChromeOptions()
opcoes.add_argument("--headless")  # Executar em modo headless
opcoes.add_argument("--start-maximized")  # Maximizar a janela do navegador

# Inicializando o driver do Chrome
driver = webdriver.Chrome(service=servico, options=opcoes)

pygame.mixer.init()

# Carrega o arquivo de som
caminho_arquivo_som = "MONEY ALARM.mp3"

# Carrega o som
som_alarme = pygame.mixer.Sound(caminho_arquivo_som)

# Variável global para contar os alarmes
contagem_alarmes = 0

# Caminho da área de trabalho
caminho_area_trabalho = os.path.join(os.path.expanduser("~"), "Desktop")


def verificar_parada():
    caminho_parada = os.path.join(caminho_area_trabalho, "stop.txt")
    return os.path.exists(caminho_parada)

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

    select_elemento = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//select[@tabindex='0']")))
    select = Select(select_elemento)
    time.sleep(1)
    select.select_by_value(str(valor))
    time.sleep(1)

    elementos_texto_presentes = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.TAG_NAME, "text")))
    elementos_texto_visiveis = WebDriverWait(driver, 10).until(
        EC.visibility_of_all_elements_located((By.TAG_NAME, "text")))

    # Extrair apenas os valores de porcentagem e remover o símbolo '%'
    valores = [elemento.get_attribute("textContent") for elemento in elementos_texto_presentes
               if elemento.get_attribute("y") == "288" and "SofiaPro" in elemento.get_attribute("font-family")]
    percentuais = [float(valor.split('%')[0]) for valor in valores]

    return percentuais

# Função principal


def principal():
    global contagem_alarmes
    ultimo_tempo_alarme = datetime.datetime.now(
        pytz.timezone('America/Sao_Paulo'))
    try:
        url = 'https://blaze-7.com/pt/games/double'
        driver.get(url)

        while not verificar_parada():
            elemento_resultados_recentes = driver.find_element(
                By.ID, "roulette-recent")
            elementos_caixa = elemento_resultados_recentes.find_elements(
                By.CLASS_NAME, "sm-box")

            # Analisa as 15 últimas cores disponíveis
            sequencia = [caixa.get_attribute(
                "class").split()[-1] for caixa in elementos_caixa[:15]]

            # Verifica se há uma sequência de 3 cores iguais
            if len(set(sequencia[:2])) == 1:
                cor_atual = sequencia[0]
                cor_oposta = 'black' if cor_atual == 'red' else 'red'
                
                percentuais100 = extrair_cores(driver, 100)
                percentuais25 = extrair_cores(driver, 25)
                percentuais50 = extrair_cores(driver, 50)
                percentuais500 = extrair_cores(driver, 500)
                
                cor_atual_percentual_500 = None
                cor_oposta_percentual_500 = None
                cor_atual_percentual_100 = None
                cor_oposta_percentual_100 = None
                cor_atual_percentual_50 = None
                cor_oposta_percentual_50 = None
                cor_atual_percentual_25 = None
                cor_oposta_percentual_25 = None

                # Extrair percentuais apenas se a lista não estiver vazia
                if percentuais500:
                    cor_atual_percentual_500 = int(
                        percentuais500[['white', 'black', 'red'].index(cor_atual)])
                    cor_oposta_percentual_500 = int(
                        percentuais500[['white', 'black', 'red'].index(cor_oposta)])
                
                if percentuais100:
                    cor_atual_percentual_100 = int(
                        percentuais100[['white', 'black', 'red'].index(cor_atual)])
                    cor_oposta_percentual_100 = int(
                        percentuais100[['white', 'black', 'red'].index(cor_oposta)])

                if percentuais50:
                    cor_atual_percentual_50 = int(
                        percentuais50[['white', 'black', 'red'].index(cor_atual)])
                    cor_oposta_percentual_50 = int(
                        percentuais50[['white', 'black', 'red'].index(cor_oposta)])

                if percentuais25:
                    cor_atual_percentual_25 = int(
                        percentuais25[['white', 'black', 'red'].index(cor_atual)])
                    cor_oposta_percentual_25 = int(
                        percentuais25[['white', 'black', 'red'].index(cor_oposta)])

                if cor_atual_percentual_25 is not None and cor_atual_percentual_25 <= 44 and ((cor_atual_percentual_25 < cor_oposta_percentual_25 and
                                                                                               cor_atual_percentual_50 > cor_oposta_percentual_50 and
                                                                                               cor_atual_percentual_100 > cor_oposta_percentual_100 and
                                                                                               cor_atual_percentual_500 > cor_oposta_percentual_500) or
                                                                                              (cor_atual_percentual_25 > cor_oposta_percentual_25 and
                                                                                               cor_atual_percentual_50 < cor_oposta_percentual_50 and
                                                                                               cor_atual_percentual_100 < cor_oposta_percentual_100 and
                                                                                               cor_atual_percentual_500 < cor_oposta_percentual_500) or
                                                                                              (cor_atual_percentual_25 < cor_oposta_percentual_25 and
                                                                                               cor_atual_percentual_50 > cor_oposta_percentual_50 and
                                                                                               cor_atual_percentual_100 > cor_oposta_percentual_100 and
                                                                                               cor_atual_percentual_500 < cor_oposta_percentual_500) or
                                                                                              (cor_atual_percentual_25 < cor_oposta_percentual_25 and
                                                                                               cor_atual_percentual_50 < cor_oposta_percentual_50 and
                                                                                               cor_atual_percentual_100 > cor_oposta_percentual_100 and
                                                                                               cor_atual_percentual_500 < cor_oposta_percentual_500) or
                                                                                              (cor_atual_percentual_25 < cor_oposta_percentual_25 and
                                                                                               cor_atual_percentual_50 > cor_oposta_percentual_50 and
                                                                                               cor_atual_percentual_100 < cor_oposta_percentual_100 and
                                                                                               cor_atual_percentual_500 < cor_oposta_percentual_500)):
                    tempo_atual = datetime.datetime.now(
                        pytz.timezone('America/Sao_Paulo'))
                    # Verifica se já passou 2 minutos desde o último alarme para a mesma sequência
                    if (tempo_atual - ultimo_tempo_alarme).total_seconds() >= 120:
                        hora_atual = tempo_atual.strftime("%H:%M:%S")
                        data_atual = tempo_atual.strftime("%d-%m-%Y")  
                        som_alarme.play()
                        contagem_alarmes += 1
                        print(f"Alarme acionado. Contagem: {contagem_alarmes}")
                        print((f"PADRAO ENCONTRADO. {hora_atual}, {data_atual}"))

                        ultimo_tempo_alarme = tempo_atual  # Atualiza o tempo do último alarme

            time.sleep(1)

    except Exception as e:
        print(f"Erro: {e}")

    finally:
        # Finalizando o driver
        if driver:
            driver.quit()


# Chamando a função principal
if __name__ == "__main__":
    principal()
