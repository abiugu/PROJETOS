import pandas as pd
import threading
import time
from tkinter import *
from tkinter import ttk, filedialog, messagebox
import os

# ==========================================================
# Função para identificar a cor baseada no número
# ==========================================================
def identificar_cor(numero):
    """
    Função que mapeia o número para sua respectiva cor:
    0 -> white, 1-7 -> red, 8-14 -> black.
    """
    try:
        numero = int(numero)  # Garantir que o número seja tratado como inteiro
        if numero == 0:
            return "white"
        elif 1 <= numero <= 7:
            return "red"
        elif 8 <= numero <= 14:
            return "black"
        else:
            return "qualquer"  # Caso o número esteja fora do intervalo (se necessário tratar outros casos)
    except ValueError:
        return "qualquer"  # Caso o número não seja válido

# ==========================================================
# Função para verificar se o padrão selecionado corresponde à sequência
# ==========================================================
def padrao_confere(padrao, trecho):
    """
    Verifica se o padrão selecionado pelo usuário corresponde exatamente ao trecho.
    """
    if len(padrao) != len(trecho):
        return False
    for p, t in zip(padrao, trecho):
        if p != t:  # Verifica se a sequência é igual, sem converter os valores novamente
            return False
    return True

# ==========================================================
# Função principal de análise
# ==========================================================
def executar_analise(arquivo, sequencia_selecionada, casas, cor_alvo, janela, barra, label_status, btn_iniciar, protecao_branco):
    try:
        label_status.config(text="🔍 Lendo arquivo...")
        janela.update_idletasks()

        # Ler o arquivo
        if arquivo.endswith(".csv"):
            df = pd.read_csv(arquivo)
        else:
            df = pd.read_excel(arquivo)

        # Normaliza colunas
        df.columns = [c.strip().capitalize() for c in df.columns]
        if "Número" not in df.columns:
            messagebox.showerror("Erro", "A planilha precisa ter a coluna 'Número'.")
            return

        # Mapeia a coluna "Número" para cores diretamente
        df["Cor"] = df["Número"].apply(identificar_cor)

        label_status.config(text="🧩 Processando padrões...")
        janela.update_idletasks()

        resultados = {}
        total_linhas = len(df)
        limite = total_linhas - len(sequencia_selecionada) - casas
        if limite < 0:
            messagebox.showwarning("Aviso", "Arquivo curto para o tamanho do padrão + casas.")
            btn_iniciar.config(state="normal")
            return

        contador = 0

        # Agora, filtramos apenas as sequências que correspondem exatamente à sequência escolhida
        for i in range(limite):
            # Extraímos a sequência de números da coluna 'Número' e as cores
            trecho_numeros = df["Número"].iloc[i:i+len(sequencia_selecionada)].tolist()
            trecho_cores = df["Cor"].iloc[i:i+len(sequencia_selecionada)].tolist()

            # Verificar se a sequência de números corresponde
            if padrao_confere(sequencia_selecionada, trecho_numeros):  # Comparar diretamente com os números
                acertos_total = 0
                acertos_gale_1 = 0
                acertos_gale_2 = 0
                erros = 0
                jogadas_total = 0  # Contador de jogadas totais

                for gale in range(1, casas + 1):  # Aqui 'casas' determina o número de Gales
                    proxima_numeros = df["Número"].iloc[i+len(sequencia_selecionada): i+len(sequencia_selecionada)+casas].tolist()
                    proxima_cores = df["Cor"].iloc[i+len(sequencia_selecionada): i+len(sequencia_selecionada)+casas].tolist()

                    jogadas_total += 1  # Contabilizando a jogada para cada Gale

                    # Contagem de acertos para cada gale específico
                    for j, numero in enumerate(proxima_numeros):
                        cor = proxima_cores[j]  # Cor associada ao número

                        if (cor == cor_alvo) or (protecao_branco and cor == "white"):
                            acertos_total += 1
                            if gale == 1 and j == 0:  # Acerto Gale 1 (primeiro acerto após o padrão)
                                acertos_gale_1 += 1
                            elif gale == 2 and j == 0:  # Acerto Gale 2 (primeiro acerto após o Gale 1)
                                acertos_gale_2 += 1
                            break
                    else:
                        erros += 1

                # Histórico dos últimos 1000 antes do padrão
                inicio_hist = max(0, i - 100)
                hist_norm = df["Número"].iloc[inicio_hist:i]
                pct_cor = (hist_norm.apply(identificar_cor) == cor_alvo).mean() * 100 if len(hist_norm) > 0 else 0

                # Armazenando os resultados agregados para cada padrão
                if tuple(sequencia_selecionada) not in resultados:
                    resultados[tuple(sequencia_selecionada)] = {
                        "acertos_total": 0, "acertos_gale_1": 0, "acertos_gale_2": 0,
                        "erros": 0, "total_ocorrencias": 0, "cor_pos_padrao": cor_alvo,
                        "protecao_branco": protecao_branco, "jogadas_total": 0
                    }

                resultados[tuple(sequencia_selecionada)]["acertos_total"] += acertos_total
                resultados[tuple(sequencia_selecionada)]["acertos_gale_1"] += acertos_gale_1
                resultados[tuple(sequencia_selecionada)]["acertos_gale_2"] += acertos_gale_2
                resultados[tuple(sequencia_selecionada)]["erros"] += erros
                resultados[tuple(sequencia_selecionada)]["total_ocorrencias"] += 1
                resultados[tuple(sequencia_selecionada)]["jogadas_total"] += jogadas_total

            # progresso
            contador += 1
            if contador % 20 == 0:
                progresso = int((contador / max(1, limite)) * 100)
                barra["value"] = progresso
                label_status.config(text=f"⚙️ Analisando... {progresso}%")
                janela.update_idletasks()
                time.sleep(0.001)

        if not resultados:
            barra["value"] = 100
            label_status.config(text="⚠️ Nenhum padrão encontrado.")
            messagebox.showinfo("Resultado", "Nenhum padrão encontrado.")
            btn_iniciar.config(state="normal")
            return

        # Agregando os resultados por padrão e calculando o percentual de acerto
        dados = []
        for padrao, valores in resultados.items():
            total_ocorrencias = valores["total_ocorrencias"]
            acertos_total = valores["acertos_total"]
            acertos_gale_1 = valores["acertos_gale_1"]
            acertos_gale_2 = valores["acertos_gale_2"]
            erros = valores["erros"]
            jogadas_total = valores["jogadas_total"]
            cor_pos_padrao = valores["cor_pos_padrao"]
            protecao_branco = "Sim" if valores["protecao_branco"] else "Não"
            
            # Cálculo correto do percentual de acerto
            if acertos_total + erros > 0:
                percentual_acerto = (acertos_total / (acertos_total + erros)) * 100
            else:
                percentual_acerto = 0

            dados.append({
                "Padrão encontrado": "-".join([p[0].upper() if p != "qualquer" else "Q" for p in padrao]),
                "Jogadas Totais": jogadas_total,
                "Acertos Total": acertos_total,
                "Acertos Gale 1": acertos_gale_1,
                "Acertos Gale 2": acertos_gale_2,
                "Erros": erros,
                "Percentual de Acerto Total (%)": round(percentual_acerto, 2),
                "Cor Pós-Padrão": cor_pos_padrao,
                "Proteção no Branco": protecao_branco
            })

        # Salvar os resultados finais em uma planilha
        df_result = pd.DataFrame(dados)

        # === Salvar em múltiplas planilhas ===
        salvar_em_multiplas_planilhas(df_result)

        barra["value"] = 100
        label_status.config(text="✅ Análise concluída!")
        btn_iniciar.config(state="normal")

        messagebox.showinfo(
            "Análise Concluída",
            f"Arquivo salvo na Área de Trabalho.\n\n"
            f"Total de ocorrências: {len(df_result)}\n"
            f"Rankeado por percentual de acerto:\n"
            f"{df_result[['Padrão encontrado', 'Percentual de Acerto Total (%)']].head()}"
        )

    except Exception as e:
        messagebox.showerror("Erro", f"Ocorreu um erro: {e}")
        btn_iniciar.config(state="normal")

# ==========================================================
# Função para salvar em múltiplas planilhas caso ultrapasse o limite do Excel
# ==========================================================
def salvar_em_multiplas_planilhas(df_result):
    """
    Função para salvar em múltiplas planilhas caso o número de linhas ultrapasse o limite do Excel
    """
    max_linhas = 1048576  # Limite do Excel para linhas por planilha
    planilha_numero = 1  # Contador para as planilhas
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    nome_saida_base = os.path.join(desktop_path, "analise_padroes_blaze")

    while len(df_result) > max_linhas:
        # Salvar a planilha atual
        df_result.iloc[:max_linhas].to_excel(f"{nome_saida_base}_{planilha_numero}.xlsx", index=False)
        
        # Atualizar os dados para salvar o restante em outra planilha
        df_result = df_result.iloc[max_linhas:]
        planilha_numero += 1
    
    # Salvar a última parte que sobrou
    df_result.to_excel(f"{nome_saida_base}_{planilha_numero}.xlsx", index=False)

# ==========================================================
# Interface Tkinter
# ==========================================================
def iniciar_interface():
    janela = Tk()
    janela.title("Analisador de Padrões Blaze 🔥")
    janela.geometry("600x750")  # Aumentar a altura e largura para mais espaço
    janela.resizable(True, True)  # Permitir redimensionamento da janela

    Label(janela, text="Analisador de Padrões - Blaze Double", font=("Arial", 14, "bold")).pack(pady=10)

    arquivo_path = StringVar()
    cor_alvo_selecionada = StringVar(value="")
    protecao_branco_ativada = BooleanVar(value=False)  # Variável para proteção no branco
    sequencia_selecionada = []  # Lista para armazenar a sequência selecionada

    # ======= Selecionar arquivo =======
    def selecionar_arquivo():
        caminho = filedialog.askopenfilename(
            title="Selecione o arquivo de rodadas",
            filetypes=[("Arquivos Excel ou CSV", "*.xlsx *.csv")]
        )
        arquivo_path.set(caminho)

    Button(janela, text="Selecionar Arquivo", command=selecionar_arquivo).pack(pady=5)
    Label(janela, textvariable=arquivo_path, wraplength=460, fg="blue").pack(pady=5)

    # ======= Exibir sequência selecionada =======
    Label(janela, text="Sequência Selecionada:").pack(pady=5)
    sequencia_display = Label(janela, text="Nenhuma sequência selecionada", font=("Arial", 12))
    sequencia_display.pack(pady=5)

    # ======= Botões de Números (0 a 14) =======
    Label(janela, text="Selecione um número (0 a 14):").pack(pady=5)

    frame_numeros = Frame(janela)
    frame_numeros.pack(pady=5)

    botoes_numeros = {}

    def selecionar_numero(numero):
        sequencia_selecionada.append(str(numero))  # Adiciona o número (como string)
        sequencia_display.config(text=" -> ".join(sequencia_selecionada))

    for i in range(15):
        botoes_numeros[i] = Button(frame_numeros, text=str(i), font=("Arial", 12), command=lambda i=i: selecionar_numero(i))
        botoes_numeros[i].grid(row=0, column=i, padx=5)

    # ======= Botões de cores (sem números) =======
    Label(janela, text="Selecione a cor (sem número específico):").pack(pady=5)

    frame_cores = Frame(janela)
    frame_cores.pack(pady=5)

    botoes_cores = {}

    def selecionar_cor(cor):
        sequencia_selecionada.append(cor)  # Adiciona a cor diretamente na sequência
        sequencia_display.config(text=" -> ".join(sequencia_selecionada))

    botoes_cores["red"] = Button(frame_cores, text="🔴", font=("Arial", 20), command=lambda: selecionar_cor("red"))
    botoes_cores["black"] = Button(frame_cores, text="⚫", font=("Arial", 20), command=lambda: selecionar_cor("black"))
    botoes_cores["white"] = Button(frame_cores, text="⚪", font=("Arial", 20), command=lambda: selecionar_cor("white"))

    for i, b in enumerate(botoes_cores.values()):
        b.grid(row=0, column=i, padx=10)

    # ======= Seleção da cor após a sequência =======
    Label(janela, text="Selecione a cor após a sequência:").pack(pady=10)

    frame_cor_alvo = Frame(janela)
    frame_cor_alvo.pack(pady=5)

    botoes_cor_alvo = {}

    def selecionar_cor_alvo(cor):
        cor_alvo_selecionada.set(cor)
        label_cor_alvo.config(text=f"Cor selecionada: {cor}")

    botoes_cor_alvo["red"] = Button(frame_cor_alvo, text="🔴", font=("Arial", 20), command=lambda: selecionar_cor_alvo("red"))
    botoes_cor_alvo["black"] = Button(frame_cor_alvo, text="⚫", font=("Arial", 20), command=lambda: selecionar_cor_alvo("black"))
    botoes_cor_alvo["white"] = Button(frame_cor_alvo, text="⚪", font=("Arial", 20), command=lambda: selecionar_cor_alvo("white"))

    for i, b in enumerate(botoes_cor_alvo.values()):
        b.grid(row=0, column=i, padx=10)

    # Exibir cor alvo selecionada
    label_cor_alvo = Label(janela, text="Cor selecionada: Nenhuma", font=("Arial", 12))
    label_cor_alvo.pack(pady=5)

    # ======= Botão para apagar a última seleção =======
    def apagar_ultima_selecao():
        if sequencia_selecionada:
            sequencia_selecionada.pop()  # Remove o último item da sequência
            sequencia_display.config(text=" -> ".join(sequencia_selecionada))

    Button(janela, text="Apagar Última Seleção", command=apagar_ultima_selecao).pack(pady=10)

    # ======= Checkbox para proteção no branco =======
    checkbox_protecao_branco = Checkbutton(janela, text="Proteger Branco (considerar acerto)", variable=protecao_branco_ativada)
    checkbox_protecao_branco.pack(pady=10)

    # ======= Entradas adicionais =======
    Label(janela, text="Casas à frente (1=Sem Gale, 2=Gale1, 3=Gale2):").pack()
    entrada_casas = Entry(janela, width=10)
    entrada_casas.pack(pady=5)

    barra = ttk.Progressbar(janela, length=400, mode="determinate")
    barra.pack(pady=20)
    label_status = Label(janela, text="Aguardando início...", fg="gray")
    label_status.pack()

    def iniciar_thread():
        arquivo = arquivo_path.get()
        cor_alvo = cor_alvo_selecionada.get()
        protecao_branco = protecao_branco_ativada.get()
        try:
            casas = int(entrada_casas.get())
        except ValueError:
            messagebox.showerror("Erro", "Os valores devem ser números inteiros.")
            return

        if not arquivo or not cor_alvo or not sequencia_selecionada:
            messagebox.showwarning("Aviso", "Preencha todos os campos e selecione a cor esperada.")
            return

        label_status.config(text="🟡 Preparando análise...")
        barra["value"] = 0
        btn_iniciar.config(state="disabled")

        thread = threading.Thread(
            target=executar_analise,
            args=(arquivo, sequencia_selecionada, casas, cor_alvo, janela, barra, label_status, btn_iniciar, protecao_branco)
        )
        thread.start()

    btn_iniciar = Button(janela, text="Iniciar Análise", command=iniciar_thread, bg="#4CAF50", fg="white", width=20)
    btn_iniciar.pack(pady=15)

    janela.mainloop()

# === Iniciar o programa ===
if __name__ == "__main__":
    iniciar_interface()
