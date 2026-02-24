import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox
import os

# === Função principal ===
def gerar_codigo_padroes():
    root = tk.Tk()
    root.withdraw()  # Esconde a janela principal
    arquivo = filedialog.askopenfilename(
        title="Selecione o arquivo Excel ou CSV",
        filetypes=[("Planilhas Excel", "*.xlsx *.xls"), ("Arquivos CSV", "*.csv")]
    )

    if not arquivo:
        messagebox.showwarning("Cancelado", "Nenhum arquivo foi selecionado.")
        return

    try:
        # Detecta o tipo de arquivo e lê
        if arquivo.endswith(".csv"):
            df = pd.read_csv(arquivo, sep=";", encoding="utf-8")
        else:
            df = pd.read_excel(arquivo)

        # Normaliza os nomes das colunas
        df.columns = df.columns.str.strip().str.lower()

        # Colunas obrigatórias
        colunas_necessarias = [
            "cor", "ciclos preto 100", "ciclos vermelho 100",
            "ciclos preto 50", "ciclos vermelho 50", "comparação cor anterior"
        ]
        faltando = [c for c in colunas_necessarias if c not in df.columns]
        if faltando:
            messagebox.showerror("Erro", f"Colunas faltando no arquivo: {faltando}")
            return

        # Gera o código automaticamente
        linhas_codigo = []
        for _, row in df.iterrows():
            try:
                cor = str(row["cor"]).strip().lower()
                ciclos100_preto = int(row["ciclos preto 100"])
                ciclos100_vermelhos = int(row["ciclos vermelho 100"])
                ciclos50_preto = int(row["ciclos preto 50"])
                ciclos50_vermelhos = int(row["ciclos vermelho 50"])
                comp_cor_anterior = str(row["comparação cor anterior"]).strip().lower()

                # Define a condição final conforme "comparação cor anterior"
                if comp_cor_anterior == "sim":
                    condicao_cor = "cor_atual == ultima_cor_anterior"
                elif comp_cor_anterior == "não":
                    condicao_cor = "cor_atual != ultima_cor_anterior"
                else:
                    condicao_cor = "# condição desconhecida"

                bloco = (
                    f"elif ciclos100_preto == {ciclos100_preto} and "
                    f"ciclos100_vermelhos == {ciclos100_vermelhos} and "
                    f"ciclos50_preto == {ciclos50_preto} and "
                    f"ciclos50_vermelhos == {ciclos50_vermelhos} and "
                    f"{condicao_cor}:\n"
                    f"    padrao_encontrado = True"
                )
                linhas_codigo.append(bloco)
            except Exception as e:
                print(f"Erro ao processar linha: {e}")

        # Junta tudo em um bloco de texto
        codigo_gerado = "\n".join(linhas_codigo)

        # Caminho do Desktop do usuário
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", "padroes_gerados.txt")

        # Salva em TXT
        with open(desktop_path, "w", encoding="utf-8") as f:
            f.write(codigo_gerado)

        # Mensagem de sucesso
        messagebox.showinfo("Sucesso", f"Código gerado e salvo em:\n{desktop_path}")

    except Exception as e:
        messagebox.showerror("Erro", f"Ocorreu um erro: {e}")

# === Executa o programa ===
if __name__ == "__main__":
    gerar_codigo_padroes()
