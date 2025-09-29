import os
import tkinter as tk
from tkinter import filedialog

# Função para formatar os dados e salvar no arquivo
def formatar_linhas(input_file, output_file):
    try:
        with open(input_file, 'r', encoding='utf-8') as infile:
            lines = infile.readlines()

        # Abrir o arquivo de saída para escrever os dados formatados
        with open(output_file, 'w', encoding='utf-8') as outfile:
            for line in lines:
                # Limpar espaços e quebras de linha
                line = line.strip()

                # Verifica se a linha contém dois valores separados por tabulação ou espaço
                if line:
                    # Substitui as vírgulas por pontos e separa os valores
                    values = line.split('\t') if '\t' in line else line.split()

                    if len(values) == 2:
                        # Escreve os dados no formato correto no arquivo
                        formatted_line = f"({repr(values[0].replace(",", "."))}, {repr(values[1].replace(",", "."))})"
                        outfile.write(formatted_line + ",\n")

        print(f"Arquivo formatado criado com sucesso: {output_file}")
    
    except Exception as e:
        print(f"Erro ao processar o arquivo: {e}")

# Função para selecionar o arquivo .txt
def selecionar_arquivo():
    root = tk.Tk()
    root.withdraw()  # Esconde a janela principal

    # Abre o diálogo para selecionar o arquivo de entrada
    input_file = filedialog.askopenfilename(
        title="Selecione o arquivo de entrada",
        filetypes=[("Text files", "*.txt")]
    )

    # Verifica se o usuário selecionou um arquivo
    if input_file:
        # Caminho do novo arquivo formatado no Desktop
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", "lista formatada branco.txt")
        formatar_linhas(input_file, desktop_path)
    else:
        print("Nenhum arquivo selecionado.")

# Chama a função para selecionar o arquivo e processá-lo
selecionar_arquivo()
