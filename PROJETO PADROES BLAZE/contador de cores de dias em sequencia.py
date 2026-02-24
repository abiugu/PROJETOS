import requests
from datetime import datetime, timedelta
from tkcalendar import Calendar
import tkinter as tk
from tkinter import messagebox
import time
import random
import pytz

# ============================================================
# TIMEZONES
# ============================================================
UTC = pytz.utc
BR = pytz.timezone("America/Sao_Paulo")

# ============================================================
# CALENDÁRIO PARA ESCOLHER DATA INICIAL E FINAL
# ============================================================
def obter_intervalo_datas():
    root = tk.Tk()
    root.title("Selecionar Datas Blaze")

    tk.Label(root, text="Selecione a Data Inicial:").pack(pady=5)
    cal_inicio = Calendar(root, selectmode='day', date_pattern='yyyy-mm-dd')
    cal_inicio.pack(pady=5)

    tk.Label(root, text="Selecione a Data Final:").pack(pady=5)
    cal_fim = Calendar(root, selectmode='day', date_pattern='yyyy-mm-dd')
    cal_fim.pack(pady=5)

    datas = {}

    def confirmar():
        inicio = cal_inicio.get_date()
        fim = cal_fim.get_date()

        dt_inicio = datetime.strptime(inicio, "%Y-%m-%d")
        dt_fim = datetime.strptime(fim, "%Y-%m-%d")

        if dt_fim < dt_inicio:
            messagebox.showerror("Erro", "A data FINAL não pode ser menor que a data INICIAL.")
            return

        datas["inicio"] = inicio
        datas["fim"] = fim
        root.destroy()

    tk.Button(root, text="Confirmar", command=confirmar).pack(pady=10)
    root.mainloop()
    return datas.get("inicio"), datas.get("fim")

# ============================================================
# OBTÉM OS DADOS DA BLAZE
# ============================================================
def obter_dados_blaze(start_date, end_date):
    # Datas escolhidas em BR
    dt_inicio_br = BR.localize(datetime.strptime(start_date, "%Y-%m-%d"))
    dt_fim_br = BR.localize(
        datetime.strptime(end_date, "%Y-%m-%d")
        .replace(hour=23, minute=59, second=59)
    )

    # Converter para UTC (API)
    start = dt_inicio_br.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    end   = dt_fim_br.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.999Z")

    print("\n🕒 Janela enviada para API (UTC):")
    print("START:", start)
    print("END  :", end)

    url_base = "https://blaze.bet.br/api/singleplayer-originals/originals/roulette_games/recent/history/1"
    page = 1
    all_records = []

    print("\n📥 Baixando dados...\n")

    while True:
        print(f"📄 Página {page}")

        url = f"{url_base}?startDate={start}&endDate={end}&page={page}"
        headers = {"User-Agent": random.choice(["Mozilla", "Chrome", "Safari"])}

        tentativas = 0
        sucesso = False

        while tentativas < 10:
            try:
                r = requests.get(url, headers=headers, timeout=10)

                # força erro se status != 200
                r.raise_for_status()

                dados = r.json().get("records", [])

                if not dados:
                    print("⛔ Não há mais páginas.")
                    return all_records

                all_records.extend(dados)
                sucesso = True
                break

            except requests.exceptions.HTTPError as e:
                tentativas += 1
                print(
                    f"⚠ Erro HTTP {r.status_code} "
                    f"(tentativa {tentativas}/10) — aguardando 2s"
                )
                time.sleep(2)

            except Exception as e:
                tentativas += 1
                print(
                    f"⚠ Erro inesperado ({e}) "
                    f"(tentativa {tentativas}/10) — aguardando 2s"
                )
                time.sleep(2)

        if not sucesso:
            print(f"❌ Falha definitiva na página {page}. Abortando coleta.")
            break

        page += 1
        time.sleep(1.2)  # pausa entre páginas (ajuda MUITO no 429)

    return all_records


# ============================================================
# CALCULAR MÉDIA POR DIA (ATÉ 2 JOGADAS POR HORÁRIO)
# ============================================================
def calcular_percentuais_por_horario(dados, total_dias_escolhidos):
    dias_horarios = {}

    agora_br = datetime.now(BR)
    dia_atual = agora_br.strftime("%Y-%m-%d")
    hora_atual_min = agora_br.hour * 60 + agora_br.minute

    for jogo in dados:

        if "created_at" not in jogo or "color" not in jogo:
            continue

        created_at = jogo["created_at"]

        # ---- PARSE UTC ----
        try:
            dt_utc = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%S.%fZ")
        except:
            try:
                dt_utc = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")
            except:
                continue

        dt_utc = UTC.localize(dt_utc)
        dt_br = dt_utc.astimezone(BR)

        dia = dt_br.strftime("%Y-%m-%d")
        horario = dt_br.strftime("%H:%M")

        hora_min_jogo = dt_br.hour * 60 + dt_br.minute

        # --- SE FOR HOJE, IGNORAR FUTURO ---
        if dia == dia_atual and hora_min_jogo > hora_atual_min:
            continue

        cor = jogo["color"]

        if cor not in (0, 1, 2):
            continue

        dias_horarios.setdefault(dia, {})
        dias_horarios[dia].setdefault(horario, [])
        dias_horarios[dia][horario].append(cor)

    consolidado = {}

    for dia, horarios in dias_horarios.items():
        for horario, cores in horarios.items():

            cores = cores[:2]

            if len(cores) == 1:
                if cores[0] == 1:
                    perc_red, perc_black = 100, 0
                elif cores[0] == 2:
                    perc_red, perc_black = 0, 100
                else:
                    continue
            else:
                c1, c2 = cores
                if c1 == c2 == 1:
                    perc_red, perc_black = 100, 0
                elif c1 == c2 == 2:
                    perc_red, perc_black = 0, 100
                else:
                    perc_red = 50 if 1 in cores else 0
                    perc_black = 50 if 2 in cores else 0

            consolidado.setdefault(horario, {"red": [], "black": []})
            consolidado[horario]["red"].append(perc_red)
            consolidado[horario]["black"].append(perc_black)

    resultados_red = []
    resultados_black = []

    for horario, valores in consolidado.items():
        if len(valores["red"]) != total_dias_escolhidos:
            continue

        media_red = sum(valores["red"]) / total_dias_escolhidos
        media_black = sum(valores["black"]) / total_dias_escolhidos

        if media_red >= 90:
            resultados_red.append((horario, media_red, len(valores["red"])))

        if media_black >= 90:
            resultados_black.append((horario, media_black, len(valores["black"])))

    resultados_red.sort(key=lambda x: x[1], reverse=True)
    resultados_black.sort(key=lambda x: x[1], reverse=True)

    return resultados_red, resultados_black

# ============================================================
# PROCESSAMENTO PRINCIPAL
# ============================================================
def gerar_previsoes(start_date, end_date):
    print(f"\nIniciando análise entre {start_date} e {end_date}...\n")

    dados = obter_dados_blaze(start_date, end_date)
    if not dados:
        print("‼ Nenhum dado obtido.")
        return

    print(f"Total de registros recebidos: {len(dados)}\n")

    dt_i = datetime.strptime(start_date, "%Y-%m-%d")
    dt_f = datetime.strptime(end_date, "%Y-%m-%d")
    total_dias = (dt_f - dt_i).days + 1

    print("🔎 Calculando predominância de cores...\n")

    reds, blacks = calcular_percentuais_por_horario(dados, total_dias)

    print("🔴 RED (+90%):")
    for h, p, d in reds:
        print(f"{h} → {p:.2f}% ({d} dias)")

    print("\n⚫ BLACK (+90%):")
    for h, p, d in blacks:
        print(f"{h} → {p:.2f}% ({d} dias)")

    print(f"\n✔ Processo concluído às {datetime.now(BR).strftime('%Y-%m-%d %H:%M:%S')}\n")

# ============================================================
# EXECUÇÃO
# ============================================================
def iniciar():
    data_inicio, data_fim = obter_intervalo_datas()

    if not (data_inicio and data_fim):
        messagebox.showerror("Erro", "Datas inválidas.")
        return

    gerar_previsoes(data_inicio, data_fim)

if __name__ == "__main__":
    iniciar()
