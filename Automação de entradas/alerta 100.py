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
#options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

# Inicializando o driver do Chrome
driver = webdriver.Chrome(service=service, options=options)

# Variáveis globais
count_alarm = 0
acertos_direto = 0
acertos_gale = 0
erros = 0
last_alarm_time = 0  # Inicializa last_alarm_time
alarme_acionado = False  # Inicializa o estado do alarme como falso
acertos_branco = 0
acertos_gale_branco = 0
alarme_acionado_start_time = None  # Para armazenar o tempo em que o alarme foi ativado

# Caminho da área de trabalho
desktop_path = os.path.join(os.path.expanduser("~"), 'Desktop')

# Pasta de logs
logs_path = os.path.join(desktop_path, "LOGS")

# Caminho completo para o arquivo de log
log_file_path = os.path.join(logs_path, "log global.txt")

# Inicializa o mixer de áudio do pygame
pygame.mixer.init()

# Carrega o arquivo de som
sound_file_path = "ENTRADA CONFIRMADA.mp3"
sound_file_path2 = "MONEY ALARM.mp3"

# Carrega o som
alarm_sound = pygame.mixer.Sound(sound_file_path)
alarm_sound2 = pygame.mixer.Sound(sound_file_path2)

# Arquivo de log interativo
log_interativo_path = os.path.join(logs_path, "log interativo 100.txt")

# Dicionário para armazenar valores anteriores
valores_anteriores = {"acertos_direto": 0, "acertos_gale": 0, "erros": 0}

estrategias = [
    {"percentual_25": 48.0, "percentual_50": 52.0},
    {"percentual_50": 44.0, "percentual_100": 50.0},
    {"percentual_50": 56.0, "percentual_100": 54.0},
    {"percentual_50": 52.0, "percentual_100": 53.0},
    {"percentual_50": 44.0, "percentual_100": 46.0},
    {"percentual_50": 44.0, "percentual_100": 43.0},
    {"percentual_25": 48.0, "percentual_50": 54.0},
    {"percentual_25": 44.0, "percentual_50": 50.0},
    {"percentual_25": 40.0, "percentual_50": 40.0},
    {"percentual_25": 56.0, "percentual_50": 46.0},
    {"percentual_25": 44.0, "percentual_50": 38.0},
    {"percentual_50": 50.0, "percentual_100": 45.0},
    {"percentual_50": 44.0, "percentual_100": 46.0},
    {"percentual_50": 36.0, "percentual_100": 42.0},
    {"percentual_25": 64.0, "percentual_50": 52.0},
    {"percentual_25": 40.0, "percentual_50": 40.0},
    {"percentual_25": 36.0, "percentual_50": 42.0},
    {"percentual_100": 50.0, "percentual_500": 49.0},
    {"percentual_100": 50.0, "percentual_500": 47.4},
    {"percentual_50": 60.0, "percentual_100": 53.0},
    {"percentual_50": 50.0, "percentual_100": 54.0},
    {"percentual_50": 46.0, "percentual_100": 54.0},
    {"percentual_50": 38.0, "percentual_100": 45.0},
    {"percentual_25": 52.0, "percentual_50": 58.0},
    {"percentual_25": 52.0, "percentual_50": 40.0},
    {"percentual_25": 44.0, "percentual_50": 40.0},
    {"percentual_100": 52.0, "percentual_500": 48.4},
    {"percentual_100": 49.0, "percentual_500": 48.6},
    {"percentual_100": 47.0, "percentual_500": 47.0},
    {"percentual_100": 42.0, "percentual_500": 44.0},
    {"percentual_50": 50.0, "percentual_100": 48.0},
    {"percentual_25": 44.0, "percentual_50": 40.0},
    {"percentual_50": 50.0, "percentual_100": 46.0},
    {"percentual_50": 62.0, "percentual_100": 55.0},
    {"percentual_50": 52.0, "percentual_100": 50.0},
    {"percentual_50": 48.0, "percentual_100": 49.0},
    {"percentual_50": 54.0, "percentual_100": 57.0},
    {"percentual_50": 52.0, "percentual_100": 52.0},
    {"percentual_25": 68.0, "percentual_50": 54.0},
    {"percentual_50": 54.0, "percentual_100": 53.0},
    {"percentual_50": 48.0, "percentual_100": 52.0},
    {"percentual_50": 42.0, "percentual_100": 44.0},
    {"percentual_50": 50.0, "percentual_100": 51.0},
    {"percentual_50": 48.0, "percentual_100": 51.0},
]

# Exemplo de como verificar as condições em uma função de entrada
def verificar_estrategias(cor_atual_percentual_25, cor_atual_percentual_50, cor_atual_percentual_100, cor_atual_percentual_500):
    for estrategia in estrategias:
        if ('percentual_25' in estrategia and estrategia['percentual_25'] == cor_atual_percentual_25) and \
           ('percentual_50' in estrategia and estrategia['percentual_50'] == cor_atual_percentual_50) and \
           ('percentual_100' in estrategia and estrategia['percentual_100'] == cor_atual_percentual_100) and \
           ('percentual_500' in estrategia and estrategia['percentual_500'] == cor_atual_percentual_500):
            print(f"Estratégia acionada: {estrategia}")


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
        json.dump({'alarme_acionado2': alarme_acionado2}, f)
    print(f"JSON atualizado: alarme_acionado2={alarme_acionado2}")

# Função para extrair as porcentagens das cores
def extrair_cores(driver, valor):
    # Abrir o site se ainda não estiver aberto
    if driver.current_url != "https://blaze1.space/pt/games/double?modal=double_history_index":
        driver.get("https://blaze1.space/pt/games/double?modal=double_history_index")
        # Aguarda até 5 segundos para elementos aparecerem
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
    valores = [element.get_attribute("textContent") for element in text_elements_present if element.get_attribute("y") == "288" and "SofiaPro" in element.get_attribute("font-family")]
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


# Função principal
def main():
    global count_alarm, acertos_direto, erros, last_alarm_time, alarme_acionado, alarme_acionado2, acertos_branco, acertos_gale_branco, alarme_acionado_start_time
    last_alarm_time = time.time()  # Inicializa o tempo do último alarme
    alarme_acionado_start_time = None  # Inicializa o tempo de início do alarme

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

                    # ... [código anterior] ...

                    if len(set(sequencia[:2])) == 1:
                        cor_atual = sequencia[0]
                        cor_oposta = None
                        if cor_atual == 'red':
                            cor_oposta = 'black'
                        elif cor_atual == 'black':
                            cor_oposta = 'red'
                        if cor_oposta:
                            cor_atual_percentual_500 = int(percentuais500[['white', 'black', 'red'].index(cor_atual)])
                            cor_oposta_percentual_500 = int(percentuais500[['white', 'black', 'red'].index(cor_oposta)])
                    
                            cor_atual_percentual_100 = int(percentuais100[['white', 'black', 'red'].index(cor_atual)])
                            cor_oposta_percentual_100 = int(percentuais100[['white', 'black', 'red'].index(cor_oposta)])
                    
                            cor_atual_percentual_50 = int(percentuais50[['white', 'black', 'red'].index(cor_atual)])
                            cor_oposta_percentual_50 = int(percentuais50[['white', 'black', 'red'].index(cor_oposta)])
                    
                            cor_atual_percentual_25 = int(percentuais25[['white', 'black', 'red'].index(cor_atual)])
                            cor_oposta_percentual_25 = int(percentuais25[['white', 'black', 'red'].index(cor_oposta)])
                    
                            # Aqui, substitua a verificação original pela chamada à função verificar_estrategias
                            verificar_estrategias(cor_atual_percentual_25, cor_atual_percentual_50, cor_atual_percentual_100, cor_atual_percentual_500)
                    
                            # A lógica do alarme pode ser ativada se a estratégia for encontrada.
                            if alarme_acionado and alarme_acionado_start_time:
                                if time.time() - alarme_acionado_start_time >= 30:
                                    log_to_file("Desativando alarme após 30 segundos.")
                                    alarme_acionado = False
                                    alarme_acionado2 = False
                                    atualizar_json_alarme(alarme_acionado2)
                                    print("Alarme desativado após 30 segundos.")

# ... [código seguinte] ...


                    if len(set(sequencia[:3])) == 1:
                        cor_atual = sequencia[0]
                        cor_oposta = None
                        if cor_atual == 'red':
                            cor_oposta = 'black'
                        elif cor_atual == 'black':
                            cor_oposta = 'red'
                        if cor_oposta:
                            cor_atual_percentual_500 = int(percentuais500[['white', 'black', 'red'].index(cor_atual)])
                            cor_oposta_percentual_500 = int(percentuais500[['white', 'black', 'red'].index(cor_oposta)])

                            cor_atual_percentual_100 = int(percentuais100[['white', 'black', 'red'].index(cor_atual)])
                            cor_oposta_percentual_100 = int(percentuais100[['white', 'black', 'red'].index(cor_oposta)])

                            cor_atual_percentual_50 = int(percentuais50[['white', 'black', 'red'].index(cor_atual)])
                            cor_oposta_percentual_50 = int(percentuais50[['white', 'black', 'red'].index(cor_oposta)])

                            cor_atual_percentual_25 = int(percentuais25[['white', 'black', 'red'].index(cor_atual)])
                            cor_oposta_percentual_25 = int(percentuais25[['white', 'black', 'red'].index(cor_oposta)])

                            # Aqui, substitua a verificação original pela chamada à função verificar_estrategias
                            verificar_estrategias(cor_atual_percentual_25, cor_atual_percentual_50, cor_atual_percentual_100, cor_atual_percentual_500)
                            print(f"Cor atual: {cor_atual}, Percentual 25: {cor_atual_percentual_25}%, Percentual 50: {cor_atual_percentual_50}%, Percentual 100: {cor_atual_percentual_100}%")



                            if cor_atual_percentual_25 <= 100:
                                current_time = datetime.datetime.now(pytz.timezone('America/Sao_Paulo'))
                                hora_atual = current_time.strftime("%H:%M:%S")
                                data_atual = current_time.strftime("%d-%m-%Y")  # Ajuste para dia-mês-ano

                                current_time = time.time()
                                if current_time - last_alarm_time >= 60:
                                    alarm_sound2.play()
                                    alarme_acionado = True
                                    count_alarm += 1
                                    print(f"Alarme acionado. {hora_atual}, {data_atual}, Contagem: {count_alarm}")
                                    log_to_file(f"Alarme acionado. {hora_atual}, {data_atual}, Contagem: {count_alarm}")

                                    last_alarm_time = current_time
                                    alarme_acionado_start_time = current_time  # Atualiza o tempo em que o alarme foi ativado

                                    # Atualiza a sequência anterior
                                    sequencia_anterior = sequencia

            # Verifica se o alarme deve ser desativado após 30 segundos
            if alarme_acionado and alarme_acionado_start_time:
                if time.time() - alarme_acionado_start_time >= 30:
                    alarme_acionado = False
                    alarme_acionado2 = False
                    atualizar_json_alarme(alarme_acionado2)
                    print("Alarme desativado após 30 segundos.")

            time.sleep(1)

    except Exception as e:
        error_message = f"Erro: {e}"
        log_to_file(error_message)
        print(error_message)

    finally:
        # Finalizando o driver
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()
