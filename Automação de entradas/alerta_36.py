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
import json

# Inicializando o serviço do Chrome
service = Service()

# Configurando as opções do Chrome
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Executar em modo headless
options.add_argument("--disable-gpu")

# Inicializando o driver do Chrome
driver = webdriver.Chrome(service=service, options=options)

# Variáveis globais
count_alarm = 0
acertos_direto = 0
acertos_gale = 0
erros = 0
last_alarm_time = 0  # Inicializar last_alarm_time
alarme_acionado = False  # Inicializa o estado do alarme como falso
alarme_acionado2 = False
acertos_branco = 0
acertos_gale_branco = 0

# Caminho da área de trabalho
desktop_path = os.path.join(os.path.expanduser("~"), 'Desktop')

# Pasta de logs
logs_path = os.path.join(desktop_path, "LOGS")

# Caminho completo para o arquivo de log
log_file_path = os.path.join(logs_path, "log 36.txt")

# Inicializa o mixer de áudio do pygame
pygame.mixer.init()

# Carrega o arquivo de som
sound_file_path = "ENTRADA CONFIRMADA.mp3"
sound_file_path2 = "MONEY ALARM.mp3"

# Carrega o som
alarm_sound = pygame.mixer.Sound(sound_file_path)
alarm_sound2 = pygame.mixer.Sound(sound_file_path2)

# Arquivo de log interativo
log_interativo_path = os.path.join(logs_path, "log interativo 36.txt")

# Dicionário para armazenar valores anteriores
valores_anteriores = {"acertos_direto": 0, "acertos_gale": 0, "erros": 0}

# Função para registrar mensagens no arquivo de log
def log_to_file(message):
    with open(log_file_path, "a") as log_file:
        log_file.write(message + "\n")

# Função para verificar se o arquivo stop.txt existe
def verificar_stop():
    stop_path = os.path.join(desktop_path, "stop.txt")
    return os.path.exists(stop_path)

def atualizar_json_alarme(alarme_acionado2):
    with open('estado_alarme.json', 'w') as f:
        json.dump({'alarme_acionado': alarme_acionado2}, f)
    print(f"JSON atualizado: alarme_acionado={alarme_acionado2}")

# Função para extrair as porcentagens das cores
def extrair_cores(driver, valor):
    # Abrir o site se ainda não estiver aberto
    if driver.current_url != "https://blaze1.space/pt/games/double?modal=double_history_index":
        driver.get("https://blaze1.space/pt/games/double?modal=double_history_index")
        driver.implicitly_wait(5)
        
        # Esperar até que a div "tabs-crash-analytics" esteja visível
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CLASS_NAME, "tabs-crash-analytics")))

        # Clicar no botão "Padrões" dentro da div "tabs-crash-analytics"
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//button[text()='Padrões']"))).click()

        # Esperar até que o botão "Padrões" se torne ativo
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//button[@class='tab active']")))

    select_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//select[@tabindex='0']")))
    select = Select(select_element)
    time.sleep(1)
    select.select_by_value(str(valor))
    time.sleep(1)

    text_elements_present = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.TAG_NAME, "text")))
    text_elements_visible = WebDriverWait(driver, 10).until(EC.visibility_of_all_elements_located((By.TAG_NAME, "text")))

    # Extrair apenas os valores de porcentagem e remover o símbolo '%'
    valores = [element.get_attribute("textContent") for element in text_elements_present
               if element.get_attribute("y") == "288" and "SofiaPro" in element.get_attribute("font-family")]
    percentuais = [float(valor.split('%')[0]) for valor in valores]

    return percentuais

# Função para atualizar o log interativo
def atualizar_log_interativo(acertos_direto, acertos_branco, erros):
    with open(log_interativo_path, "w") as log_interativo_file:
        log_interativo_file.write("=== LOG INTERATIVO ===\n")
        log_interativo_file.write(f"Acertos diretos: {acertos_direto}\n")
        log_interativo_file.write(f"Acertos branco: {acertos_branco}\n")
        log_interativo_file.write(f"Erros: {erros}\n")
        entrada_direta = int(acertos_direto - (acertos_branco + erros))
        entrada_branco = int((acertos_branco * 13) - (acertos_direto + erros))
        entrada_dupla = int((acertos_direto + acertos_branco) - (erros * 1.34))
        log_interativo_file.write(f"Entrada direta: {entrada_direta}\n")
        log_interativo_file.write(f"Entrada branco: {entrada_branco}\n")
        log_interativo_file.write(f"Entrada dupla: {entrada_dupla}\n")

# Função para verificar padrões e fazer entradas
def verificar_e_entrar_padroes(sequencia, driver):
    padroes = {
        "padrao_5": (["white", "white", "black"], ["red", "white"]),
        "padrao_7": (["black", "black", "white", "red", "black"], ["black", "white"]),
        "padrao_8": (["red", "red", "white", "black", "red"], ["red", "white"])
    }

    for nome_padroes, (padrao_sequencia, cores_entrada) in padroes.items():
        if sequencia[-len(padrao_sequencia):] == padrao_sequencia:
            cor_entrada = cores_entrada[0]  # Exemplo: escolher a primeira cor
            print(f"Reconhecido: {nome_padroes}, fazendo entrada na cor {cor_entrada}.")
            # Aqui você deve adicionar a lógica para fazer a entrada na cor específica
            # Exemplo: driver.find_element(...) para clicar na cor
            return cor_entrada

    return None

# Função principal
def main():
    global count_alarm, acertos_direto, erros, last_alarm_time, alarme_acionado, alarme_acionado2, acertos_branco, acertos_gale_branco
    last_alarm_time = time.time()  # Inicializa o tempo do último alarme

    # Variável para armazenar a última sequência de cores registrada no log
    ultima_sequencia_log = None

    try:
        url = 'https://blaze-7.com/pt/games/double'
        driver.get(url)

        while not verificar_stop():
            recent_results_element = driver.find_element(By.ID, "roulette-recent")
            box_elements = recent_results_element.find_elements(By.CLASS_NAME, "sm-box")

            # Analisa as 15 últimas cores disponíveis
            sequencia = [box_element.get_attribute("class").split()[-1] for box_element in box_elements[:15]]

            # Verifica se houve uma mudança na sequência de cores
            if 'sequencia_anterior' not in locals() or sequencia != sequencia_anterior:
                # Verifica se a sequência de cores é diferente da última registrada no log
                if sequencia != ultima_sequencia_log:
                    ultima_sequencia_log = sequencia  # Atualiza a última sequência registrada no log

                    percentuais100 = extrair_cores(driver, 100)
                    percentuais25 = extrair_cores(driver, 25)
                    percentuais50 = extrair_cores(driver, 50)
                    percentuais500 = extrair_cores(driver, 500)

                    log_to_file("Ultimos 3 resultados: " + ', '.join(sequencia[:3]))
                    log_to_file("Ultimas 25 porcentagens: " + ', '.join(map(str, percentuais25)))
                    log_to_file("Ultimas 50 porcentagens: " + ', '.join(map(str, percentuais50)))
                    log_to_file("Ultimas 100 porcentagens: " + ', '.join(map(str, percentuais100)))
                    log_to_file("Ultimas 500 porcentagens: " + ', '.join(map(str, percentuais500)))

                    cor_entrada = verificar_e_entrar_padroes(sequencia, driver)
                    if cor_entrada:
                        # Aqui você pode inserir a lógica para entrar na cor determinada
                        # Por exemplo: driver.find_element(...) para clicar na cor
                        pass

                # Atualiza a sequência anterior
                sequencia_anterior = sequencia

            # Espera um segundo antes de verificar novamente
            time.sleep(1)

    except Exception as e:
        print(f"Ocorreu um erro: {e}")
        log_to_file(f"Erro: {str(e)}")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
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
import json

# Variáveis globais
count_alarm = 0
acertos_direto = 0
acertos_gale = 0
erros = 0
last_alarm_time = 0  # Inicializar last_alarm_time
alarme_acionado = False  # Inicializa o estado do alarme como falso
alarme_acionado2 = False
acertos_branco = 0
acertos_gale_branco = 0

# Caminho da área de trabalho
desktop_path = os.path.join(os.path.expanduser("~"), 'Desktop')

# Pasta de logs
logs_path = os.path.join(desktop_path, "LOGS")

# Caminho completo para o arquivo de log
log_file_path = os.path.join(logs_path, "log 36.txt")

# Inicializa o mixer de áudio do pygame
pygame.mixer.init()

# Carrega os arquivos de som
sound_file_path = "ENTRADA CONFIRMADA.mp3"
sound_file_path2 = "MONEY ALARM.mp3"

# Carrega o som
alarm_sound = pygame.mixer.Sound(sound_file_path)
alarm_sound2 = pygame.mixer.Sound(sound_file_path2)

# Função para registrar logs em arquivo
def log_to_file(message):
    with open(log_file_path, "a") as log_file:
        log_file.write(message + "\n")

# Função para verificar se o script deve parar
def verificar_stop():
    stop_path = os.path.join(desktop_path, "stop.txt")
    return os.path.exists(stop_path)

# Função para atualizar o estado do alarme em um arquivo JSON
def atualizar_json_alarme(alarme_acionado2):
    with open('estado_alarme.json', 'w') as f:
        json.dump({'alarme_acionado': alarme_acionado2}, f)
    print(f"JSON atualizado: alarme_acionado={alarme_acionado2}")

# Função para extrair cores e porcentagens
def extrair_cores(driver, valor):
    # Abrir o site se ainda não estiver aberto
    if driver.current_url != "https://blaze1.space/pt/games/double?modal=double_history_index":
        driver.get("https://blaze1.space/pt/games/double?modal=double_history_index")
        driver.implicitly_wait(5)

        # Esperar até que a div "tabs-crash-analytics" esteja visível
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CLASS_NAME, "tabs-crash-analytics")))

        # Clicar no botão "Padrões"
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//button[text()='Padrões']"))).click()

        # Esperar até que o botão "Padrões" se torne ativo
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//button[@class='tab active']")))
    
    select_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//select[@tabindex='0']")))
    select = Select(select_element)
    time.sleep(1)
    select.select_by_value(str(valor))
    time.sleep(1)

    text_elements_present = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.TAG_NAME, "text")))
    
    # Extrair apenas os valores de porcentagem e remover o símbolo '%'
    valores = [element.get_attribute("textContent") for element in text_elements_present
               if element.get_attribute("y") == "288" and "SofiaPro" in element.get_attribute("font-family")]
    percentuais = [float(valor.split('%')[0]) for valor in valores]

    return percentuais

# Função para atualizar o log interativo
def atualizar_log_interativo(acertos_direto, acertos_branco, erros):
    log_interativo_path = os.path.join(desktop_path, "LOGS", "log_interativo.txt")
    with open(log_interativo_path, "w") as log_interativo_file:
        log_interativo_file.write("=== LOG INTERATIVO ===\n")
        log_interativo_file.write(f"Acertos diretos: {acertos_direto}\n")
        log_interativo_file.write(f"Acertos branco: {acertos_branco}\n")
        log_interativo_file.write(f"Erros: {erros}\n")
        entrada_direta = int(acertos_direto - (acertos_branco + erros))
        entrada_branco = int((acertos_branco * 13) - (acertos_direto + erros))
        entrada_dupla = int((acertos_direto + acertos_branco) - (erros * 1.34))
        log_interativo_file.write(f"Entrada direta: {entrada_direta}\n")
        log_interativo_file.write(f"Entrada branco: {entrada_branco}\n")
        log_interativo_file.write(f"Entrada dupla: {entrada_dupla}\n")

# Função para verificar padrões e realizar entradas
def verificar_e_entrar_padroes(sequencia, driver):
    padroes = {
        "padrao_5": (["white", "white", "black"], ["red", "white"]),
        "padrao_7": (["black", "black", "white", "red", "black"], ["black", "white"]),
        "padrao_8": (["red", "red", "white", "black", "red"], ["red", "white"])
    }

    for nome_padroes, (padrao_sequencia, cores_entrada) in padroes.items():
        if sequencia[-len(padrao_sequencia):] == padrao_sequencia:
            cor_entrada = cores_entrada[0]  # Exemplo: escolher a primeira cor
            print(f"Reconhecido: {nome_padroes}, fazendo entrada na cor {cor_entrada}.")
            # Aqui você deve adicionar a lógica para fazer a entrada na cor específica
            return cor_entrada

    return None

# Função principal
def main():
    global count_alarm, acertos_direto, erros, last_alarm_time, alarme_acionado, alarme_acionado2, acertos_branco, acertos_gale_branco
    last_alarm_time = time.time()  # Inicializa o tempo do último alarme

    # Variável para armazenar a última sequência de cores registrada no log
    ultima_sequencia_log = None

    # Inicializando o serviço do Chrome
    service = Service()

    # Configurando as opções do Chrome
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Executar em modo headless
    options.add_argument("--disable-gpu")

    # Inicializando o driver do Chrome
    driver = webdriver.Chrome(service=service, options=options)

    try:
        url = 'https://blaze-7.com/pt/games/double'
        driver.get(url)

        while not verificar_stop():
            recent_results_element = driver.find_element(By.ID, "roulette-recent")
            box_elements = recent_results_element.find_elements(By.CLASS_NAME, "sm-box")

            # Analisa as 15 últimas cores disponíveis
            sequencia = [box_element.get_attribute("class").split()[-1] for box_element in box_elements[:15]]

            # Verifica se houve uma mudança na sequência de cores
            if 'sequencia_anterior' not in locals() or sequencia != sequencia_anterior:
                # Verifica se a sequência de cores é diferente da última registrada no log
                if sequencia != ultima_sequencia_log:
                    ultima_sequencia_log = sequencia  # Atualiza a última sequência registrada no log

                    percentuais100 = extrair_cores(driver, 100)
                    percentuais25 = extrair_cores(driver, 25)
                    percentuais50 = extrair_cores(driver, 50)
                    percentuais500 = extrair_cores(driver, 500)

                    log_to_file("Ultimos 3 resultados: " + ', '.join(sequencia[:3]))
                    log_to_file("Ultimas 25 porcentagens: " + ', '.join(map(str, percentuais25)))
                    log_to_file("Ultimas 50 porcentagens: " + ', '.join(map(str, percentuais50)))
                    log_to_file("Ultimas 100 porcentagens: " + ', '.join(map(str, percentuais100)))
                    log_to_file("Ultimas 500 porcentagens: " + ', '.join(map(str, percentuais500)))

                    cor_entrada = verificar_e_entrar_padroes(sequencia, driver)
                    if cor_entrada:
                        # Aqui você pode inserir a lógica para entrar na cor determinada
                        pass

                # Atualiza a sequência anterior
                sequencia_anterior = sequencia

            # Espera um segundo antes de verificar novamente
            time.sleep(1)

    except Exception as e:
        print(f"Ocorreu um erro: {e}")
        log_to_file(f"Erro: {str(e)}")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
