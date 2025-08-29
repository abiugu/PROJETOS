import pandas as pd
import itertools
from tkinter import Tk, filedialog, Toplevel, Listbox, MULTIPLE, END, Button, Label, messagebox
from tkinter import simpledialog
import os
import time

# =========================
# UI helpers
# =========================
def escolher_arquivo():
    root = Tk()
    root.withdraw()
    caminho = filedialog.askopenfilename(
        title="Selecione o arquivo Excel",
        filetypes=[("Excel files", "*.xlsx")]
    )
    root.quit()
    return caminho

def perguntar_tipo_assertividade():
    root = Tk(); root.withdraw()
    val = simpledialog.askstring(
        "Tipo de Assertividade",
        "Escolha o tipo de assertividade:\n"
        "1 = Acertos Comuns (padrão)\n"
        "2 = Apenas Brancos",
        initialvalue="1"
    )
    if val is None:
        return "1"
    return val.strip()

def selecionar_colunas_iteracao(df):
    selecionadas = []

    def confirmar():
        sel = [listbox.get(i) for i in listbox.curselection()]
        if not sel:
            if not messagebox.askyesno(
                "Nenhuma coluna selecionada",
                "Nenhuma coluna foi selecionada para iterar.\n"
                "Isso gerará apenas um resumo único com os filtros fixos.\n\nDeseja continuar?"
            ):
                return
        selecionadas.extend(sel)
        top.destroy()

    top = Toplevel()
    top.title("Escolha as colunas para iterar (combinações)")
    top.geometry("560x460")

    Label(top, text="Selecione as colunas que devem entrar nas COMBINAÇÕES:").pack(pady=8)

    listbox = Listbox(top, selectmode=MULTIPLE, width=70, height=20)
    for col in df.columns:
        listbox.insert(END, col)
    listbox.pack(padx=10, pady=8)

    Button(top, text="Confirmar", command=confirmar).pack(pady=10)

    top.grab_set()
    top.wait_window()
    return selecionadas

def coletar_filtros_fixos(df):
    root = Tk()
    root.withdraw()

    filtros_fixos = {}
    for col in df.columns:
        try:
            unicos = pd.unique(df[col].dropna())[:20]
            amostra = ", ".join(map(lambda v: str(v), unicos))
        except Exception:
            amostra = ""
        prompt = (
            f"Coluna: {col}\n"
            f"Valores (amostra): {amostra}\n\n"
            f"Digite um valor para FILTRAR essa coluna (igualdade),\n"
            f"ou deixe em branco para NÃO filtrar:"
        )
        val = simpledialog.askstring("Filtro fixo (opcional)", prompt)
        if val is None:
            continue
        if val.strip() != "":
            filtros_fixos[col] = val.strip()

    root.destroy()
    return filtros_fixos

def perguntar_min_acerto():
    root = Tk(); root.withdraw()
    while True:
        val = simpledialog.askfloat(
            "Mínimo de acerto (%)",
            "Informe o percentual mínimo de acerto para considerar (ex.: 70):",
            initialvalue=90,
            minvalue=0.0, maxvalue=100.0
        )
        if val is None:
            return 90
        try:
            return round(float(val), 2)
        except Exception:
            messagebox.showerror("Valor inválido", "Digite um número válido entre 0 e 100.")

def perguntar_min_total():
    root = Tk(); root.withdraw()
    while True:
        val = simpledialog.askinteger(
            "Mínimo de amostras",
            "Informe o mínimo de entradas por combinação (ex.: 10):",
            initialvalue=10,
            minvalue=1
        )
        if val is None:
            return 10
        try:
            return int(val)
        except Exception:
            messagebox.showerror("Valor inválido", "Digite um número inteiro (>=1).")

# =========================
# Núcleo rápido (vetorizado)
# =========================

def _detectar_coluna_verificacao(df):
    candidatos = [
        "Verificação", "Verificacao", "verificação", "verificacao",
        "Resultado", "Status", "Check", "Outcome",
        "Verificação Branco", "Verificacao Branco"
    ]
    for c in candidatos:
        if c in df.columns:
            return c
    for col in df.columns:
        low = col.lower()
        if ("verific" in low) or ("result" in low) or ("status" in low) or ("outcome" in low) or ("check" in low):
            return col
    raise ValueError("Não encontrei coluna de verificação (ex.: 'Verificação', 'Resultado', 'Status').")

def analisar_combinacoes_fast(df, colunas_iterar, filtros_fixos, min_acerto=90, min_total=1, tipo_assertividade="1"):
    if not isinstance(colunas_iterar, list):
        colunas_iterar = list(colunas_iterar) if colunas_iterar else []

    # 1) Filtros fixos
    df_work = df.copy()
    for col, val in (filtros_fixos or {}).items():
        if col in df_work.columns:
            df_work = df_work[df_work[col].astype(str) == str(val)]
    if df_work.empty:
        return pd.DataFrame()

    # 2) Detecta coluna de verificação
    col_verif = _detectar_coluna_verificacao(df_work)

    # 3) Define tokens conforme tipo escolhido
    s = df_work[col_verif].astype(str).str.strip().str.lower()
    if tipo_assertividade == "2":
        success_tokens = {"branco direto", "branco gale"}
    else:
        success_tokens = {
            "acerto direto", "acerto gale", "acerto", "win", "verde",
            "branco direto", "branco gale"
        }
    df_work["is_acerto"] = s.isin(success_tokens).astype("int8")

    # 4) Resumo único
    if not colunas_iterar:
        total = len(df_work)
        acertos = int(df_work["is_acerto"].sum())
        erros = int(total - acertos)
        perc = round(acertos / total * 100, 2) if total else 0.0
        if perc < float(min_acerto) or total < int(min_total):
            return pd.DataFrame()
        return pd.DataFrame([{
            "Total Entradas": total,
            "Acertos": acertos,
            "Erros": erros,
            "Acerto (%)": perc,
            "Erro (%)": round(100 - perc, 2),
        }])

    # 5) Agrupamento
    for col in colunas_iterar:
        if col in df_work.columns:
            df_work[col] = df_work[col].astype("category")
    g = df_work.groupby(colunas_iterar, observed=True, sort=False)
    agg = g["is_acerto"].agg(total="count", acertos="sum").reset_index()
    agg["erros"] = agg["total"] - agg["acertos"]
    agg["Acerto (%)"] = (agg["acertos"] / agg["total"] * 100).round(2)
    agg["Erro (%)"] = (agg["erros"] / agg["total"] * 100).round(2)

    out = agg.loc[
        (agg["Acerto (%)"] >= float(min_acerto)) &
        (agg["total"] >= int(min_total))
    ].copy()

    out = out.rename(columns={
        "total": "Total Entradas",
        "acertos": "Acertos",
        "erros": "Erros",
    })

    out = out.sort_values(["Acerto (%)", "Total Entradas"], ascending=[False, False], ignore_index=True)
    return out

# =========================
# Execução principal
# =========================
def main():
    start_time = time.time()

    caminho_arquivo = escolher_arquivo()
    if not (caminho_arquivo and os.path.exists(caminho_arquivo)):
        print("❌ Nenhum arquivo selecionado ou caminho inválido.")
        return

    try:
        df = pd.read_excel(caminho_arquivo, engine="openpyxl")
    except Exception as e:
        print(f"❌ Erro ao ler o Excel: {e}")
        return

    colunas_iterar = selecionar_colunas_iteracao(df)
    filtros_fixos = coletar_filtros_fixos(df)
    min_acerto = perguntar_min_acerto()
    min_total = perguntar_min_total()
    tipo_assertividade = perguntar_tipo_assertividade()

    try:
        df_resultado = analisar_combinacoes_fast(
            df,
            colunas_iterar=colunas_iterar,
            filtros_fixos=filtros_fixos,
            min_acerto=min_acerto,
            min_total=min_total,
            tipo_assertividade=tipo_assertividade
        )
    except ValueError as e:
        messagebox.showerror("Erro", str(e))
        print(f"❌ {e}")
        return
    except Exception as e:
        messagebox.showerror("Erro inesperado", str(e))
        print(f"❌ Erro inesperado: {e}")
        return

    base_name = "resultado_combinacoes_fast"
    if colunas_iterar:
        base_name += "_" + "_".join([str(c).replace(" ", "_") for c in colunas_iterar])
    base_name += f"_min{int(min_total)}_{int(min_acerto)}pct"

    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", f"{base_name}.xlsx")
    try:
        df_resultado.to_excel(desktop_path, index=False)
        ok_msg = (
            f"✅ Arquivo salvo com sucesso em:\n{desktop_path}\n\n"
            f"Colunas iteradas: {colunas_iterar if colunas_iterar else 'nenhuma'}\n"
            f"Filtros fixos: {filtros_fixos if filtros_fixos else 'nenhum'}\n"
            f"Mínimo de acerto: {min_acerto:.2f}% | Mínimo de amostras: {min_total}\n"
            f"Tipo de assertividade: {'Apenas Brancos' if tipo_assertividade=='2' else 'Comum'}"
        )
        try:
            messagebox.showinfo("Concluído", ok_msg)
        except Exception:
            pass
        print(ok_msg)
    except Exception as e:
        try:
            messagebox.showerror("Erro ao salvar", str(e))
        except Exception:
            pass
        print(f"❌ Erro ao salvar: {e}")

    elapsed_time = time.time() - start_time
    print(f"⏱️ Tempo de execução: {elapsed_time:.2f} segundos")

if __name__ == "__main__":
    main()
