import pandas as pd
from tkinter import filedialog, messagebox, Tk, Label, Button, Entry, Text, Scrollbar
from tkinter import ttk
import threading

# Variável global para armazenar o DataFrame
df = None

def load_file():
    def load():
        global df
        file_path = filedialog.askopenfilename(title="Selecione o arquivo Excel", filetypes=[("Excel Files", "*.xlsx;*.xls")])
        if not file_path:
            messagebox.showwarning("Erro", "Nenhum arquivo selecionado.")
            return
        try:
            df = pd.read_excel(file_path)
            messagebox.showinfo("Sucesso", "Arquivo carregado com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao carregar o arquivo: {str(e)}")

    thread = threading.Thread(target=load)
    thread.start()

def analyze_patterns():
    global df

    if df is None:
        messagebox.showwarning("Erro", "Nenhum arquivo carregado. Por favor, selecione um arquivo primeiro.")
        return

    color_map = {'v': 'red', 'p': 'black', 'b': 'white'}

    def number_to_color(num):
        if num == 0:
            return 'white'
        elif 1 <= num <= 7:
            return 'red'
        elif 8 <= num <= 14:
            return 'black'
        return None

    pattern_input = pattern_entry.get()
    mode = mode_var.get()
    gale_mode = gale_var.get()

    if mode == "Cor":
        try:
            pattern_list = [color_map[item.strip().lower()] for item in pattern_input.split()]
        except KeyError:
            messagebox.showwarning("Erro", "Por favor, insira iniciais de cores válidas ('V', 'P', 'B').")
            return
    elif mode == "Número":
        try:
            pattern_list = [int(item) for item in pattern_input.split()]
        except ValueError:
            messagebox.showwarning("Erro", "Por favor, insira um padrão válido (somente números separados por espaço).")
            return
    elif mode == "Ambos":
        try:
            pattern_list = [int(item) if item.isdigit() else color_map[item.strip().lower()] for item in pattern_input.split()]
        except ValueError:
            messagebox.showwarning("Erro", "Por favor, insira um padrão válido.")
            return

    df['Cor'] = df['Número'].apply(number_to_color)
    color_list = df[['Cor', 'Número']].values.tolist()[::-1]

    # Contadores de acertos para Gale 0 e Gale 1
    gale_0_counts = {'white': 0, 'red': 0, 'black': 0}
    gale_1_counts = {'white': 0, 'red': 0, 'black': 0}

    total_patterns = 0

    # Ajuste no loop para garantir que não passe do limite da lista
    max_index = len(color_list) - len(pattern_list) - 1  # Considera Gale 0 e Gale 1

    # Loop para buscar o padrão e registrar os acertos
    for i in range(max_index):
        current_pattern = []
        for j in range(len(pattern_list)):
            if isinstance(pattern_list[j], int):
                current_pattern.append(color_list[i + j][1])
            else:
                current_pattern.append(color_list[i + j][0])

        if current_pattern == pattern_list:
            total_patterns += 1
            gale_positions = [i + len(pattern_list) + g for g in range(2)]  # Gale 0 e Gale 1

            # Gale 0: Conta os acertos diretamente no Gale 0, permitindo múltiplas contagens
            if gale_positions[0] < len(color_list):
                color_0 = color_list[gale_positions[0]][0]
                gale_0_counts[color_0] += 1  # O Gale 0 agora conta todas as aparições
            
            # Gale 1: Conta acertos no Gale 1, mas só conta se não foi registrado em Gale 0 para a mesma aparição
            if gale_positions[1] < len(color_list):
                color_1 = color_list[gale_positions[1]][0]
            
                # Se a cor de Gale 1 for a mesma cor de Gale 0, não somamos
                if color_1 != color_0:  # Só conta se a cor for diferente da cor de Gale 0
                    gale_1_counts[color_1] += 1

    def compute_percentages(counts, total_patterns):
        return {color: (counts[color] / total_patterns) * 100 if total_patterns != 0 else 0 for color in counts}

    # Calcular os percentuais para Gale 0 e Gale 1
    gale_0_percentages = compute_percentages(gale_0_counts, total_patterns)
    gale_1_percentages = compute_percentages(gale_1_counts, total_patterns)

    # Percentual final acumulado (Gale 0 + Gale 1)
    final_percentages = {
        color: min(gale_0_percentages[color] + gale_1_percentages[color], 100)
        for color in gale_0_percentages
    }

    # Exibir os resultados
    result_text.delete(1.0, "end")
    if total_patterns == 0:
        result_text.insert("insert", f"Padrão '{pattern_input}' não encontrado no arquivo.")
        return

    result_message = f"Padrão '{pattern_input}' encontrado {total_patterns} vezes.\n"

    # Verificar qual Gale foi selecionado e mostrar apenas o respectivo Gale
    if gale_mode == "0":
        result_message += f"Percentual acumulado até Gale 0:\n"
        nome_cores = {"white": "Branco", "red": "Vermelho", "black": "Preto"}
        for color, prob in gale_0_percentages.items():
            result_message += f"{nome_cores[color]} - Gale 0: {gale_0_counts[color]}/{total_patterns} - {prob:.2f}%\n"
    elif gale_mode == "1":
        result_message += f"Percentual acumulado até Gale 1 (Gale 0 + Gale 1):\n"
        nome_cores = {"white": "Branco", "red": "Vermelho", "black": "Preto"}
        for color, prob in final_percentages.items():
            # Somando os acertos de Gale 0 e Gale 1
            total_gale_1 = gale_0_counts[color] + gale_1_counts[color]
            # Calculando o percentual de Gale 0 + Gale 1
            total_percentage = ((total_gale_1) / total_patterns) * 100
            result_message += f"{nome_cores[color]} - Gale 1: {total_gale_1}/{total_patterns} - {total_percentage:.2f}%\n"  # Exibe o percentual acumulado de Gale 0 + Gale 1

    result_text.insert("insert", result_message)

root = Tk()
root.title("Analisador de Padrões de Jogo")
root.geometry("500x500")

label = Label(root, text="Digite o padrão a ser analisado (exemplo: 'V P B B 8 3 V'): ")
label.pack(pady=10)

pattern_entry = Entry(root, width=30)
pattern_entry.pack(pady=10)

search_mode_label = Label(root, text="Modo de Busca")
search_mode_label.pack(pady=5)

mode_var = ttk.Combobox(root, values=["Cor", "Número", "Ambos"], state="readonly")
mode_var.set("Ambos")
mode_var.pack(pady=10)

gale_label = Label(root, text="Quantidade de Gale")
gale_label.pack(pady=5)

gale_var = ttk.Combobox(root, values=["0", "1"], state="readonly")
gale_var.set("1")
gale_var.pack(pady=10)

load_button = Button(root, text="Selecionar Arquivo", command=load_file)
load_button.pack(pady=10)

analyze_button = Button(root, text="Analisar", command=analyze_patterns)
analyze_button.pack(pady=10)

result_text = Text(root, height=10, width=50)
result_text.pack(pady=10)

scrollbar = Scrollbar(root, command=result_text.yview)
scrollbar.pack(side="right", fill="y")
result_text.config(yscrollcommand=scrollbar.set)

root.mainloop()
