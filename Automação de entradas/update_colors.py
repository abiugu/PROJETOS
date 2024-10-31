import asyncio
import json
import aiohttp
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
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

# Dicionário de padrões de cores
padroes = {
    "padrao 18": (["black", "white", "red", "white", "black"], ["white", "black"]),
    "padrao 21": (["black", "red", "red", "white", "white", "black"], ["white", "red"]),
    "padrao 36": (["white", "black", "red", "white", "white"], ["white", "red"]),
    "padrao 41": (["black", "black", "white", "white", "red", "black"], ["white", "black"]),
    "padrao 43": (["white", "black", "white", "red", "white", "white"], ["white", "red"]),
    "padrao 62": (["white", "white", "black", "white", "black"], ["white", "black"]),
    "padrao 64": (["black", "white", "black", "white"], ["white", "black"]),
    "padrao 32": (["white", "black", "white", "black"], ["white", "black"]),
    "padrao 53": (["white", "red", "white", "black", "black"], ["white", "black"]),
    "padrao 27": (["white", "black", "white"], ["white", "black"]),
    "padrao 45": (["white", "red", "white", "black"], ["white", "black"]),
    "padrao 51": (["black", "white", "white", "red", "black"], ["white", "black"]),
    "padrao 57": (["red", "black", "white", "red", "red", "red"], ["white", "red"]),
    "padrao 13": (["black", "black", "white", "red", "black", "black"], ["white", "black"]),
    "padrao 5": (["white", "white", "black"], ["white", "red"]),
    "padrao 7": (["black", "black", "white", "red", "black"], ["white", "black"]),
    "padrao 68": (["black", "red", "red", "red", "white"], ["white", "red"]),
    "padrao 28": (["white", "white", "red", "red", "black"], ["white", "red"]),
    "padrao 59": (["black", "red", "black", "black", "red", "white"], ["white", "black"]),
    "padrao 8": (["red", "red", "white", "black", "red"], ["white", "red"]),
    "padrao 67": (["red", "red", "white"], ["white", "red"]),
    "padrao 20": (["black", "white", "black", "red"], ["white", "red"]),
    "padrao 66": (["red", "white", "black", "red", "red"], ["white", "red"]),
    "padrao 14": (["red", "red", "white", "black", "red", "red"], ["white", "red"]),
    "padrao 35": (["red", "white", "red", "black", "red"], ["white", "red"]),
    "padrao 25": (["black", "white", "red", "red", "black"], ["white", "black"]),
    "padrao 31": (["white", "white", "red"], ["white", "red"]),
    "padrao 4": (["white", "black", "red"], ["white", "red"]),
    "padrao 11": (["black", "white", "white"], ["white", "black"]),
    "padrao 69": (["white", "black", "red", "red", "red", "black"], ["white", "black"]),
    "padrao 9": (["black", "red", "black", "red", "black", "black", "red"], ["white", "red"]),
    "padrao 2": (["red", "black", "white", "red"], ["white", "red"]),
    "padrao 42": (["black", "white", "white", "red"], ["white", "red"]),
    "padrao 65": (["red", "white", "white", "red"], ["white", "red"]),
}

# Função assíncrona para obter os dados da API
async def api():
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return [{'id': item['id'], 'color': item['color']} for item in data]
        except aiohttp.ClientError as e:
            print(f"Erro ao obter dados da API: {e}")
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
        print(f"Erro ao salvar o arquivo colors.json: {e}")

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
    service = Service('C:\\Users\\Abiug\\PROJETOS\\Automação de entradas\\chromedriver.exe')  # Atualize este caminho se necessário
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless')  # Descomente para rodar em modo headless
    driver = webdriver.Chrome(service=service, options=options)

    driver.get("https://blaze1.space/pt/games/double?modal=auth&tab=login")

    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "username")))
        email_input = driver.find_element(By.NAME, "username")
        email_input.send_keys(email)

        password_input = driver.find_element(By.NAME, "password")
        password_input.send_keys(senha)
        password_input.send_keys(Keys.RETURN)

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="number"]')))
        return driver
    except Exception as e:
        print(f"Erro ao realizar login: {e}")
        driver.quit()

# Função para tentar realizar a aposta por até 5 segundos
def tentar_aposta(driver, valor_aposta, cor):
    tentativas = 0
    while tentativas < 5:
        try:
            valor_input = driver.find_element(By.CSS_SELECTOR, 'input[type="number"]')
            valor_input.clear()
            valor_input.send_keys(str(valor_aposta))

            # Seleciona o botão de aposta com base na cor
            cor_button = driver.find_element(By.CSS_SELECTOR, f"button[data-color='{cor}']")
            cor_button.click()
            time.sleep(1)  # Pausa para garantir que a aposta foi processada
            print(f"Aposta de {valor_aposta} em {cor} realizada com sucesso!")
            return
        except NoSuchElementException:
            print("Erro ao tentar realizar a aposta, tentando novamente...")
            tentativas += 1
            time.sleep(1)
    print("Falha ao realizar a aposta após 5 tentativas.")

# Função para monitorar as jogadas
async def monitorar_jogadas(driver):
    global ultima_mensagem_alarme  # Referência à variável global
    historico = []  # Para armazenar o histórico das cores

    while True:
        # Verificar se o modal de inatividade está presente
        try:
            modal = driver.find_element(By.CSS_SELECTOR, ".modal-content")
            if modal.is_displayed():
                botao_estou_aqui = driver.find_element(By.CSS_SELECTOR, ".btn.btn-primary")
                botao_estou_aqui.click()
                print("Botão 'Estou aqui!' clicado.")
        except NoSuchElementException:
            pass

        # Obter os resultados da API
        resultados = await api()
        save_colors(resultados)
        
        # Atualiza o histórico com as cores mais recentes
        for resultado in resultados:
            historico.append(resultado['color'])
            if len(historico) > 10:  # Limitar o histórico a 10 entradas
                historico.pop(0)

        # Verifica padrões
        alarme_acionado = False
        cor_oposta = None
        
        for padrao, (sequencia, cores_alarme) in padroes.items():
            if len(historico) >= len(sequencia) and historico[-len(sequencia):] == sequencia:
                alarme_acionado = True
                cor_oposta = cores_alarme  # Cores a serem apostadas
                print(f"Alarme acionado pelo {padrao}!")
                break

        # Atualiza o estado do alarme
        atualizar_estado_alarme(alarme_acionado, cor_oposta)

        if alarme_acionado:
            # Realiza a aposta nas cores opostas especificadas
            if cor_oposta:
                valor_aposta = 1  # Defina aqui o valor da aposta
                for cor in cor_oposta:
                    tentar_aposta(driver, valor_aposta, cor)

        await asyncio.sleep(5)  # Aguarda 5 segundos antes da próxima verificação

# Execução do script
if __name__ == "__main__":
    load_dotenv()
    email = os.getenv('EMAIL')
    senha = os.getenv('SENHA')

    if not email or not senha:
        print("Email ou senha não definidos. Verifique suas variáveis de ambiente.")
    else:
        driver = realizar_login(email, senha)
        if driver:
            try:
                asyncio.run(monitorar_jogadas(driver))
            except KeyboardInterrupt:
                print("Interrompendo o script...")
            finally:
                driver.quit()
