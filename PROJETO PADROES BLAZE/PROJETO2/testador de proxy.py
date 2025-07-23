import requests
from requests.auth import HTTPProxyAuth
from datetime import datetime

# Substitua por sua lista completa de proxies
proxies_brutos = """
85.198.45.253:6177:oldmoney0:oldmoney0
85.198.45.146:6070:proxyrap10:proxyrap10
92.112.171.245:6213:proxyrap10:proxyrap10
92.112.172.80:6352:proxyrap10:proxyrap10
85.198.45.62:5986:newmoney0:newmoney0
92.112.170.188:6157:proxyrap10:proxyrap10
92.112.170.45:6014:proxyrap50:proxyrap50
85.198.45.183:6107:proxyrap10:proxyrap10
185.72.240.38:7074:oldmoney0:oldmoney0
92.112.200.131:6714:oldmoney0:oldmoney0
""".strip().splitlines()

test_url = "https://httpbin.org/ip"
saida_ok = []

for linha in proxies_brutos:
    try:
        ip, port, user, pwd = linha.strip().split(":")
        proxy_address = f"http://{ip}:{port}"
        proxies = {"http": proxy_address, "https": proxy_address}
        auth = HTTPProxyAuth(user, pwd)

        print(f"🔍 Testando proxy {ip}:{port} ...", end=" ")

        response = requests.get(test_url, proxies=proxies, auth=auth, timeout=10)

        if response.status_code == 200:
            ip_usado = response.json().get("origin")
            print(f"✅ Sucesso | IP: {ip_usado}")
            saida_ok.append(linha)
        else:
            print(f"❌ Falhou | Status: {response.status_code}")

    except Exception as e:
        print(f"❌ Erro: {e}")

# Salvar proxies válidos
if saida_ok:
    with open("proxies_validos.txt", "w") as f:
        for proxy in saida_ok:
            f.write(proxy + "\n")
    print(f"\n📁 {len(saida_ok)} proxies salvos em proxies_validos.txt")
else:
    print("\n⚠️ Nenhum proxy válido encontrado.")
