import os
import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select

erros_anterior = 0
driver = None  # Variável global para o driver

# Redefine o caminho da área de trabalho para o sistema operacional
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")

# Define o caminho para o arquivo de log de acertos e erros na área de trabalho
acertos_erros_path = os.path.join(desktop_path, "acertos_erros.txt")

# Define o caminho para o arquivo de log diário na área de trabalho
log_file_path = os.path.join(desktop_path, "historico_do_dia.txt")

service = Service()
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Executar em modo headless
options.add_argument("--start-maximized")  # Maximizar a janela do navegador
driver = webdriver.Chrome(service=service, options=options)


def verificar_stop():
    stop_path = os.path.join(desktop_path, "stop.txt")
    return os.path.exists(stop_path)


def somar_resultados(acertos, erros, sequencia):
    global erros_anterior

    cores_anteriores = sequencia[1:4]
    cor_atual = sequencia[0]

    if all(cor == cores_anteriores[0] for cor in cores_anteriores) and cor_atual != cores_anteriores[0]:
        acertos += 1
        if erros_anterior == 1:
            log_text = f"Acerto no Martingale !! Cor atual: {cor_atual}"
            print(log_text)
            erros_anterior = 0
            intervalo_contagem = 60
            log_result = extrair_cores_25_50()  # Extrair cores após acerto martingale
            return acertos, erros, intervalo_contagem, log_text, log_result

        else:
            log_text = f"Acerto !! Cor atual: {cor_atual}"
            print(log_text)
            intervalo_contagem = 60
            log_result = extrair_cores_25_50()  # Extrair cores após acerto
            return acertos, erros, intervalo_contagem, log_text, log_result

    elif all(cor == cores_anteriores[0] for cor in cores_anteriores) and cor_atual == cores_anteriores[0]:
        erros_anterior += 1
        if erros_anterior == 1:
            log_text = f"Erro !! Cor atual: {cor_atual}"
            print(log_text)
            intervalo_contagem = 25
            log_result = extrair_cores_25_50()
            return acertos, erros, intervalo_contagem, log_text, ""

        elif erros_anterior == 2:
            log_text = f"Erro no Martingale !! Cor atual: {cor_atual}"
            print(log_text)
            erros_anterior = 0
            erros += 3
            intervalo_contagem = 60
            log_result = extrair_cores_25_50()  # Extrair cores após erro martingale
            return acertos, erros, intervalo_contagem, log_text, log_result

        return acertos, erros, 25, "", ""

    return acertos, erros, 25, "", ""


def extrair_cores_25_50():
    global driver

    # Abrir o site se ainda não estiver aberto
    if driver.current_url != "https://blaze-7.com/pt/games/double?modal=double_history_index":
        driver.get(
            "https://blaze-7.com/pt/games/double?modal=double_history_index")
        # Esperar até que a div "tabs-crash-analytics" esteja visível
        tabs_div = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "tabs-crash-analytics")))
        # Clicar no botão "Padrões" dentro da div "tabs-crash-analytics"
        padroes_button = tabs_div.find_element(
            By.XPATH, ".//button[text()='Padrões']")
        padroes_button.click()
        # Esperar até que o botão "Padrões" se torne ativo
        padroes_active_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//button[@class='tab active']")))

    select_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//select[@tabindex='0']")))
    select = Select(select_element)

    time.sleep(2)

    select.select_by_value("50")

    time.sleep(5)

    text_elements_present = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.TAG_NAME, "text")))
    text_elements_visible = WebDriverWait(driver, 10).until(
        EC.visibility_of_all_elements_located((By.TAG_NAME, "text")))
    valores_50 = [element.get_attribute("textContent") for element in text_elements_present
                  if element.get_attribute("y") == "288" and "SofiaPro" in element.get_attribute("font-family")]

    time.sleep(2)

    select.select_by_value("25")

    time.sleep(5)

    text_elements_present = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.TAG_NAME, "text")))
    text_elements_visible = WebDriverWait(driver, 10).until(
        EC.visibility_of_all_elements_located((By.TAG_NAME, "text")))
    valores_25 = [element.get_attribute("textContent") for element in text_elements_present
                  if element.get_attribute("y") == "288" and "SofiaPro" in element.get_attribute("font-family")]

    log_result = "Ultimas 25 rodadas:" + \
        str(valores_25) + "\nUltimas 50 rodadas:" + str(valores_50)
    print(log_result)
    return log_result


def main():
    global erros_anterior
    global driver

    acertos, erros = 0, 0
    intervalo_contagem = 60  # Começa com 60 segundos

    try:
        driver = webdriver.Chrome(service=service, options=options)
        url = 'https://blaze-7.com/pt/games/double'
        driver.get(url)

        while not verificar_stop():
            recent_results_element = driver.find_element(
                By.ID, "roulette-recent")
            box_elements = recent_results_element.find_elements(
                By.CLASS_NAME, "sm-box")

            sequencia = [box_element.get_attribute(
                "class").split()[-1] for box_element in box_elements[:5]]

            acertos, erros, intervalo_contagem, log_text, log_result = somar_resultados(
                acertos, erros, sequencia)

            with open(acertos_erros_path, "w") as acertos_erros_file:
                acertos_erros_file.write(
                    f"Acertos: {acertos}\nErros: {erros}\n")
                acertos_erros_file.write(f"Segundos do loop atual: {
                                         intervalo_contagem}\n")
                acertos_erros_file.write("Últimas 5 linhas:\n")
                acertos_erros_file.write("\n".join(sequencia) + "\n")

            with open(log_file_path, "a") as log_file:
                if log_text:
                    log_file.write(log_text + "\n")

                if log_result:
                    log_file.write(log_result + "\n")

                log_file.write(f"Segundos do loop atual: {
                               intervalo_contagem}" + "\n")

            print(f"Segundos do loop atual: {intervalo_contagem}")

            time.sleep(intervalo_contagem)

    except Exception as e:
        print(f"Erro: {e}")

    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    main()
