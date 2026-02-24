import requests
import datetime
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from openpyxl import Workbook
import os
import random

# ============================================================
# 📌 Função para baixar dados da Blaze
# ============================================================
def obter_dados_blaze(start_date, end_date):
    start = f"{start_date}T00:00:00.000Z"
    end   = f"{end_date}T23:59:59.999Z"

    url_base = "https://blaze.bet.br/api/singleplayer-originals/originals/roulette_games/recent/history/1"
    page = 1
    all_records = []

    print("\n📥 Baixando dados...")


    while True:
        print(f"📄 Baixando página {page}...")

        url = f"{url_base}?startDate={start}&endDate={end}&page={page}"
        headers = {"User-Agent": random.choice(["Mozilla", "Chrome", "Safari"])}

        tentativas = 0
        sucesso = False

        while tentativas < 10:
            try:
                r = requests.get(url, headers=headers, timeout=10)
                r.raise_for_status()

                dados = r.json().get("records", [])
                if not dados:
                    print("⛔ Fim das páginas.\n")
                    return all_records

                all_records.extend(dados)
                sucesso = True
                break

            except Exception as e:
                tentativas += 1
                print(f"⚠ Erro página {page} ({tentativas}/10): {e}")
                time.sleep(3) 

        if not sucesso:
            print(f"❌ Página {page} ignorada após falhas.")
            page += 1
            continue

        page += 1
        time.sleep(1)

# ============================================================
# 📌 Agrupar jogadas por dia e horário
# ============================================================
def agrupar_por_horario(registros):
    dias = {}

    for r in registros:
        dt = datetime.datetime.fromisoformat(r["created_at"].replace("Z", "+00:00"))
        dia = dt.date().isoformat()
        hora = dt.strftime("%H:%M")

        color = r["color"]
        if color == 0:   cor = "white"
        elif color == 1: cor = "red"
        elif color == 2: cor = "black"
        else: continue

        if dia not in dias:
            dias[dia] = {}

        if hora not in dias[dia]:
            dias[dia][hora] = []

        dias[dia][hora].append(cor)

    return dias

# ============================================================
# 📌 Determinar cor dominante
# ============================================================
def cor_dominante(lista):
    if len(lista) == 1:
        return lista[0]  
    else:
        if lista[0] == lista[1]:
            return lista[0]
        else:
            return None

# ============================================================
# 📌 Encontrar sequências consecutivas por horário
# ============================================================
def encontrar_sequencias(dias_processados):
    sequencias = []

    todos_dias = sorted(dias_processados.keys())

    horarios = set()
    for d in dias_processados:
        horarios.update(dias_processados[d].keys())
    horarios = sorted(horarios)

    for horario in horarios:
        ultima_cor = None
        inicio_seq = None
        contador = 0

        for dia in todos_dias:
            cor = dias_processados[dia].get(horario, None)

            if cor is None:
                if contador > 0:
                    sequencias.append((horario, ultima_cor, inicio_seq, dia_anterior, contador))
                ultima_cor = None
                inicio_seq = None
                contador = 0

            else:
                if cor == ultima_cor:
                    contador += 1
                else:
                    if contador > 0:
                        sequencias.append((horario, ultima_cor, inicio_seq, dia_anterior, contador))
                    ultima_cor = cor
                    inicio_seq = dia
                    contador = 1

            dia_anterior = dia

        if contador > 0:
            sequencias.append((horario, ultima_cor, inicio_seq, dia_anterior, contador))

    return sequencias

# ============================================================
# 📌 Exportar Excel
# ============================================================
def exportar_excel(sequencias_filtradas):
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    caminho = os.path.join(desktop, "sequencias_horarios.xlsx")

    wb = Workbook()
    ws = wb.active
    ws.title = "Sequências"

    ws.append(["Horário", "Cor", "Data Início", "Data Fim", "Dias Seguidos"])

    for seq in sequencias_filtradas:
        ws.append(list(seq))

    wb.save(caminho)
    return caminho

# ============================================================
# 📌 Processo principal (thread)
# ============================================================
def rodar_analise():
    try:
        start_date = inicio_cal.get_date().strftime("%Y-%m-%d")
        end_date   = fim_cal.get_date().strftime("%Y-%m-%d")
        minimo     = int(entrada_minimo.get())

        lbl_status.config(text="Baixando dados da API...")
        registros = obter_dados_blaze(start_date, end_date)

        lbl_status.config(text="Processando dados...")
        dias = agrupar_por_horario(registros)

        dias_proc = {}
        for dia in dias:
            dias_proc[dia] = {}
            for h in dias[dia]:
                c = cor_dominante(dias[dia][h])
                if c:
                    dias_proc[dia][h] = c

        sequencias = encontrar_sequencias(dias_proc)

        filtradas = [seq for seq in sequencias if seq[4] >= minimo]

        lbl_status.config(text="Exportando Excel...")
        caminho = exportar_excel(filtradas)

        messagebox.showinfo("Finalizado", f"Arquivo salvo em:\n{caminho}")
        lbl_status.config(text="Concluído!")

    except Exception as e:
        messagebox.showerror("Erro", str(e))
        lbl_status.config(text="Erro")

# ============================================================
# 📌 Tkinter (Interface com calendário)
# ============================================================
janela = tk.Tk()
janela.title("Analisador de Sequências - Blaze")

tk.Label(janela, text="Data Início:").pack()
inicio_cal = DateEntry(janela, date_pattern="yyyy-mm-dd")
inicio_cal.pack()

tk.Label(janela, text="Data Fim:").pack()
fim_cal = DateEntry(janela, date_pattern="yyyy-mm-dd")
fim_cal.pack()

tk.Label(janela, text="Mínimo de dias seguidos:").pack()
entrada_minimo = tk.Entry(janela)
entrada_minimo.insert(0, "3")
entrada_minimo.pack()

def iniciar_thread():
    t = threading.Thread(target=rodar_analise)
    t.start()

btn = tk.Button(janela, text="Iniciar Análise", command=iniciar_thread)
btn.pack(pady=10)

lbl_status = tk.Label(janela, text="")
lbl_status.pack()

janela.mainloop()
