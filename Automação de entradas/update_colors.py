import asyncio
import json
import aiohttp
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
from selenium.common.exceptions import NoSuchElementException
import platform
import time

# Definir o loop de eventos correto no Windows
if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# URL da API Blaze
url = "https://blaze1.space/api/roulette_games/recent"

# Variável global para armazenar a última mensagem
ultima_mensagem = ""
# Variável global para armazenar a última mensagem do alarme
ultima_mensagem_alarme = ""

# Função assíncrona para obter os dados da API
async def api():
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return [{'id': item['id'], 'color': item['color']} for item in data]
        except aiohttp.ClientError as e:
            print(f"Erro ao obter dados: {e}")
            return []


# Função para salvar os dados no arquivo colors.json
def save_colors(results):
    global ultima_mensagem  # Referência à variável global
    try:
        with open('colors.json', 'w') as file:
            json.dump(results, file, indent=4)
        
        nova_mensagem = "Dados atualizados no arquivo colors.json"
        
        # Verifica se a nova mensagem é diferente da última
        if nova_mensagem != ultima_mensagem:
            print(nova_mensagem)
            ultima_mensagem = nova_mensagem  # Atualiza a última mensagem

    except IOError as e:
        print(f"Erro ao salvar o arquivo: {e}")


# Função para ler o estado do alarme do arquivo estado_alarme.json
def ler_estado_alarme():
    try:
        with open('estado_alarme.json', 'r') as f:
            estado = json.load(f)
            alarme_acionado2 = estado.get('alarme_acionado2', False)
            cor_oposta = estado.get('cor_oposta', None)
            return alarme_acionado2, cor_oposta
    except FileNotFoundError:
        print("Arquivo estado_alarme.json não encontrado.")
        return False, None

# Função para atualizar o estado do alarme (desativá-lo, por exemplo)
def atualizar_estado_alarme(alarme_acionado2, cor_oposta):
    estado = {
        'alarme_acionado2': alarme_acionado2,
        'cor_oposta': cor_oposta
    }
    with open('estado_alarme.json', 'w') as f:
        json.dump(estado, f, indent=4)
    print(f"Estado do alarme atualizado: alarme_acionado2={alarme_acionado2}, cor_oposta={cor_oposta}")

# Função para realizar login no site Blaze
def realizar_login(email, senha):
    service = Service()
    options = webdriver.ChromeOptions()
    #options.add_argument('--headless')  # Adicionar headless para reduzir latência
    driver = webdriver.Chrome(service=service, options=options)

    driver.get("https://blaze1.space/pt/games/double?modal=auth&tab=login")

    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "username")))
    email_input = driver.find_element(By.NAME, "username")
    email_input.send_keys(email)

    password_input = driver.find_element(By.NAME, "password")
    password_input.send_keys(senha)
    password_input.send_keys(Keys.RETURN)

    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="number"]')))
    return driver

# Função para tentar realizar a aposta por até 5 segundos
def tentar_aposta(driver, valor_aposta, cor_aposta, tentativas=5):
    for tentativa in range(tentativas):
        try:
            # Localiza o campo de valor de entrada e insere o valor
            input_valor_aposta = WebDriverWait(driver, 1).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="number"]'))
            )
            input_valor_aposta.clear()
            input_valor_aposta.send_keys(valor_aposta)

            # Seleciona a cor correta
            cor_button = WebDriverWait(driver, 1).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, f'div.{cor_aposta}'))
            )
            cor_button.click()

            # Clicar no botão de "Apostar"
            apostar_button = WebDriverWait(driver, 1).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "div.place-bet button"))
            )
            apostar_button.click()

            print(f"Aposta de {valor_aposta} na cor {cor_aposta} realizada com sucesso!")
            return True  # Se aposta foi feita com sucesso

        except Exception as e:
            # Se a aposta não foi realizada, tenta novamente
            print(f"Tentativa {tentativa + 1} falhou. Erro: {e}")
            time.sleep(1)  # Espera 1 segundo antes de tentar novamente

    print("Não foi possível realizar a aposta após 5 segundos.")
    return False  # Se todas as tentativas falharem


# Função principal que monitora as jogadas e realiza as apostas
async def monitorar_jogadas(driver):
    ultimo_id = None
    ultima_cor = None
    penultima_cor = None  # Variável para armazenar a cor antes da última

    while True:
        # Verificar se o modal de confirmação de atividade está presente
        try:
            # Tenta localizar o modal de confirmação de atividade
            modal = driver.find_element(By.ID, "confirm-activity-modal")
            # Se o modal estiver presente, tenta clicar no botão "Estou aqui!"
            if modal.is_displayed():
                print("Modal de inatividade detectado, clicando no botão 'Estou aqui!'")
                botao_estou_aqui = modal.find_element(By.CSS_SELECTOR, "button.custom-button.i_m_here")
                botao_estou_aqui.click()
                print("Clique realizado com sucesso!")
        except NoSuchElementException:
            # Se o modal não estiver presente, o código continua normalmente
            pass

        # Lê o estado do alarme antes de qualquer operação
        alarme_acionado2, cor_oposta = ler_estado_alarme()

        results = await api()  # Função de API assíncrona para pegar os dados
        if results:
            save_colors(results)

            id_atual = results[0]['id']  # ID da jogada mais recente
            cor_atual = results[0]['color']  # Cor da jogada mais recente

            # Verifica se o alarme está acionado
            if alarme_acionado2:
                print("Alarme acionado, aguardando a próxima jogada...")

                # Verifica se o ID mudou (nova jogada)
                if id_atual != ultimo_id:
                    print(f"Nova jogada detectada. ID anterior: {ultimo_id}, ID atual: {id_atual}")

                    # Verifica se a cor da nova jogada é igual às duas anteriores
                    if cor_atual == ultima_cor == penultima_cor:
                        print(f"Cor repetida pela terceira vez detectada ({cor_atual}), realizando as apostas...")

                        # Realiza as apostas na cor oposta e no white
                        if cor_oposta:
                            sucesso = tentar_aposta(driver, "20", cor_oposta)
                            if sucesso:
                                tentar_aposta(driver, "2", "white")  # Aposta no white também

                                # Desativa o alarme após a aposta
                                atualizar_estado_alarme(False, None)

                                # Aguarda 30 segundos antes de retomar a leitura
                                print("Esperando 30 segundos antes de retomar a leitura.")
                                await asyncio.sleep(30)

                            else:
                                print("Falha ao realizar as apostas. Tentando novamente.")
                        else:
                            print("Erro: cor_oposta não definida.")
                    else:
                        # Se a cor for diferente, desativa o alarme
                        print(f"Cor diferente detectada ({cor_atual}), alarme será desativado.")
                        atualizar_estado_alarme(False, None)

                    # Atualiza os valores de última jogada
                    penultima_cor = ultima_cor  # Move a última cor para a penúltima
                    ultima_cor = cor_atual
                    ultimo_id = id_atual

            # Atualiza os valores de última jogada
            penultima_cor = ultima_cor  # Move a última cor para a penúltima
            ultima_cor = cor_atual
            ultimo_id = id_atual

        await asyncio.sleep(0.5)  # Reduzir latência com await

if __name__ == "__main__":
    load_dotenv(dotenv_path='C:/Users/abiug/PROJETOS/Login.Env')
    EMAIL = os.getenv('EMAIL')
    SENHA = os.getenv('SENHA')

    driver = realizar_login(EMAIL, SENHA)

    try:
        asyncio.run(monitorar_jogadas(driver))  # Executar com asyncio
    except KeyboardInterrupt:
        print("\nExecução interrompida manualmente.")
    finally:
        driver.quit()
