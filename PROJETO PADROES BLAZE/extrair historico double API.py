import requests
import random
import time
import os
import pandas as pd

# 🔹 Lista de proxies no formato "IP:PORT:USER:PASS"

PROXIES = [
"91.123.10.15:6557:gmdanightpaulista:melhorproxybr",
"91.123.11.35:6301:gmdanightpaulista:melhorproxybr",
"92.112.202.161:6745:gmdanightpaulista:melhorproxybr",
"92.112.202.51:6635:gmdanightpaulista:melhorproxybr",
"92.112.202.206:6790:gmdanightpaulista:melhorproxybr",
"92.112.200.167:6750:gmdanightpaulista:melhorproxybr",
"185.72.240.193:7229:gmdanightpaulista:melhorproxybr",
"92.113.244.10:5697:gmdanightpaulista:melhorproxybr",
"92.113.245.47:5733:gmdanightpaulista:melhorproxybr",
"85.198.47.148:6416:gmdanightpaulista:melhorproxybr",
"91.123.10.39:6581:gmdanightpaulista:melhorproxybr",
"92.112.200.194:6777:gmdanightpaulista:melhorproxybr",
"91.123.10.102:6644:gmdanightpaulista:melhorproxybr",
"23.129.252.177:6445:gmdanightpaulista:melhorproxybr",
"92.113.244.73:5760:gmdanightpaulista:melhorproxybr",
"92.112.171.117:6085:gmdanightpaulista:melhorproxybr",
"92.113.244.2:5689:gmdanightpaulista:melhorproxybr",
"85.198.47.217:6485:gmdanightpaulista:melhorproxybr",
"92.113.245.143:5829:gmdanightpaulista:melhorproxybr",
"92.112.202.128:6712:gmdanightpaulista:melhorproxybr",
"92.113.244.3:5690:gmdanightpaulista:melhorproxybr",
"91.123.10.194:6736:gmdanightpaulista:melhorproxybr",
"92.112.170.80:6049:gmdanightpaulista:melhorproxybr",
"92.112.200.68:6651:gmdanightpaulista:melhorproxybr",
"91.123.11.191:6457:gmdanightpaulista:melhorproxybr",
"92.112.202.208:6792:gmdanightpaulista:melhorproxybr",
"91.123.10.151:6693:gmdanightpaulista:melhorproxybr",
"92.112.200.8:6591:gmdanightpaulista:melhorproxybr",
"92.113.245.73:5759:gmdanightpaulista:melhorproxybr",
"92.113.245.109:5795:gmdanightpaulista:melhorproxybr",
"91.123.10.77:6619:gmdanightpaulista:melhorproxybr",
"92.112.170.221:6190:gmdanightpaulista:melhorproxybr",
"92.113.244.238:5925:gmdanightpaulista:melhorproxybr",
"92.112.200.170:6753:gmdanightpaulista:melhorproxybr",
"92.113.244.13:5700:gmdanightpaulista:melhorproxybr",
"23.129.252.152:6420:gmdanightpaulista:melhorproxybr",
"92.112.200.42:6625:gmdanightpaulista:melhorproxybr",
"91.123.10.190:6732:gmdanightpaulista:melhorproxybr",
"185.72.240.222:7258:gmdanightpaulista:melhorproxybr",
"91.123.11.48:6314:gmdanightpaulista:melhorproxybr",
"92.113.245.154:5840:gmdanightpaulista:melhorproxybr",
"91.123.11.110:6376:gmdanightpaulista:melhorproxybr",
"92.112.202.207:6791:gmdanightpaulista:melhorproxybr",
"91.123.8.112:6652:gmdanightpaulista:melhorproxybr",
"91.123.11.130:6396:gmdanightpaulista:melhorproxybr",
"92.113.245.215:5901:gmdanightpaulista:melhorproxybr",
"91.123.8.61:6601:gmdanightpaulista:melhorproxybr",
"23.129.253.83:6701:gmdanightpaulista:melhorproxybr",
"91.123.8.64:6604:gmdanightpaulista:melhorproxybr",
"91.123.10.245:6787:gmdanightpaulista:melhorproxybr",
"45.87.51.19:6579:cowards01:voltamosfieis",
"185.72.240.10:7046:cowards01:voltamosfieis",
"194.38.18.211:7273:cowards01:voltamosfieis",
"23.129.254.70:6052:cowards01:voltamosfieis",
"91.123.11.3:6269:cowards01:voltamosfieis",
"92.112.200.91:6674:cowards01:voltamosfieis",
"45.91.166.80:7139:cowards01:voltamosfieis",
"194.38.27.171:6732:cowards01:voltamosfieis",
"45.87.50.201:7261:cowards01:voltamosfieis",
"185.72.242.45:5728:cowards01:voltamosfieis",
"92.113.244.246:5933:cowards01:voltamosfieis",
"23.129.252.6:6274:cowards01:voltamosfieis",
"194.38.19.46:6608:cowards01:voltamosfieis",
"194.38.26.243:7304:cowards01:voltamosfieis",
"91.123.10.173:6715:cowards01:voltamosfieis",
"91.123.10.23:6565:cowards01:voltamosfieis",
"85.198.45.229:6153:cowards01:voltamosfieis",
"194.38.26.254:7315:cowards01:voltamosfieis",
"92.112.170.183:6152:cowards01:voltamosfieis",
"45.87.50.251:7311:cowards01:voltamosfieis",
"92.112.171.113:6081:cowards01:voltamosfieis",
"45.91.166.141:7200:cowards01:voltamosfieis",
"85.198.45.47:5971:cowards01:voltamosfieis",
"185.72.242.98:5781:cowards01:voltamosfieis",
"45.91.167.63:6622:cowards01:voltamosfieis",
"45.87.51.29:6589:cowards01:voltamosfieis",
"23.129.253.141:6759:cowards01:voltamosfieis",
"45.91.166.76:7135:cowards01:voltamosfieis",
"92.112.171.164:6132:cowards01:voltamosfieis",
"92.112.170.143:6112:cowards01:voltamosfieis",
"194.38.18.78:7140:cowards01:voltamosfieis",
"92.112.172.56:6328:cowards01:voltamosfieis",
"92.112.200.70:6653:cowards01:voltamosfieis",
"92.112.170.121:6090:cowards01:voltamosfieis",
"92.112.200.20:6603:cowards01:voltamosfieis",
"45.91.166.126:7185:cowards01:voltamosfieis",
"185.72.242.140:5823:cowards01:voltamosfieis",
"185.72.240.69:7105:cowards01:voltamosfieis",
"92.112.175.63:6336:cowards01:voltamosfieis",
"92.113.245.127:5813:cowards01:voltamosfieis",
"45.87.51.245:6805:cowards01:voltamosfieis",
"45.87.50.232:7292:cowards01:voltamosfieis",
"45.87.50.161:7221:cowards01:voltamosfieis",
"91.123.8.49:6589:cowards01:voltamosfieis",
"45.91.167.2:6561:cowards01:voltamosfieis",
"45.87.50.96:7156:cowards01:voltamosfieis",
"45.87.51.51:6611:cowards01:voltamosfieis",
"92.112.172.23:6295:cowards01:voltamosfieis",
"185.72.242.10:5693:cowards01:voltamosfieis",
"185.72.242.175:5858:cowards01:voltamosfieis",
"23.129.252.56:6324:erregaseteproxys:paunaaaaschinaaass",
"91.123.8.30:6570:erregaseteproxys:paunaaaaschinaaass",
"92.112.170.252:6221:erregaseteproxys:paunaaaaschinaaass",
"23.129.252.231:6499:erregaseteproxys:paunaaaaschinaaass",
"85.198.47.212:6480:erregaseteproxys:paunaaaaschinaaass",
"92.112.172.173:6445:erregaseteproxys:paunaaaaschinaaass",
"23.129.252.136:6404:erregaseteproxys:paunaaaaschinaaass",
"92.112.171.15:5983:erregaseteproxys:paunaaaaschinaaass",
"85.198.45.224:6148:erregaseteproxys:paunaaaaschinaaass",
"91.123.8.166:6706:erregaseteproxys:paunaaaaschinaaass",
"23.129.253.21:6639:erregaseteproxys:paunaaaaschinaaass",
"185.72.242.48:5731:erregaseteproxys:paunaaaaschinaaass",
"23.129.253.104:6722:erregaseteproxys:paunaaaaschinaaass",
"92.112.202.72:6656:erregaseteproxys:paunaaaaschinaaass",
"185.72.240.27:7063:erregaseteproxys:paunaaaaschinaaass",
"92.112.202.87:6671:erregaseteproxys:paunaaaaschinaaass",
"92.112.200.54:6637:erregaseteproxys:paunaaaaschinaaass",
"185.72.240.23:7059:erregaseteproxys:paunaaaaschinaaass",
"92.112.172.30:6302:erregaseteproxys:paunaaaaschinaaass",
"92.113.245.227:5913:erregaseteproxys:paunaaaaschinaaass",
"92.112.170.126:6095:erregaseteproxys:paunaaaaschinaaass",
"85.198.45.13:5937:erregaseteproxys:paunaaaaschinaaass",
"92.112.171.251:6219:erregaseteproxys:paunaaaaschinaaass",
"185.72.242.23:5706:erregaseteproxys:paunaaaaschinaaass",
"185.72.240.145:7181:erregaseteproxys:paunaaaaschinaaass",
"85.198.47.26:6294:erregaseteproxys:paunaaaaschinaaass",
"92.112.171.45:6013:erregaseteproxys:paunaaaaschinaaass",
"23.129.254.158:6140:erregaseteproxys:paunaaaaschinaaass",
"23.129.253.127:6745:erregaseteproxys:paunaaaaschinaaass",
"92.112.200.120:6703:erregaseteproxys:paunaaaaschinaaass",
"23.129.254.206:6188:erregaseteproxys:paunaaaaschinaaass",
"185.72.242.147:5830:erregaseteproxys:paunaaaaschinaaass",
"92.113.244.141:5828:erregaseteproxys:paunaaaaschinaaass",
"92.112.172.26:6298:erregaseteproxys:paunaaaaschinaaass",
"23.129.254.157:6139:erregaseteproxys:paunaaaaschinaaass",
"91.123.11.158:6424:erregaseteproxys:paunaaaaschinaaass",
"92.112.170.172:6141:erregaseteproxys:paunaaaaschinaaass",
"23.129.253.71:6689:erregaseteproxys:paunaaaaschinaaass",
"185.72.242.97:5780:erregaseteproxys:paunaaaaschinaaass",
"185.72.241.105:7397:erregaseteproxys:paunaaaaschinaaass",
"92.112.172.181:6453:erregaseteproxys:paunaaaaschinaaass",
"92.112.170.32:6001:erregaseteproxys:paunaaaaschinaaass",
"91.123.11.182:6448:erregaseteproxys:paunaaaaschinaaass",
"85.198.45.223:6147:erregaseteproxys:paunaaaaschinaaass",
"91.123.8.214:6754:erregaseteproxys:paunaaaaschinaaass",
"92.112.202.76:6660:erregaseteproxys:paunaaaaschinaaass",
"91.123.10.254:6796:erregaseteproxys:paunaaaaschinaaass",
"85.198.45.227:6151:erregaseteproxys:paunaaaaschinaaass",
"185.72.242.129:5812:erregaseteproxys:paunaaaaschinaaass",
"92.112.202.230:6814:erregaseteproxys:paunaaaaschinaaass",
"23.129.253.22:6640:erregaseteproxys:paunaaaaschinaaass",
"23.129.253.60:6678:erregaseteproxys:paunaaaaschinaaass",
"23.129.252.105:6373:erregaseteproxys:paunaaaaschinaaass",
"23.129.252.22:6290:erregaseteproxys:paunaaaaschinaaass",
"92.112.200.157:6740:erregaseteproxys:paunaaaaschinaaass",
"91.123.10.61:6603:erregaseteproxys:paunaaaaschinaaass",
"85.198.47.97:6365:erregaseteproxys:paunaaaaschinaaass",
"85.198.47.28:6296:erregaseteproxys:paunaaaaschinaaass",
"85.198.45.154:6078:erregaseteproxys:paunaaaaschinaaass",
"185.72.242.191:5874:erregaseteproxys:paunaaaaschinaaass",
"85.198.47.209:6477:erregaseteproxys:paunaaaaschinaaass",
"92.112.202.38:6622:erregaseteproxys:paunaaaaschinaaass",
"92.112.202.54:6638:erregaseteproxys:paunaaaaschinaaass",
"91.123.11.143:6409:erregaseteproxys:paunaaaaschinaaass",
"91.123.10.148:6690:erregaseteproxys:paunaaaaschinaaass",
"92.112.172.137:6409:erregaseteproxys:paunaaaaschinaaass",
"185.72.242.91:5774:erregaseteproxys:paunaaaaschinaaass",
"185.72.241.70:7362:erregaseteproxys:paunaaaaschinaaass",
"185.72.242.51:5734:erregaseteproxys:paunaaaaschinaaass",
"92.112.202.94:6678:erregaseteproxys:paunaaaaschinaaass",
"23.129.253.222:6840:erregaseteproxys:paunaaaaschinaaass",
"91.123.11.34:6300:erregaseteproxys:paunaaaaschinaaass",
"92.112.170.68:6037:erregaseteproxys:paunaaaaschinaaass",
"91.123.10.38:6580:erregaseteproxys:paunaaaaschinaaass",
"185.72.240.233:7269:erregaseteproxys:paunaaaaschinaaass",
"185.72.242.27:5710:erregaseteproxys:paunaaaaschinaaass",
"85.198.47.110:6378:erregaseteproxys:paunaaaaschinaaass",
"92.113.244.230:5917:erregaseteproxys:paunaaaaschinaaass",
"92.112.202.56:6640:erregaseteproxys:paunaaaaschinaaass",
"23.129.254.204:6186:erregaseteproxys:paunaaaaschinaaass",
"23.129.254.71:6053:erregaseteproxys:paunaaaaschinaaass",
"92.112.200.228:6811:erregaseteproxys:paunaaaaschinaaass",
"92.112.172.210:6482:erregaseteproxys:paunaaaaschinaaass",
"91.123.10.231:6773:erregaseteproxys:paunaaaaschinaaass",
"85.198.47.252:6520:erregaseteproxys:paunaaaaschinaaass",
"23.129.254.193:6175:erregaseteproxys:paunaaaaschinaaass",
"185.72.240.207:7243:erregaseteproxys:paunaaaaschinaaass",
"23.129.252.114:6382:erregaseteproxys:paunaaaaschinaaass",
"185.72.240.144:7180:erregaseteproxys:paunaaaaschinaaass",
"23.129.254.124:6106:erregaseteproxys:paunaaaaschinaaass",
"92.113.244.147:5834:erregaseteproxys:paunaaaaschinaaass",
"185.72.241.95:7387:erregaseteproxys:paunaaaaschinaaass",
"23.129.253.14:6632:erregaseteproxys:paunaaaaschinaaass",
"92.112.170.240:6209:erregaseteproxys:paunaaaaschinaaass",
"92.112.172.163:6435:erregaseteproxys:paunaaaaschinaaass",
"185.72.240.13:7049:erregaseteproxys:paunaaaaschinaaass",
"92.112.171.211:6179:erregaseteproxys:paunaaaaschinaaass",
"92.113.244.108:5795:erregaseteproxys:paunaaaaschinaaass",
"92.112.202.113:6697:erregaseteproxys:paunaaaaschinaaass",
"23.129.254.79:6061:erregaseteproxys:paunaaaaschinaaass",
"92.113.244.7:5694:erregaseteproxys:paunaaaaschinaaass",
"85.198.47.91:6359:erregaseteproxys:paunaaaaschinaaass",
"91.123.8.48:6588:erregaseteproxys:paunaaaaschinaaass",
"92.112.202.156:6740:erregaseteproxys:paunaaaaschinaaass",
"92.112.202.22:6606:erregaseteproxys:paunaaaaschinaaass",
"185.72.241.38:7330:erregaseteproxys:paunaaaaschinaaass",
"85.198.47.246:6514:erregaseteproxys:paunaaaaschinaaass",
"91.123.10.212:6754:erregaseteproxys:paunaaaaschinaaass",
"91.123.11.51:6317:erregaseteproxys:paunaaaaschinaaass",
"92.113.245.226:5912:erregaseteproxys:paunaaaaschinaaass",
"23.129.252.238:6506:erregaseteproxys:paunaaaaschinaaass",
"85.198.45.61:5985:erregaseteproxys:paunaaaaschinaaass",
"92.113.244.156:5843:erregaseteproxys:paunaaaaschinaaass",
"91.123.11.57:6323:erregaseteproxys:paunaaaaschinaaass",
"91.123.11.146:6412:erregaseteproxys:paunaaaaschinaaass",
"91.123.10.177:6719:erregaseteproxys:paunaaaaschinaaass",
"85.198.47.38:6306:erregaseteproxys:paunaaaaschinaaass",
"185.72.241.106:7398:erregaseteproxys:paunaaaaschinaaass",
"92.112.170.219:6188:erregaseteproxys:paunaaaaschinaaass",
"92.112.170.166:6135:erregaseteproxys:paunaaaaschinaaass",
"185.72.240.217:7253:erregaseteproxys:paunaaaaschinaaass",
"92.112.202.8:6592:erregaseteproxys:paunaaaaschinaaass",
"185.72.240.177:7213:erregaseteproxys:paunaaaaschinaaass",
"91.123.11.144:6410:erregaseteproxys:paunaaaaschinaaass",
"92.112.202.32:6616:erregaseteproxys:paunaaaaschinaaass",
"92.112.200.62:6645:erregaseteproxys:paunaaaaschinaaass",
"23.129.254.245:6227:erregaseteproxys:paunaaaaschinaaass",
"23.129.252.233:6501:erregaseteproxys:paunaaaaschinaaass",
"92.112.202.148:6732:erregaseteproxys:paunaaaaschinaaass",
"91.123.8.226:6766:erregaseteproxys:paunaaaaschinaaass",
"92.112.172.3:6275:erregaseteproxys:paunaaaaschinaaass",
"92.113.244.85:5772:erregaseteproxys:paunaaaaschinaaass",
"23.129.254.40:6022:erregaseteproxys:paunaaaaschinaaass",
"92.112.200.60:6643:erregaseteproxys:paunaaaaschinaaass",
"91.123.11.86:6352:erregaseteproxys:paunaaaaschinaaass",
"85.198.47.92:6360:erregaseteproxys:paunaaaaschinaaass",
"92.112.172.248:6520:erregaseteproxys:paunaaaaschinaaass",
"185.72.240.159:7195:erregaseteproxys:paunaaaaschinaaass",
"23.129.254.36:6018:erregaseteproxys:paunaaaaschinaaass",
"23.129.254.87:6069:erregaseteproxys:paunaaaaschinaaass",
"91.123.11.59:6325:erregaseteproxys:paunaaaaschinaaass",
"92.113.245.139:5825:erregaseteproxys:paunaaaaschinaaass",
"92.113.244.114:5801:erregaseteproxys:paunaaaaschinaaass",
"185.72.242.71:5754:erregaseteproxys:paunaaaaschinaaass",
"23.129.253.82:6700:erregaseteproxys:paunaaaaschinaaass",
"185.72.240.88:7124:erregaseteproxys:paunaaaaschinaaass",
"91.123.10.15:6557:erregaseteproxys:paunaaaaschinaaass",
"85.198.45.107:6031:erregaseteproxys:paunaaaaschinaaass",
"92.112.202.84:6668:erregaseteproxys:paunaaaaschinaaass",
"91.123.8.53:6593:erregaseteproxys:paunaaaaschinaaass",
"185.72.241.6:7298:ytkjcjxx:9m7974kkk4g4",
"185.72.242.85:5768:asueiave:uuhr2huecewg",
"185.72.240.5:7041:ytkjcjxx:9m7974kkk4g4",
"185.72.241.4:7296:asueiave:uuhr2huecewg",
"185.72.242.96:5779:asueiave:uuhr2huecewg",
"185.72.242.250:5933:asueiave:uuhr2huecewg",
"185.72.242.71:5754:asueiave:uuhr2huecewg",
"185.72.242.151:5834:ytkjcjxx:9m7974kkk4g4",
"185.72.240.22:7058:asueiave:uuhr2huecewg",
"185.72.242.145:5828:asueiave:uuhr2huecewg",
"185.72.241.147:7439:asueiave:uuhr2huecewg",
"185.72.241.221:7513:ytkjcjxx:9m7974kkk4g4",
"185.72.241.67:7359:asueiave:uuhr2huecewg",
"185.72.242.43:5726:asueiave:uuhr2huecewg",
"185.72.240.233:7269:asueiave:uuhr2huecewg",
"185.72.241.164:7456:ytkjcjxx:9m7974kkk4g4",
"185.72.240.8:7044:asueiave:uuhr2huecewg",
"185.72.242.98:5781:asueiave:uuhr2huecewg",
"185.72.241.108:7400:asueiave:uuhr2huecewg",
"185.72.242.147:5830:asueiave:uuhr2huecewg",
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
END_DATE = "2025-05-09T04:05:47.243Z"

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
