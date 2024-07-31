import pandas as pd
import os

# Função para ler o conteúdo de um arquivo de texto e retornar como lista de dicionários
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
                             "Quantidade": quantidade})
                i += 1
            else:
                print(f"Erro: Formato inválido na linha {i + 1} do arquivo {arquivo}.")
                i += 1  # Avança para a próxima linha
        elif linhas[i].startswith("Quantidade:"):
            # Se a linha for uma quantidade sem uma sequência correspondente, pule
            i += 1
        elif linhas[i].strip() == "":
            # Pular linhas em branco
            i += 1
        else:
            # Ignorar linhas que não seguem o formato esperado
            print(f"Ignorando linha {i + 1} do arquivo {arquivo}.")
            i += 1  # Avança para a próxima linha

    return lista

# Diretório onde os arquivos serão lidos e o arquivo de saída será salvo
desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
logs_path = os.path.join(desktop_path, 'LOGS')

# Verificar se a pasta LOGS existe, se não existir, criar
if not os.path.exists(logs_path):
    os.makedirs(logs_path)

# Arquivos de jogadas e erros
arquivo_jogadas = os.path.join(logs_path, 'jogadas.txt')
arquivo_erros = os.path.join(logs_path, 'erros.txt')
arquivo_saida = os.path.join(logs_path, 'planilha_jogadas_erros.xlsx')

# Verificar se os arquivos existem
if not os.path.exists(arquivo_jogadas):
    print(f"Erro: O arquivo {arquivo_jogadas} não existe.")
    exit()
if not os.path.exists(arquivo_erros):
    print(f"Erro: O arquivo {arquivo_erros} não existe.")
    exit()

# Ler os dados dos arquivos
jogadas = ler_arquivo(arquivo_jogadas)
if jogadas is None:
    exit()

erros = ler_arquivo(arquivo_erros)
if erros is None:
    exit()

# Criar DataFrames
df_jogadas = pd.DataFrame(jogadas)
df_erros = pd.DataFrame(erros)

# Adicionar a coluna de erros totais ao DataFrame de jogadas (erro * 3)
df_jogadas["Erros Totais"] = df_jogadas["Sequência"].map(
    lambda x: df_erros.loc[df_erros["Sequência"] == x, "Quantidade"].sum() * 3)

# Adicionar a coluna de percentual de erro ao DataFrame de jogadas
df_jogadas["Percentual de Erro"] = (
    df_jogadas["Erros Totais"] / df_jogadas["Quantidade"])

# Calcular a média do percentual de erro
media_percentual_erro = df_jogadas["Percentual de Erro"].mean()

# Função para aplicar a formatação condicional
def formata_cor(val):
    return 'font-weight: bold;'

# Aplicar a formatação condicional em toda a planilha
df_jogadas_styled = df_jogadas.style

# Aplicar estilo negrito para todo o DataFrame
df_jogadas_styled = df_jogadas_styled.set_properties(**{'font-weight': 'bold'})

# Aplicar estilo de centralização e largura das colunas em toda a tabela
df_jogadas_styled = df_jogadas_styled.set_table_styles([
    {'selector': 'td, th', 'props': [
        ('text-align', 'center'), ('border', '1px solid black'), ('width', '17px')]},
    {'selector': 'th', 'props': [('background-color', 'lightgrey')]},
    {'selector': 'table', 'props': [
        ('width', '100%'), ('border-collapse', 'collapse')]},
])

# Salvar o DataFrame estilizado em um arquivo Excel
df_jogadas_styled.to_excel(arquivo_saida, index=False)

print(f"Arquivo salvo com sucesso em: {arquivo_saida}")
