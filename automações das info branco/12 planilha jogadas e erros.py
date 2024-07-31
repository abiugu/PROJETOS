import os
import pandas as pd

def ler_arquivo(arquivo):
    with open(arquivo, 'r') as f:
        linhas = f.readlines()

    lista = []
    i = 0
    while i < len(linhas):
        if linhas[i].startswith("Sequencia:"):
            sequencia = linhas[i].split(": ")[1].strip()
            i += 1
            if i < len(linhas) and linhas[i].startswith("Quantidade:"):
                quantidade = int(linhas[i].split(": ")[1].strip())
                lista.append({"Sequência": f'\'{sequencia}',
                             "Total de Jogadas": quantidade})
                i += 1
            else:
                print(f"Erro: Formato inválido na linha {i + 1} do arquivo {arquivo}.")
                i += 1
        elif linhas[i].startswith("Quantidade:"):
            i += 1
        elif linhas[i].strip() == "":
            i += 1
        else:
            print(f"Ignorando linha {i + 1} do arquivo {arquivo}.")
            i += 1

    return lista

# Diretório onde os arquivos serão lidos e o arquivo de saída será salvo
desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
logs_path = os.path.join(desktop_path, 'LOGS')

# Verificar se a pasta LOGS existe, se não existir, criar
if not os.path.exists(logs_path):
    os.makedirs(logs_path)

# Arquivos de jogadas, erros e acertos
arquivo_jogadas = os.path.join(logs_path, "sequencias", 'sequencias 60 branco.txt')
arquivo_erros = os.path.join(logs_path, "sequencias", 'sequencias erros 60 branco.txt')
arquivo_acertos_brancos = os.path.join(logs_path, "sequencias", 'sequencias acertos branco 60.txt')
arquivo_acertos_gale_brancos = os.path.join(logs_path, "sequencias", 'sequencias acertos gale branco 60.txt')
arquivo_saida = os.path.join(logs_path, 'planilha acertos 60 branco.xlsx')

# Verificar se os arquivos existem
for arquivo in [arquivo_jogadas, arquivo_erros, arquivo_acertos_brancos, arquivo_acertos_gale_brancos]:
    if not os.path.exists(arquivo):
        print(f"Erro: O arquivo {arquivo} não existe.")
        exit()

# Ler os dados dos arquivos
jogadas = ler_arquivo(arquivo_jogadas)
if jogadas is None:
    exit()

erros = ler_arquivo(arquivo_erros)
if erros is None:
    exit()

acertos_brancos = ler_arquivo(arquivo_acertos_brancos)
if acertos_brancos is None:
    exit()

acertos_gale_brancos = ler_arquivo(arquivo_acertos_gale_brancos)
if acertos_gale_brancos is None:
    exit()

# Criar DataFrames
df_jogadas = pd.DataFrame(jogadas)
df_erros = pd.DataFrame(erros)
df_acertos_brancos = pd.DataFrame(acertos_brancos)
df_acertos_gale_brancos = pd.DataFrame(acertos_gale_brancos)

# Adicionar a coluna de erros totais ao DataFrame de jogadas (erro * 3)
df_jogadas["Erros Totais"] = df_jogadas["Sequência"].map(
    lambda x: df_erros.loc[df_erros["Sequência"] == x, "Total de Jogadas"].sum())

# Adicionar as colunas de acertos brancos e acertos gale brancos totais ao DataFrame de jogadas
df_jogadas["Acertos Brancos"] = df_jogadas["Sequência"].map(
    lambda x: df_acertos_brancos.loc[df_acertos_brancos["Sequência"] == x, "Total de Jogadas"].sum())

df_jogadas["Acertos Gale Brancos"] = df_jogadas["Sequência"].map(
    lambda x: df_acertos_gale_brancos.loc[df_acertos_gale_brancos["Sequência"] == x, "Total de Jogadas"].sum())

# Adicionar as colunas de percentual de acerto ao DataFrame de jogadas
df_jogadas["Percentual de Acerto Brancos"] = df_jogadas["Acertos Brancos"] / df_jogadas["Total de Jogadas"]
df_jogadas["Percentual de Acerto Gale Brancos"] = df_jogadas["Acertos Gale Brancos"] / df_jogadas["Total de Jogadas"]

# Adicionar a coluna de percentual de erros ao DataFrame de jogadas
df_jogadas["Percentual de Erros"] = df_jogadas["Erros Totais"] / df_jogadas["Total de Jogadas"]

# Selecionar apenas as colunas necessárias na ordem desejada
df_jogadas = df_jogadas[["Sequência", "Total de Jogadas", "Erros Totais", "Percentual de Erros",
                         "Acertos Brancos", "Percentual de Acerto Brancos",
                         "Acertos Gale Brancos", "Percentual de Acerto Gale Brancos"]]

# Salvar o DataFrame em um arquivo Excel
df_jogadas.to_excel(arquivo_saida, index=False)

print(f"Arquivo salvo com sucesso em: {arquivo_saida}")
