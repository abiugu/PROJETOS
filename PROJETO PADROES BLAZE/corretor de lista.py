import requests
import random
import time
import threading
import pytz
import pandas as pd
import tkinter as tk
from tkcalendar import Calendar
from datetime import datetime

# =========================================================
# TIMEZONES
# =========================================================
UTC = pytz.utc
BR = pytz.timezone("America/Sao_Paulo")

# =========================================================
# ORDENA HORÁRIOS (HH:MM) EM ORDEM DECRESCENTE
# =========================================================
def ordenar_horarios_desc(lista):
    horarios = []
    for h in lista:
        h = h.strip()
        if not h:
            continue
        try:
            horarios.append(datetime.strptime(h, "%H:%M").time())
        except:
            pass
    horarios.sort(reverse=True)
    return [h.strftime("%H:%M") for h in horarios]

# =========================================================
# BUSCAR DADOS DA API
# =========================================================
def obter_dados_blaze(start_date, end_date):
    url_base = "https://blaze.bet.br/api/singleplayer-originals/originals/roulette_games/recent/history/1"
    all_records = []
    page = 1

    print("\nIniciando coleta da API...\n")

    while True:
        print(f"Baixando página {page}...")
        url = f"{url_base}?startDate={start_date}&endDate={end_date}&page={page}"
        headers = {"User-Agent": random.choice(["Mozilla", "Chrome", "Safari"])}

        tentativas = 0

        while tentativas < 10:
            try:
                r = requests.get(url, headers=headers, timeout=10)

                # Retry apenas para erro 429
                if r.status_code == 429:
                    tentativas += 1
                    print(
                        f"⚠ Erro 429 na página {page} "
                        f"(tentativa {tentativas}/10) — aguardando 2s"
                    )
                    time.sleep(2.5)
                    continue

                r.raise_for_status()

                data = r.json().get("records", [])

                if not data:
                    print("Nenhuma página adicional encontrada.")
                    return all_records

                all_records.extend(data)
                page += 1
                time.sleep(2.5)
                break  # sucesso → sai do retry

            except Exception as e:
                print(f"Erro na página {page}: {e}")
                return all_records

        else:
            print(f"❌ Falha após 10 tentativas na página {page}. Encerrando coleta.")
            break

    print(f"\nTotal de registros obtidos: {len(all_records)}\n")
    return all_records

# =========================================================
# PROCESSAR DADOS (UTC → BR + DATA + HORA)
# =========================================================
def processar_dados(dados):
    df = pd.DataFrame(dados)

    cor_map = {0: "white", 1: "red", 2: "black"}
    df["Cor"] = df["color"].map(cor_map)

    df["created_at"] = (
        pd.to_datetime(df["created_at"], utc=True)
        .dt.tz_convert("America/Sao_Paulo")
    )

    df["Data"] = df["created_at"].dt.strftime("%Y-%m-%d")
    df["HoraMinuto"] = df["created_at"].dt.strftime("%H:%M")

    # ⚠️ AGRUPAR POR DATA + HORA
    return (
        df.groupby(["Data", "HoraMinuto"])["Cor"]
        .apply(list)
        .to_dict()
    )

# =========================================================
# VALIDAR JOGADA
# =========================================================
def validar_jogada(hora, cor_usuario, dados, data_escolhida):
    agora = datetime.now(BR)

    hoje_str = agora.strftime("%Y-%m-%d")
    hora_atual = agora.strftime("%H:%M")

    if data_escolhida == hoje_str and hora > hora_atual:
        return f"{hora} | FUTURO", "future"

    chave = (data_escolhida, hora)

    if chave in dados:
        cores = dados[chave]

        reds = cores.count("red")
        blacks = cores.count("black")
        whites = cores.count("white")  # Contando a cor white

        # Se houver apenas uma cor (não oposta)
        if len(cores) == 1:
            if cores[0] == cor_usuario or cores[0] == "white":
                return f"{hora} | WIN | {cores}", "win"
            else:
                return f"{hora} | LOSS | {cores}", "loss"

        # Se houver 2 cores (red e black), considera as regras de acerto ou erro
        if len(cores) == 2:
            if cor_usuario in cores or "white" in cores:
                return f"{hora} | WIN | {cores}", "win"
            else:
                return f"{hora} | LOSS | {cores}", "loss"

    return None, None
# =========================================================
# THREAD PRINCIPAL
# =========================================================
def executar(root, data, blacks, reds):
    try:
        # ----- DATA BR → UTC CORRETA PARA API -----
        data_br = datetime.strptime(data, "%Y-%m-%d")
        inicio_br = BR.localize(data_br.replace(hour=0, minute=0, second=0))
        fim_br = BR.localize(data_br.replace(hour=23, minute=59, second=59))

        start = inicio_br.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.000Z")
        end   = fim_br.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.999Z")

        dados_api = obter_dados_blaze(start, end)
        dados = processar_dados(dados_api)

        blacks = ordenar_horarios_desc(blacks)
        reds = ordenar_horarios_desc(reds)

        root.after(0, output.delete, "1.0", tk.END)

        # ================= BLACK =================
        output.insert(tk.END, "LISTA BLACK\n", "black_title")

        win_b = loss_b = 0
        for h in blacks:
            res, status = validar_jogada(h, "black", dados, data)
            if res:
                output.insert(tk.END, res + "\n", status)
                if status == "win": win_b += 1
                if status == "loss": loss_b += 1

        total_b = win_b + loss_b
        perc_b = (win_b / total_b * 100) if total_b > 0 else 0

        output.insert(
            tk.END,
            f"\nBLACK → WIN: {win_b} | LOSS: {loss_b} | RATE: {perc_b:.2f}%\n\n",
            "info"
        )

        # ================= RED =================
        output.insert(tk.END, "LISTA RED\n", "red_title")

        win_r = loss_r = 0
        for h in reds:
            res, status = validar_jogada(h, "red", dados, data)
            if res:
                output.insert(tk.END, res + "\n", status)
                if status == "win": win_r += 1
                if status == "loss": loss_r += 1

        total_r = win_r + loss_r
        perc_r = (win_r / total_r * 100) if total_r > 0 else 0

        output.insert(
            tk.END,
            f"\nRED → WIN: {win_r} | LOSS: {loss_r} | RATE: {perc_r:.2f}%\n",
            "info"
        )

        # ================= TOTAL GERAL =================
        total_win = win_b + win_r
        total_loss = loss_b + loss_r
        total_geral = total_win + total_loss
        perc_total = (total_win / total_geral * 100) if total_geral > 0 else 0

        output.insert(
            tk.END,
            f"\nTOTAL GERAL → WIN: {total_win} | LOSS: {total_loss} | RATE: {perc_total:.2f}%\n",
            "info"
        )

    finally:
        root.after(0, lambda: botao.config(state=tk.NORMAL))

# =========================================================
# UI
# =========================================================
def iniciar():
    botao.config(state=tk.DISABLED)

    data = cal.get_date()
    blacks = txt_black.get("1.0", tk.END).strip().splitlines()
    reds = txt_red.get("1.0", tk.END).strip().splitlines()

    threading.Thread(
        target=executar,
        args=(root, data, blacks, reds),
        daemon=True
    ).start()

# =========================================================
# INTERFACE
# =========================================================
root = tk.Tk()
root.title("Análise Blaze - Correção de Listas")
root.geometry("820x760")

tk.Label(root, text="Selecione a data").pack()
cal = Calendar(root, date_pattern="yyyy-mm-dd")
cal.pack(pady=5)

tk.Label(root, text="Horários BLACK").pack()
txt_black = tk.Text(root, height=6, width=40)
txt_black.pack()

tk.Label(root, text="Horários RED").pack()
txt_red = tk.Text(root, height=6, width=40)
txt_red.pack()

botao = tk.Button(root, text="Rodar análise", command=iniciar)
botao.pack(pady=15)

output = tk.Text(root, height=25, width=95)
output.pack(pady=10)

# ===== CORES =====
output.tag_config("win", foreground="green")
output.tag_config("loss", foreground="red")
output.tag_config("future", foreground="orange")
output.tag_config("black_title", foreground="black", font=("Arial", 10, "bold"))
output.tag_config("red_title", foreground="red", font=("Arial", 10, "bold"))
output.tag_config("info", foreground="blue")

root.mainloop()
