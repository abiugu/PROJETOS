import pandas as pd
import os
import tkinter as tk
from tkinter import messagebox

# Função de cálculo dos acertos com proteção (tentativas múltiplas) e Gale (tentativas extras)
def calcular_acertos():
    try:
        # Obter entradas
        numero_escolhido = int(entry_numero.get())
        pular_x = int(entry_pular_x.get())
        pular_y = int(entry_pular_y.get())
        gale = int(entry_gale.get())  # Número de tentativas extras (Gale)

        # Construindo o caminho para o arquivo Excel na área de trabalho
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", "historico blaze teste.xlsx")
        
        # Carregar o arquivo xlsx
        df = pd.read_excel(desktop_path)  # Lê o arquivo Excel da área de trabalho

        # Filtrar as linhas que correspondem ao número escolhido
        df_filtrado = df[df['Número'] == numero_escolhido]
        
        if df_filtrado.empty:
            messagebox.showinfo("Resultado", f"Nenhuma aparição do número {numero_escolhido} encontrada.")
            return

        acertos = 0
        total_aparicoes = len(df_filtrado)

        # Criar uma lista para controlar as aparições já acertadas
        aparicoes_acertadas = set()

        # Verifica cada aparição do número escolhido
        for index, row in df_filtrado.iterrows():
            acerto_na_tentativa = False

            # Primeira tentativa: Verificar a linha inicial (sem o Gale)
            next_row_1 = df.iloc[index + pular_y] if index + pular_y < len(df) else None
            if next_row_1 is not None:
                cor1 = next_row_1['Cor']

                # Pula X jogadas para verificar a cor da segunda ocorrência
                next_row_2 = df.iloc[index + pular_y + pular_x] if index + pular_y + pular_x < len(df) else None
                if next_row_2 is not None:
                    cor2 = next_row_2['Cor']

                    # Se a cor for igual, é um acerto
                    if cor1 == cor2:
                        acerto_na_tentativa = True

            # Gale: Tentativas extras
            if not acerto_na_tentativa:  # Se o acerto não ocorrer na primeira tentativa
                for gale_index in range(1, gale + 1):  # Gale > 0 significa tentativas extras
                    # Tenta pular X e Y jogadas extras dependendo do número de Gale
                    next_row_1 = df.iloc[index + pular_y + gale_index] if index + pular_y + gale_index < len(df) else None
                    if next_row_1 is not None:
                        cor1 = next_row_1['Cor']

                        # Pula X jogadas para verificar a cor da segunda ocorrência
                        next_row_2 = df.iloc[index + pular_y + gale_index + pular_x] if index + pular_y + gale_index + pular_x < len(df) else None
                        if next_row_2 is not None:
                            cor2 = next_row_2['Cor']

                            # Se a cor for igual, é um acerto
                            if cor1 == cor2:
                                acerto_na_tentativa = True
                                break  # Se houver um acerto, sai do loop de Gale

            # Se houver um acerto em pelo menos uma das tentativas, conta como 1 acerto por sequência
            if acerto_na_tentativa and index not in aparicoes_acertadas:
                acertos += 1  # Contabiliza um acerto por sequência
                aparicoes_acertadas.add(index)  # Marca a aparição como acertada

        # Calcular o percentual de acertos
        percentual_acertos = (acertos / total_aparicoes) * 100 if total_aparicoes else 0
        resultado = (f"Total de aparições do número {numero_escolhido}: {total_aparicoes}\n"
                     f"Total de acertos: {acertos}\n"
                     f"Percentual de acertos: {percentual_acertos:.2f}%")
        
        # Exibir o resultado na janela
        resultado_label.config(text=resultado)
    
    except Exception as e:
        messagebox.showerror("Erro", f"Ocorreu um erro: {e}")

# Criando a janela principal
root = tk.Tk()
root.title("Calculadora de Acertos com Gale")

# Tamanho da janela
root.geometry("400x450")

# Label e entrada para o número escolhido
label_numero = tk.Label(root, text="Escolha um número entre 0 e 14:")
label_numero.pack(pady=10)
entry_numero = tk.Entry(root)
entry_numero.pack(pady=5)

# Label e entrada para pular Y linhas (primeira cor)
label_pular_y = tk.Label(root, text="Quantas linhas pular para verificar a primeira cor?")
label_pular_y.pack(pady=10)
entry_pular_y = tk.Entry(root)
entry_pular_y.pack(pady=5)

# Label e entrada para pular X linhas (segunda cor)
label_pular_x = tk.Label(root, text="Quantas linhas pular para verificar a segunda cor?")
label_pular_x.pack(pady=10)
entry_pular_x = tk.Entry(root)
entry_pular_x.pack(pady=5)

# Label e entrada para o número de Gale
label_gale = tk.Label(root, text="Quantas tentativas extras de Gale deseja?")
label_gale.pack(pady=10)
entry_gale = tk.Entry(root)
entry_gale.pack(pady=5)

# Botão para calcular
button_calcular = tk.Button(root, text="Calcular Acertos", command=calcular_acertos)
button_calcular.pack(pady=20)

# Label para exibir o resultado
resultado_label = tk.Label(root, text="Resultado será exibido aqui", justify=tk.LEFT)
resultado_label.pack(pady=10)

# Rodando a janela
root.mainloop()
