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
from selenium.common.exceptions import NoSuchElementException
from dotenv import load_dotenv
import platform
import time

# Definir o loop de eventos correto no Windows
if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# URL da API Blaze
url = "https://blaze1.space/api/roulette_games/recent"

# Variável global para armazenar a última mensagem
ultima_mensagem = ""

# Dicionário de padrões
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
            cores_para_apostar = estado.get('cores_para_apostar', None)
            return alarme_acionado2, cores_para_apostar
    except FileNotFoundError:
        print("Arquivo estado_alarme.json não encontrado.")
        return False, None

# Função para atualizar o estado do alarme (desativá-lo, por exemplo)
def atualizar_estado_alarme(alarme_acionado2, cores_para_apostar):
    estado = {
        'alarme_acionado2': alarme_acionado2,
        'cores_para_apostar': cores_para_apostar
    }
    with open('estado_alarme.json', 'w') as f:
        json.dump(estado, f, indent=4)
    print(f"Estado do alarme atualizado: alarme_acionado2={alarme_acionado2}, cores_para_apostar={cores_para_apostar}")

# Função para realizar login no site Blaze
def realizar_login(email, senha):
    service = Service()  # Atualize este caminho se necessário
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
            botao_apostar = WebDriverWait(driver, 1).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button#bet-button'))
            )
            botao_apostar.click()
            print(f"Aposta de {valor_aposta} na cor {cor_aposta} realizada com sucesso!")
            return True  # Retorna verdadeiro se a aposta foi realizada com sucesso
        except Exception as e:
            print(f"Tentativa {tentativa + 1}/{tentativas} falhou: {e}")
            time.sleep(1)  # Aguardar antes de tentar novamente
    return False  # Retorna falso se todas as tentativas falharam

# Função principal que monitora as jogadas e realiza as apostas
async def monitorar_jogadas(driver):
    ultimo_id = None
    ultima_cor = None
    penultima_cor = None  # Variável para armazenar a cor antes da última
    historico = []  # Para armazenar o histórico das cores

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
                await asyncio.sleep(1)  # Pequeno delay para garantir que o modal seja fechado
        except NoSuchElementException:
            pass  # Se o modal não estiver presente, continua normalmente

        results = await api()  # Função de API assíncrona para pegar os dados
        if results:
            save_colors(results)

            id_atual = results[0]['id']  # ID da jogada mais recente
            cor_atual = results[0]['color']  # Cor da jogada mais recente
            
            # Adiciona a cor atual ao histórico
            historico.append(cor_atual)
            if len(historico) > 10:  # Limitar o histórico a 10 entradas
                historico.pop(0)

            # Verifica padrões
            alarme_acionado = False
            cores_para_apostar = []  # Listar cores a serem apostadas

            for padrao, (sequencia, cores_alarme) in padroes.items():
                if len(historico) >= len(sequencia) and historico[-len(sequencia):] == sequencia:
                    alarme_acionado = True
                    cores_para_apostar = cores_alarme  # Cores a serem apostadas
                    print(f"Alarme acionado pelo padrão '{padrao}'!")
                    break

            # Atualiza o estado do alarme
            atualizar_estado_alarme(alarme_acionado, cores_para_apostar)

            if alarme_acionado and cores_para_apostar:
                valor_aposta = 10  # Define o valor da aposta
                for cor in cores_para_apostar:
                    sucesso = tentar_aposta(driver, valor_aposta, cor)
                    if sucesso:
                        # Realiza também a aposta na cor "white"
                        tentar_aposta(driver, 1, "white")  # Aposta de 1 na cor "white"
                        print(f"Apostas realizadas para as cores: {cores_para_apostar} e white.")
                        # Desativa o alarme após a aposta
                        atualizar_estado_alarme(False, None)
                        print("Apostas realizadas, aguardando 30 segundos antes de continuar.")
                        await asyncio.sleep(30)  # Aguardar 30 segundos antes de continuar

            # Atualiza os valores de última jogada
            penultima_cor = ultima_cor  # Move a última cor para a penúltima
            ultima_cor = cor_atual
            ultimo_id = id_atual

        await asyncio.sleep(0.5)  # Reduzir latência com await

# Função principal do programa
async def main():
    load_dotenv()  # Carrega as variáveis de ambiente do arquivo .env
    email = os.getenv('EMAIL')
    senha = os.getenv('SENHA')

    # Verifique se as variáveis foram carregadas corretamente
    if email is None or senha is None:
        print("Erro: EMAIL ou SENHA não estão definidos no arquivo .env.")
        return

    driver = realizar_login(email, senha)
    try:
        await monitorar_jogadas(driver)
    finally:
        driver.quit()  # Garante que o navegador seja fechado no final

