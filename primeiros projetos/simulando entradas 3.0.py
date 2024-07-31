import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select

# Variáveis globais
erros_anterior = 0
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
acertos_erros_path = os.path.join(desktop_path, "acertos_erros.txt")
log_file_path = os.path.join(desktop_path, "historico_do_dia.txt")

# Serviço e opções do webdriver Chrome
service = Service()
options = webdriver.ChromeOptions()
options.add_argument("--headless")
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
            print("")
            print(log_text)
            erros_anterior = 0
            intervalo_contagem = 60
            log_result_percentagens, log_result_double = obter_logs()
            return acertos, erros, intervalo_contagem, log_text, log_result_double, log_result_percentagens

        else:
            log_text = f"Acerto !! Cor atual: {cor_atual}"
            print("")
            print(log_text)
            intervalo_contagem = 60
            log_result_percentagens, log_result_double = obter_logs()
            return acertos, erros, intervalo_contagem, log_text, log_result_double, log_result_percentagens

    elif all(cor == cores_anteriores[0] for cor in cores_anteriores) and cor_atual == cores_anteriores[0]:
        erros_anterior += 1
        if erros_anterior == 1:
            log_text = f"Erro !! Cor atual: {cor_atual}"
            print("")
            print(log_text)
            intervalo_contagem = 25
            log_result_percentagens, log_result_double = obter_logs()
            return acertos, erros, intervalo_contagem, log_text, log_result_double, log_result_percentagens

        elif erros_anterior == 2:
            log_text = f"Erro no Martingale !! Cor atual: {cor_atual}"
            print("")
            print(log_text)
            erros_anterior = 0
            erros += 3
            intervalo_contagem = 60
            log_result_percentagens, log_result_double = obter_logs()
            return acertos, erros, intervalo_contagem, log_text, log_result_double, log_result_percentagens

        return acertos, erros, 25, "", "", ""
    return acertos, erros, 25, "", "", ""


def obter_logs():
    log_result_percentagens = percentual_ultimas_25_rodadas()
    log_result_double = resultados_vistos_ultimas_25_rodadas()
    return log_result_percentagens, log_result_double


def percentual_ultimas_25_rodadas():
    global driver

    # Verificar se a URL atual não corresponde à página desejada
    if "double_history_index" not in driver.current_url:
        driver.get(
            "https://blaze-7.com/pt/games/double?modal=double_history_index")

        # Aguardar até que a parte relevante da página seja carregada
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located(
            (By.CLASS_NAME, "tabs-crash-analytics")))

        # Aguardar até que o botão "Padrões" esteja presente
        padroes_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, ".//button[text()='Padrões']")))

        # Clicar no botão "Padrões" se ainda não estiver ativo
        if "active" not in padroes_button.get_attribute("class"):
            padroes_button.click()

    # Selecionar as opções no menu suspenso
    select_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//select[@tabindex='0']")))
    select = Select(select_element)
    time.sleep(2)
    select.select_by_value("50")
    time.sleep(2)
    select.select_by_value("25")
    time.sleep(2)

    # Extrair os valores das últimas 25 rodadas
    text_elements_present = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.TAG_NAME, "text")))
    valores_25 = [element.get_attribute("textContent") for element in text_elements_present if element.get_attribute(
        "y") == "288" and "SofiaPro" in element.get_attribute("font-family")]

    log_result = "Ultimas 25 rodadas:" + str(valores_25)
    print(log_result)
    return log_result


def resultados_vistos_ultimas_25_rodadas():
    global driver

    try:
        roll_div = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "roll")))
        roll_containers = roll_div.find_elements(
            By.CLASS_NAME, "roll__container")
        cores_numeros = []
        for container in roll_containers:
            cor_class = container.find_element(
                By.CLASS_NAME, "roll__square").get_attribute("class")
            if "roll__square--red" in cor_class:
                cor = "red"
            elif "roll__square--black" in cor_class:
                cor = "black"
            elif "roll__square--white" in cor_class:
                cor = "white"

            numero_str = container.find_element(By.TAG_NAME, "span").text
            numero_str_limpo = ''.join(
                filter(lambda x: x.isdigit() or x == '.', numero_str))
            numero_float = float(numero_str_limpo)
            numero_int = int(numero_float)

            ocorrencias_str = container.find_element(By.TAG_NAME, "p").text
            if '%' not in ocorrencias_str:
                ocorrencias_int = int(ocorrencias_str)
                cores_numeros.append((numero_int, cor, ocorrencias_int))

        cores_numeros.sort(key=lambda x: x[0])


    except Exception as e:
        print(f"Erro ao extrair resultados das ultimas 25 rodadas: {e}")
        return ""


def main():
    global erros_anterior
    global driver

    acertos, erros = 0, 0
    intervalo_contagem = 60
    print_intervalo = True  # Variável para controlar a impressão do intervalo

    try:
        url = 'https://blaze1.space/pt/games/double'
        driver.get(url)

        while not verificar_stop():
            recent_results_element = driver.find_element(
                By.ID, "roulette-recent")
            box_elements = recent_results_element.find_elements(
                By.CLASS_NAME, "sm-box")

            sequencia = [box_element.get_attribute(
                "class").split()[-1] for box_element in box_elements[:5]]

            acertos, erros, intervalo_contagem, log_text, log_result_double, log_result_percentagens = somar_resultados(
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

                if log_result_percentagens:
                    log_file.write(log_result_percentagens + "\n")
                    print("\n")
                    print_intervalo = True  # Ativar a impressão do intervalo após o log

                if log_result_double:
                    log_file.write(log_result_double + "\n")

                if print_intervalo:  # Verificar se é necessário imprimir o intervalo
                    print(f"Segundos do loop atual: {intervalo_contagem}")
                    print_intervalo = False  # Desativar a impressão do intervalo após imprimir

            time.sleep(intervalo_contagem)

    except Exception as e:
        print(f"Erro: {e}")

    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    main()
