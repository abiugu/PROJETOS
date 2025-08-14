import requests
import time
import random
import os
import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8')

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.59"
]

START_DATE = "2025-01-01T04:00:00.000Z"
END_DATE = "2025-08-12T23:05:47.000Z"

def traduzir_cor(cor):
    return {0: "white", 1: "red", 2: "black"}.get(cor, "unknown")

def obter_dados_blaze_sem_proxy():
    url_base = "https://blaze.bet.br/api/singleplayer-originals/originals/roulette_games/recent/history/1"
    all_records = []
    page = 1

    while True:
        url = f"{url_base}?startDate={START_DATE}&endDate={END_DATE}&page={page}"
        headers = {"User-Agent": random.choice(USER_AGENTS)}

        while True:  # tenta até conseguir a mesma página
            try:
                print(f"🔄 Tentando capturar página {page}...")
                response = requests.get(url, headers=headers, timeout=10)

                if response.status_code == 200:
                    data = response.json().get("records", [])
                    if not data:
                        print("📭 Nenhuma nova informação. Finalizando...")
                        return all_records
                    all_records.extend(data)
                    print(f"✅ Página {page} coletada com sucesso. Total: {len(all_records)} registros.")
                    time.sleep(3)  # ✅ Delay de 5 segundos entre páginas
                    page += 1
                    break  # próxima página

                else:
                    print(f"⚠️ Erro HTTP {response.status_code}. Retentando em 5s...")
                    time.sleep(3)

            except Exception as e:
                print(f"❌ Erro na página {page}: {e}. Retentando em 5s...")
                time.sleep(5)

def salvar_dados_em_planilha(records):
    if not records:
        print("📭 Nenhum dado para salvar.")
        return

    for record in records:
        if "color" in record:
            record["color"] = traduzir_cor(record["color"])

    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    caminho_arquivo = os.path.join(desktop, "historico_blaze_agosto.xlsx")

    df = pd.DataFrame(records)
    df.to_excel(caminho_arquivo, index=False)
    print(f"✅ Dados salvos em {caminho_arquivo}")

if __name__ == "__main__":
    print("🚀 Iniciando coleta sem proxy...\n")
    registros = obter_dados_blaze_sem_proxy()
    salvar_dados_em_planilha(registros)
