import os

desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
file_path = os.path.join(desktop_path, "historico acertos e erros 26.02.txt")


# Lista para armazenar as linhas não em branco
non_empty_lines = []

# Abrir o arquivo para leitura
with open(file_path, "r") as file:
    # Ler todas as linhas do arquivo
    lines = file.readlines()
    # Filtrar as linhas não em branco
    non_empty_lines = [line for line in lines if line.strip()]

# Abrir o arquivo para escrita e escrever as linhas não em branco de volta
with open(file_path, "w") as file:
    file.writelines(non_empty_lines)

print("Linhas em branco removidas com sucesso.")
