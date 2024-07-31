import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import pygame

service = Service()
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Executar em modo headless
options.add_argument("--start-maximized")  # Maximizar a janela do navegador
driver = webdriver.Chrome(service=service, options=options)

count_alarm = 0
acertos_direto = 0
acertos_gale = 0
erros = 0
last_alarm_time = 0  # Inicializar last_alarm_time
alarme_acionado = False  # Inicializa o estado do alarme como falso

# Redefine o caminho da área de trabalho para o sistema operacional
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")

# Caminho completo para o arquivo de log
log_file_path = os.path.join(desktop_path, "log 44.txt")

# Inicializa o mixer de áudio do pygame
pygame.mixer.init()

# Carrega o arquivo de som
sound_file_path = "MONEY ALARM.mp3"

# Carrega o som
alarm_sound = pygame.mixer.Sound(sound_file_path)

# Lê os valores anteriores do log interativo apenas uma vez no início do programa
log_interativo_path = os.path.join(desktop_path, "log_interativo 44.txt")
valores_anteriores = {"acertos_direto": 0, "acertos_gale": 0, "erros": 0}
if os.path.exists(log_interativo_path):
    with open(log_interativo_path, "r") as log_interativo_file:
        for line in log_interativo_file:
            if line.startswith("Acertos diretos:"):
                valores_anteriores["acertos_direto"] = int(line.split(":")[1])
            elif line.startswith("Acertos gale:"):
                valores_anteriores["acertos_gale"] = int(line.split(":")[1])
            elif line.startswith("Erros:"):
                valores_anteriores["erros"] = int(line.split(":")[1])


def log_to_file(message):
    with open(log_file_path, "a") as log_file:
        log_file.write(message + "\n")


def verificar_stop():
    stop_path = os.path.join(desktop_path, "stop.txt")
    return os.path.exists(stop_path)


def extrair_cores(driver, valor):
    # Abrir o site se ainda não estiver aberto
    if driver.current_url != "https://blaze1.space/pt/games/double?modal=double_history_index":
        driver.get(
            "https://blaze1.space/pt/games/double?modal=double_history_index")
        # Aguarda até 5 segundos para elementos aparecerem
        driver.implicitly_wait(5)

        # Esperar até que a div "tabs-crash-analytics" esteja visível
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "tabs-crash-analytics")))

        # Clicar no botão "Padrões" dentro da div "tabs-crash-analytics"
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, ".//button[text()='Padrões']"))).click()

        # Esperar até que o botão "Padrões" se torne ativo
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//button[@class='tab active']")))

    select_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//select[@tabindex='0']")))
    select = Select(select_element)
    time.sleep(2)
    select.select_by_value(str(valor))
    time.sleep(2)

    text_elements_present = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.TAG_NAME, "text")))
    text_elements_visible = WebDriverWait(driver, 10).until(
        EC.visibility_of_all_elements_located((By.TAG_NAME, "text")))

    # Extrair apenas os valores de porcentagem e remover o símbolo '%'
    valores = [element.get_attribute("textContent") for element in text_elements_present
               if element.get_attribute("y") == "288" and "SofiaPro" in element.get_attribute("font-family")]
    percentuais = [float(valor.split('%')[0]) for valor in valores]

    return percentuais


def atualizar_log_interativo(acertos_direto, acertos_gale, erros):
    with open(log_interativo_path, "w") as log_interativo_file:
        log_interativo_file.write("=== LOG INTERATIVO ===\n")
        log_interativo_file.write(f"Acertos diretos: {acertos_direto}\n")
        log_interativo_file.write(f"Acertos gale: {acertos_gale}\n")
        log_interativo_file.write(f"Erros: {erros}\n")
        entrada_direta = int(
            float(acertos_direto - (acertos_gale + erros / 3)))
        entrada_secundaria = int(float(acertos_gale - (erros / 3)))
        entrada_gale = int(float(acertos_direto + acertos_gale - erros))
        log_interativo_file.write(f"Entrada direta: {entrada_direta}\n")
        log_interativo_file.write(f"Entrada secundária: {
                                  entrada_secundaria}\n")
        log_interativo_file.write(f"Entrada gale: {entrada_gale}\n")


def main():
    global count_alarm
    global acertos_direto
    global acertos_gale
    global erros
    global last_alarm_time
    global alarme_acionado
    sequencia_anterior = []  # Definindo a variável sequencia_anterior antes de ser utilizada

    last_alarm_time = time.time()  # Inicializa o tempo do último alarme

    try:
        url = 'https://blaze-7.com/pt/games/double'
        driver.get(url)

        while not verificar_stop():
            recent_results_element = driver.find_element(
                By.ID, "roulette-recent")
            box_elements = recent_results_element.find_elements(
                By.CLASS_NAME, "sm-box")

            # Analisa as 15 últimas cores disponíveis
            sequencia = [box_element.get_attribute(
                "class").split()[-1] for box_element in box_elements[:15]]

            # Obtém apenas as últimas 3 cores para imprimir
            ultimas_tres_cores = sequencia[:3]

            # Verifica se houve uma mudança na sequência de cores
            if sequencia != sequencia_anterior:
                percentuais25 = extrair_cores(driver, 25)
                percentuais100 = extrair_cores(driver, 100)
                percentuais500 = extrair_cores(driver, 500)
                log_to_file("Ultimos 3 resultados: " +
                            ', '.join(ultimas_tres_cores))
                log_to_file("Ultimas 25 porcentagens: " +
                            ', '.join(map(str, percentuais25)))
                log_to_file("Ultimas 100 porcentagens: " +
                            ', '.join(map(str, percentuais100)))
                log_to_file("Ultimas 500 porcentagens: " +
                            ', '.join(map(str, percentuais500)))

                # Verifica se há alguma sequência de 3 cores iguais
                if len(set(ultimas_tres_cores)) == 1:
                    cor_atual = sequencia[0]
                    cor_oposta = None
                    if cor_atual == 'red':
                        cor_oposta = 'black'
                    elif cor_atual == 'black':
                        cor_oposta = 'red'
                    if cor_oposta:
                        cor_atual_percentual = int(
                            percentuais25[['white', 'black', 'red'].index(cor_atual)])

                        if cor_atual_percentual is not None:
                            print(f"Cor atual: {cor_atual}, Percentual: {
                                  cor_atual_percentual}")
                            if cor_atual_percentual <= 44:
                                if ultimas_tres_cores[0] == ultimas_tres_cores[1] == ultimas_tres_cores[2]:
                                    print(
                                        "Tres cores iguais e porcentagem menor ou igual a 44. Solicitar alarme.")
                                    current_time = time.time()
                                    if current_time - last_alarm_time >= 60:
                                        alarm_sound.play()
                                        count_alarm += 1
                                        print(f"Alarme acionado. Contagem: {
                                              count_alarm}")
                                        log_to_file(
                                            f"Alarme acionado. Contagem: {count_alarm}")
                                        last_alarm_time = current_time
                                        alarme_acionado = True  # Define alarme_acionado como True
                sequencia_anterior = sequencia  # Atualiza a sequência anterior
            # Lógica para verificar duas sequências após o alarme acionado

                if alarme_acionado:
                    while sequencia == sequencia_anterior:
                        recent_results_element = driver.find_element(
                            By.ID, "roulette-recent")
                        box_elements = recent_results_element.find_elements(
                            By.CLASS_NAME, "sm-box")
                        sequencia = [box_element.get_attribute(
                            "class").split()[-1] for box_element in box_elements[:15]]

                        time.sleep(1)

                    if sequencia != sequencia_anterior:
                        percentuais25_1 = extrair_cores(driver, 25)
                        percentuais100_1 = extrair_cores(driver, 100)
                        percentuais500_1 = extrair_cores(driver, 500)

                        recent_results_element = driver.find_element(
                            By.ID, "roulette-recent")
                        box_elements = recent_results_element.find_elements(
                            By.CLASS_NAME, "sm-box")
                        sequencia_1 = [box_element.get_attribute(
                            "class").split()[-1] for box_element in box_elements[:15]]
                        ultimas_tres_cores_1 = sequencia_1[:3]
                        log_to_file("Ultimos 3 resultados: " +
                                    ', '.join(ultimas_tres_cores_1))
                        log_to_file("Ultimas 25 porcentagens: " +
                                    ', '.join(map(str, percentuais25_1)))
                        log_to_file("Ultimas 100 porcentagens: " +
                                    ', '.join(map(str, percentuais100_1)))
                        log_to_file("Ultimas 500 porcentagens: " +
                                    ', '.join(map(str, percentuais500_1)))

                        while ultimas_tres_cores_1 == sequencia_1:
                            recent_results_element = driver.find_element(
                                By.ID, "roulette-recent")
                            box_elements = recent_results_element.find_elements(
                                By.CLASS_NAME, "sm-box")
                            sequencia = [box_element.get_attribute(
                                "class").split()[-1] for box_element in box_elements[:15]]

                            time.sleep(1)
                        if ultimas_tres_cores_1 != sequencia:
                            percentuais25_2 = extrair_cores(driver, 25)
                            percentuais100_2 = extrair_cores(driver, 100)
                            percentuais500_2 = extrair_cores(driver, 500)

                            recent_results_element = driver.find_element(
                                By.ID, "roulette-recent")
                            box_elements = recent_results_element.find_elements(
                                By.CLASS_NAME, "sm-box")
                            sequencia_2 = [box_element.get_attribute(
                                "class").split()[-1] for box_element in box_elements[:15]]
                            ultimas_tres_cores_2 = sequencia_2[:3]
                            log_to_file("Ultimos 3 resultados: " +
                                        ', '.join(ultimas_tres_cores_2))
                            log_to_file("Ultimas 25 porcentagens: " +
                                        ', '.join(map(str, percentuais25_2)))
                            log_to_file("Ultimas 100 porcentagens: " +
                                        ', '.join(map(str, percentuais100_2)))
                            log_to_file("Ultimas 500 porcentagens: " +
                                        ', '.join(map(str, percentuais500_2)))

                        # Define alarme_acionado como False após coletar a segunda sequênci
                        alarme_acionado = False

                        # Verifica se as duas sequências são iguais
                        if ultimas_tres_cores_1 != sequencia_anterior[:3]:
                            print("Acerto direto !!")
                            acertos_direto += 1
                        else:
                            if ultimas_tres_cores_1 != ultimas_tres_cores_2:
                                print("Acerto gale !!")
                                acertos_gale += 1
                            else:
                                print("Erro gale !!")
                                erros += 3
                        log_to_file(f"Acertos direto: {acertos_direto}, Acertos gale: {
                                    acertos_gale}, Erros: {erros}")
                        print(f"Acertos direto: {acertos_direto}, Acertos gale: {
                              acertos_gale}, Erros: {erros}")

                atualizar_log_interativo(acertos_direto, acertos_gale, erros)
                time.sleep(1)

    except Exception as e:
        error_message = f"Erro: {e}"
        print(error_message)
        log_to_file(error_message)

    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    main()
