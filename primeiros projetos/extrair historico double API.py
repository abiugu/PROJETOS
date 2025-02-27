import requests
import random
import time
import os
import pandas as pd

# 🔹 Lista de proxies no formato "IP:PORT:USER:PASS"

PROXIES = [
"23.129.252.6:6274:cowards01:voltamosfieis",
"91.123.10.173:6715:cowards01:voltamosfieis",
"91.123.10.23:6565:cowards01:voltamosfieis",
"85.198.45.229:6153:cowards01:voltamosfieis",
"92.112.170.183:6152:cowards01:voltamosfieis",
"92.112.171.113:6081:cowards01:voltamosfieis",
"85.198.45.47:5971:cowards01:voltamosfieis",
"185.72.242.98:5781:cowards01:voltamosfieis",
"185.72.240.10:7046:cowards01:voltamosfieis",
"91.123.11.3:6269:cowards01:voltamosfieis",
"185.72.242.45:5728:cowards01:voltamosfieis",
"92.113.244.246:5933:cowards01:voltamosfieis",
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
END_DATE = "2025-02-27T23:59:59.999Z"

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
    caminho_arquivo = os.path.join(desktop, "historico_blaze.xlsx")
    
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
