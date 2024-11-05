from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import asyncio

# Inicialização do driver
driver = webdriver.Chrome()

async def obter_cores():
    driver.get("https://blaze1.space/pt/games/double")
    
    # Armazena as últimas jogadas para comparação
    ultimas_jogadas = []

    while True:
        try:
            # Espera até que pelo menos um novo elemento apareça
            WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".entries .entry"))
            )
            
            # Captura os elementos que contêm os números
            entradas = driver.find_elements(By.CSS_SELECTOR, ".entries .entry")
            resultados = []

            for entrada in entradas[:10]:  # Limitar para os 10 últimos
                try:
                    # Tenta capturar o texto do número e garante que não seja vazio
                    numero_texto = entrada.find_element(By.CSS_SELECTOR, ".number").text
                    
                    if numero_texto:  # Verifica se não está vazio
                        numero = int(numero_texto)
                        
                        # Define a cor com base no número
                        if numero == 0:
                            cor_final = "branco"
                        elif 1 <= numero <= 7:
                            cor_final = "vermelho"
                        elif 8 <= numero <= 14:
                            cor_final = "preto"
                        else:
                            cor_final = "fora do intervalo"

                        resultados.append(cor_final)
                    else:
                        print("Número vazio encontrado. Aguardando 1 segundo para tentar novamente.")
                        await asyncio.sleep(1)  # Aguardar 1 segundo antes de tentar novamente
                        break  # Interrompe o loop para tentar novamente
                except Exception as e:
                    print(f"Erro ao localizar o número: {e}. Tentando novamente em 1 segundo.")
                    await asyncio.sleep(1)  # Aguardar 1 segundo antes de tentar novamente
                    break  # Interrompe o loop para tentar novamente

            # Verifica se houve mudança nas jogadas
            if resultados and resultados != ultimas_jogadas:  # Verifica se resultados não está vazio
                print("Últimas jogadas:", resultados)
                ultimas_jogadas = resultados  # Atualiza as últimas jogadas
            
            # Aguarda 1 segundo antes de verificar novamente, caso tudo esteja certo
            await asyncio.sleep(1)

        except Exception as e:
            print("Erro geral:", e)
            # Aguardar 1 segundo antes de tentar novamente
            await asyncio.sleep(1)

# Chama a função para iniciar o processo
asyncio.run(obter_cores())

# O fechamento do driver deve ser feito manualmente quando você encerrar o script
