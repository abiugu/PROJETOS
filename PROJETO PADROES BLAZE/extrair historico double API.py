import requests
import random
import time
import os
import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8')


# 🔹 Lista de proxies no formato "IP:PORT:USER:PASS"

PROXIES = [
"92.112.172.35:6307:LexuspX0:LexuspX7",
"185.72.240.234:7270:oldmoney0:oldmoney0",
"92.112.170.196:6165:oldmoney0:oldmoney0",
"92.112.175.14:6287:LexuspX0:LexuspX7",
"92.112.172.118:6390:LexuspX0:LexuspX7",
"185.72.242.8:5691:oldmoney0:oldmoney0",
"92.112.172.250:6522:LexuspX0:LexuspX7",
"23.129.253.149:6767:LexuspX0:LexuspX7",
"92.112.170.217:6186:JettapX11:JettapX17",
"91.123.10.14:6556:JettapX11:JettapX17",
"85.198.45.253:6177:oldmoney0:oldmoney0",
"85.198.45.146:6070:proxyrap10:proxyrap10",
"92.112.171.245:6213:proxyrap10:proxyrap10",
"92.112.172.80:6352:proxyrap10:proxyrap10",
"85.198.45.62:5986:newmoney0:newmoney0",
"92.112.170.188:6157:proxyrap10:proxyrap10",
"92.112.170.45:6014:proxyrap50:proxyrap50",
"85.198.45.183:6107:proxyrap10:proxyrap10",
"185.72.240.38:7074:oldmoney0:oldmoney0",
"92.112.200.131:6714:oldmoney0:oldmoney0"
]


# 🔹 Lista de User-Agents para evitar bloqueios
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.59"
]

# 🔹 Datas para buscar na API
START_DATE = "2025-01-01T04:00:00.000Z"
END_DATE = "2025-07-01T23:05:47.000Z"

# 🔹 Função para testar os proxies
def testar_proxies():
    url_teste = f"https://blaze.bet.br/api/singleplayer-originals/originals/roulette_games/recent/history/1?startDate={START_DATE}&endDate={END_DATE}&page=1"
    
    proxies_funcionais = []

    for proxy in PROXIES:
        ip, port, user, password = proxy.split(":")
        proxy_formatado = {
            "http": f"http://{user}:{password}@{ip}:{port}",
            "https": f"http://{user}:{password}@{ip}:{port}"
        }
        
        headers = {"User-Agent": random.choice(USER_AGENTS)}

        try:
            response = requests.get(url_teste, headers=headers, proxies=proxy_formatado, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ Proxy FUNCIONANDO: {ip}:{port}")
                proxies_funcionais.append(proxy)
            else:
                print(f"❌ Proxy FALHOU ({response.status_code}): {ip}:{port}")

        except Exception as e:
            print(f"⚠️ Proxy INACESSÍVEL: {ip}:{port} -> {e}")

    return proxies_funcionais

# 🔹 Função para traduzir cores
def traduzir_cor(cor):
    return {0: "white", 1: "red", 2: "black"}.get(cor, "unknown")

# 🔹 Função para obter os dados da API usando proxies rotativos
def obter_dados_blaze(proxies_validos):
    url_base = "https://blaze.bet.br/api/singleplayer-originals/originals/roulette_games/recent/history/1"
    
    all_records = []
    page = 1
    tentativas_falhas = 0

    while True:
        if tentativas_falhas >= 10000:
            print("🚨 Muitas falhas consecutivas. Interrompendo a coleta.")
            break

        # 🔀 Escolhe um proxy aleatório da lista válida
        proxy = random.choice(proxies_validos)
        ip, port, user, password = proxy.split(":")
        proxy_formatado = {
            "http": f"http://{user}:{password}@{ip}:{port}",
            "https": f"http://{user}:{password}@{ip}:{port}"
        }
        
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        url = f"{url_base}?startDate={START_DATE}&endDate={END_DATE}&page={page}"

        try:
            print(f"🔄 Coletando página {page} usando {ip}:{port}...")
            response = requests.get(url, headers=headers, proxies=proxy_formatado, timeout=10)

            if response.status_code == 200:
                page_data = response.json().get("records", [])
                if not page_data:
                    print("📭 Nenhuma nova informação. Finalizando...")
                    break
                
                all_records.extend(page_data)
                page += 1
                tentativas_falhas = 0  # Reseta falhas se for bem-sucedido
                time.sleep(random.uniform(0, 0.5))  # Pausa para evitar bloqueio

            else:
                print(f"⚠️ Erro na página {page}. Código {response.status_code}. Tentando outro proxy...")
                tentativas_falhas += 1

        except Exception as e:
            print(f"❌ Erro na página {page}: {e}. Tentando outro proxy...")
            tentativas_falhas += 1

    return all_records

# 🔹 Função para salvar os dados em um arquivo Excel
def salvar_dados_em_planilha(records):
    if not records:
        print("📭 Nenhum dado para salvar.")
        return
    
    for record in records:
        if "color" in record:
            record["color"] = traduzir_cor(record["color"])
    
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    caminho_arquivo = os.path.join(desktop, "historico_blaze_julho.xlsx")
    
    df = pd.DataFrame(records)
    df.to_excel(caminho_arquivo, index=False)
    
    print(f"✅ Dados salvos em {caminho_arquivo}")

# 🔹 Execução do código
if __name__ == "__main__":
    print("🔎 Testando proxies antes de iniciar a coleta...")
    proxies_validos = testar_proxies()
    
    if not proxies_validos:
        print("\n❌ Nenhum proxy funcional. Abortando execução.")
    else:
        print("\n✅ Proxies funcionais encontrados. Iniciando coleta de dados...\n")
        records = obter_dados_blaze(proxies_validos)
        salvar_dados_em_planilha(records)
