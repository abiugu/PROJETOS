import requests
from datetime import datetime, timedelta
import time
import threading
import tkinter as tk
from tkinter import messagebox
from tkcalendar import DateEntry
from openpyxl import Workbook
import os
import random

# ============================================================
# 📌 Função para baixar dados da Blaze (API UTC)
# ============================================================
def obter_dados_blaze(start_date, end_date):
    # Datas escolhidas no Brasil (UTC-3)
    start_local = datetime.strptime(start_date, "%Y-%m-%d")
    end_local   = datetime.strptime(end_date, "%Y-%m-%d")

    # Converter para UTC
    start_utc = start_local + timedelta(hours=3)

    end_utc_teorico = end_local + timedelta(days=1, hours=3) - timedelta(milliseconds=1)
    agora_utc = datetime.utcnow()
    end_utc = min(end_utc_teorico, agora_utc)

    start = start_utc.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    end   = end_utc.strftime("%Y-%m-%dT%H:%M:%S.%fZ")[:-4] + "Z"

    print("\n🧠 Janela da API (UTC):")
    print("START:", start)
    print("END  :", end)

    url = "https://blaze.bet.br/api/singleplayer-originals/originals/roulette_games/recent/history/1"
    page = 1
    all_records = []

    while True:
        print(f"📄 Página {page}")
        params = {"startDate": start, "endDate": end, "page": page}

        tentativas = 0
        while tentativas < 5:
            try:
                r = requests.get(
                    url,
                    params=params,
                    headers={"User-Agent": random.choice(["Mozilla", "Chrome", "Safari"])},
                    timeout=10
                )

                if r.status_code == 429:
                    tentativas += 1
                    print("⚠️ 429 — aguardando 2s")
                    time.sleep(2)
                    continue

                r.raise_for_status()
                dados = r.json()

                if not dados:
                    print("⛔ Fim dos dados.")
                    return all_records

                all_records.extend(dados)
                page += 1
                time.sleep(1)
                break

            except Exception as e:
                tentativas += 1
                print("❌ Erro:", e)
                time.sleep(2)

        else:
            print("⛔ 429 consecutivo detectado.")
            print("📌 Assumindo fim dos dados da API.")
            print(f"📊 Total coletado: {len(all_records)}\n")
            return all_records  


# ============================================================
# 📌 Agrupar por data/hora do BRASIL (UTC-3)
# ============================================================
def agrupar_por_horario(registros):
    dias = {}

    for r in registros:
        # 🔁 Converter UTC → Brasil
        dt_utc = datetime.fromisoformat(r["created_at"].replace("Z", "+00:00"))
        dt_br  = dt_utc - timedelta(hours=3)

        dia = dt_br.date().isoformat()
        hora = dt_br.strftime("%H:%M")

        color = r["color"]
        if color == 0:
            cor = "white"
        elif color == 1:
            cor = "red"
        elif color == 2:
            cor = "black"
        else:
            continue

        dias.setdefault(dia, {}).setdefault(hora, []).append(cor)

    return dias


# ============================================================
# 📌 Cor dominante
# ============================================================
def cor_dominante(lista):
    if len(lista) == 1:
        return lista[0]
    if len(lista) >= 2 and lista[0] == lista[1]:
        return lista[0]
    return None


# ============================================================
# 📌 Sequências
# ============================================================
def encontrar_sequencias(dias):
    sequencias = []

    datas = sorted(dias.keys())
    horarios = sorted({h for d in dias for h in dias[d]})

    for h in horarios:
        ultima_cor = None
        inicio = None
        contador = 0
        dia_ant = None

        for d in datas:
            cor = dias[d].get(h)

            if cor == ultima_cor and cor:
                contador += 1
            else:
                if contador > 0:
                    sequencias.append((h, ultima_cor, inicio, dia_ant, contador))
                if cor:
                    ultima_cor = cor
                    inicio = d
                    contador = 1
                else:
                    ultima_cor = None
                    inicio = None
                    contador = 0

            dia_ant = d

        if contador > 0:
            sequencias.append((h, ultima_cor, inicio, dia_ant, contador))

    return sequencias


# ============================================================
# 📌 Excel
# ============================================================
def exportar_excel(seqs):
    caminho = os.path.join(os.path.expanduser("~"), "Desktop", "sequencias_horarios.xlsx")
    wb = Workbook()
    ws = wb.active
    ws.title = "Sequências"

    ws.append(["Horário (BR)", "Cor", "Data Início", "Data Fim", "Dias Seguidos"])
    for s in seqs:
        ws.append(s)

    wb.save(caminho)
    return caminho


# ============================================================
# 📌 Processo principal
# ============================================================
def rodar():
    try:
        inicio = inicio_cal.get_date().strftime("%Y-%m-%d")
        fim    = fim_cal.get_date().strftime("%Y-%m-%d")
        minimo = int(entrada_minimo.get())

        registros = obter_dados_blaze(inicio, fim)

        if not registros:
            messagebox.showwarning("Aviso", "Nenhum dado encontrado.")
            return

        dias = agrupar_por_horario(registros)

        dias_proc = {}
        for d in dias:
            for h in dias[d]:
                c = cor_dominante(dias[d][h])
                if c:
                    dias_proc.setdefault(d, {})[h] = c

        seqs = encontrar_sequencias(dias_proc)
        filtradas = [s for s in seqs if s[4] >= minimo]

        if not filtradas:
            messagebox.showwarning("Aviso", "Nenhuma sequência encontrada.")
            return

        caminho = exportar_excel(filtradas)
        messagebox.showinfo("Finalizado", f"Arquivo salvo em:\n{caminho}")

    except Exception as e:
        messagebox.showerror("Erro", str(e))


# ============================================================
# 📌 Interface
# ============================================================
janela = tk.Tk()
janela.title("Sequências Blaze")

tk.Label(janela, text="Data início:").pack()
inicio_cal = DateEntry(janela, date_pattern="yyyy-mm-dd")
inicio_cal.pack()

tk.Label(janela, text="Data fim:").pack()
fim_cal = DateEntry(janela, date_pattern="yyyy-mm-dd")
fim_cal.pack()

tk.Label(janela, text="Mínimo de dias seguidos:").pack()
entrada_minimo = tk.Entry(janela)
entrada_minimo.insert(0, "3")
entrada_minimo.pack()

tk.Button(janela, text="Iniciar", command=lambda: threading.Thread(target=rodar, daemon=True).start()).pack(pady=10)

janela.mainloop()
