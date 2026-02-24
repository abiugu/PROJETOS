import requests
import time
import pandas as pd
from datetime import datetime, timedelta, timezone
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import os
import threading

# =====================================================
# CONFIGURAÇÕES
# =====================================================
URL_BASE = "https://blaze.bet.br/api/singleplayer-originals/originals/roulette_games/recent/history/1"
DESKTOP_PATH = os.path.join(os.path.expanduser("~"), "Desktop")
OUTPUT_FILE = os.path.join(DESKTOP_PATH, "sequencias_blaze.xlsx")

# =====================================================
# COR
# =====================================================
def cor_nome(c):
    return {0: "White", 1: "Red", 2: "Black"}.get(c, "Unknown")

# =====================================================
# COLETA DA API
# =====================================================
def coletar_dados_blaze(start_date, end_date):
    registros = []
    page = 1

    print("\n🚀 Iniciando análise de páginas da API Blaze")
    print(f"📅 Período: {start_date} → {end_date}\n")

    while True:
        print(f"📄 Baixando página {page}...")
        tentativas = 0

        while tentativas < 10:
            try:
                url = f"{URL_BASE}?startDate={start_date}&endDate={end_date}&page={page}"
                r = requests.get(url, timeout=20)

                if r.status_code == 200:
                    data = r.json().get("records", [])
                    if not data:
                        print("✅ Página vazia encontrada — fim da coleta\n")
                        return registros

                    registros.extend(data)
                    print(f"✅ Página {page} OK — {len(data)} registros")
                    page += 1
                    time.sleep(1)
                    break
                else:
                    tentativas += 1
                    print(f"⚠️ HTTP {r.status_code} — tentativa {tentativas}/5")
                    time.sleep(2.5)

            except Exception as e:
                tentativas += 1
                print(f"⚠️ Erro {e} — tentativa {tentativas}/5")
                time.sleep(2.5)

        if tentativas >= 10:
            print("❌ Falha definitiva. Encerrando coleta.")
            return registros

# =====================================================
# DATAFRAME BASE
# =====================================================
def records_para_df(records):
    linhas = []

    for r in records:
        dt_utc = datetime.fromisoformat(r["created_at"].replace("Z", "+00:00"))
        dt = dt_utc.astimezone(timezone(timedelta(hours=-3)))

        linhas.append({
            "DataHora": dt,                 # 🔑 chave real
            "Data": dt.date(),              # só data (excel)
            "Horário": dt.strftime("%H:%M"),
            "Cor": cor_nome(r["color"])
        })

    return pd.DataFrame(linhas).sort_values("DataHora")


# =====================================================
# ANÁLISE DE SEQUÊNCIAS
# =====================================================
def analisar_sequencias(df, minimo):
    resultados = []

    for horario, grupo_h in df.groupby("Horário"):
        cor_base = None
        inicio = None
        ultimo_dia = None
        cont = 0

        for data, grupo_d in grupo_h.groupby("Data"):
            cores = grupo_d["Cor"].tolist()
            datahora_quebra = grupo_d["DataHora"].max()

            # valida cor do dia
            if len(cores) == 1 and cores[0] in ["Red", "Black"]:
                cor_dia = cores[0]
            elif len(cores) == 2 and cores[0] == cores[1] and cores[0] in ["Red", "Black"]:
                cor_dia = cores[0]
            else:
                cor_dia = None

            # quebra por pulo de dia
            if ultimo_dia and data != ultimo_dia + timedelta(days=1):
                if cor_base and cont >= minimo:
                    resultados.append({
                        "Horário": horario,
                        "Cor base": cor_base,
                        "Data inicial": inicio,
                        "Data final": ultimo_dia,
                        "Dias consecutivos": cont,
                        "Data quebra": data,
                        "Dupla quebra": " + ".join(cores),

                        "Últimas 10": calcular_percentuais(df, datahora_quebra, 10),
                        "Últimas 25": calcular_percentuais(df, datahora_quebra, 25),
                        "Últimas 50": calcular_percentuais(df, datahora_quebra, 50),
                        "Últimas 100": calcular_percentuais(df, datahora_quebra, 100),
                    })
                cor_base = None
                cont = 0

            # quebra por white ou cor inválida
            if cor_dia is None:
                if cor_base and cont >= minimo:
                    resultados.append({
                        "Horário": horario,
                        "Cor base": cor_base,
                        "Data inicial": inicio,
                        "Data final": ultimo_dia,
                        "Dias consecutivos": cont,
                        "Data quebra": data,
                        "Dupla quebra": " + ".join(cores),

                        "Últimas 10": calcular_percentuais(df, datahora_quebra, 10),
                        "Últimas 25": calcular_percentuais(df, datahora_quebra, 25),
                        "Últimas 50": calcular_percentuais(df, datahora_quebra, 50),
                        "Últimas 100": calcular_percentuais(df, datahora_quebra, 100),
                    })

                cor_base = None
                cont = 0
                ultimo_dia = data
                continue

            if cor_base is None:
                cor_base = cor_dia
                inicio = data
                cont = 1
            elif cor_dia == cor_base:
                cont += 1
            else:
                if cont >= minimo:
                    resultados.append({
                        "Horário": horario,
                        "Cor base": cor_base,
                        "Data inicial": inicio,
                        "Data final": ultimo_dia,
                        "Dias consecutivos": cont,
                        "Data quebra": data,
                        "Dupla quebra": " + ".join(cores),

                        "Últimas 10": calcular_percentuais(df, datahora_quebra, 10),
                        "Últimas 25": calcular_percentuais(df, datahora_quebra, 25),
                        "Últimas 50": calcular_percentuais(df, datahora_quebra, 50),
                        "Últimas 100": calcular_percentuais(df, datahora_quebra, 100),
                    })

                cor_base = cor_dia
                inicio = data
                cont = 1

            ultimo_dia = data

    return pd.DataFrame(resultados)

# =====================================================
# EXECUÇÃO
# =====================================================
def executar():
    try:
        data_ini_local = datetime.combine(
            cal_ini.get_date(),
            datetime.min.time()
        ).replace(tzinfo=timezone(timedelta(hours=-3)))

        data_fim_local = datetime.combine(
            cal_fim.get_date(),
            datetime.max.time()
        ).replace(tzinfo=timezone(timedelta(hours=-3)))

        ini = data_ini_local.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
        fim = data_fim_local.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.999Z")

        minimo = int(entry_min.get())
    except:
        messagebox.showerror("Erro", "Preencha corretamente o mínimo de dias")
        return

    btn_executar.config(state="disabled")

    def tarefa():
        try:
            records = coletar_dados_blaze(ini, fim)
            df = records_para_df(records)
            seq = analisar_sequencias(df, minimo)

            with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as w:
                seq.to_excel(w, index=False, sheet_name="Sequências")

            root.after(0, lambda: messagebox.showinfo(
                "OK", "Planilha gerada com sucesso"
            ))

        except Exception as e:
            root.after(0, lambda: messagebox.showerror("Erro", str(e)))

        finally:
            root.after(0, lambda: btn_executar.config(state="normal"))

    threading.Thread(target=tarefa, daemon=True).start()

def records_para_df(records):
    linhas = []

    for r in records:
        dt_utc = datetime.fromisoformat(r["created_at"].replace("Z", "+00:00"))
        dt = dt_utc.astimezone(timezone(timedelta(hours=-3)))

        linhas.append({
            "DataHora": dt,                 # 🔑 chave real
            "Data": dt.date(),              # só data (excel)
            "Horário": dt.strftime("%H:%M"),
            "Cor": cor_nome(r["color"])
        })

    return pd.DataFrame(linhas).sort_values("DataHora")

def calcular_percentuais(df, datahora_quebra, n):
    # pega apenas jogadas ANTES da quebra
    base = df[df["DataHora"] < datahora_quebra].tail(n)

    if base.empty:
        return "R:0% | B:0% | W:0%"

    total = len(base)

    r = (base["Cor"] == "Red").sum() / total * 100
    b = (base["Cor"] == "Black").sum() / total * 100
    w = (base["Cor"] == "White").sum() / total * 100

    return f"R:{r:.0f}% | B:{b:.0f}% | W:{w:.0f}%"


# =====================================================
# INTERFACE
# =====================================================
root = tk.Tk()
root.title("Blaze • Sequências de Cor")

ttk.Label(root, text="Data inicial").grid(row=0, column=0)
cal_ini = DateEntry(root, date_pattern="dd/mm/yyyy")
cal_ini.grid(row=0, column=1)

ttk.Label(root, text="Data final").grid(row=1, column=0)
cal_fim = DateEntry(root, date_pattern="dd/mm/yyyy")
cal_fim.grid(row=1, column=1)

ttk.Label(root, text="Mínimo dias seguidos").grid(row=2, column=0)
entry_min = ttk.Entry(root)
entry_min.insert(0, "3")
entry_min.grid(row=2, column=1)

btn_executar = ttk.Button(root, text="Executar", command=executar)
btn_executar.grid(row=3, columnspan=2, pady=10)

root.mainloop()
