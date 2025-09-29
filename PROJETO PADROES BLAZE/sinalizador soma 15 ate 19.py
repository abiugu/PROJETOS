import pandas as pd
from tkinter import Tk, filedialog, ttk
from datetime import timedelta
import os

# Função para carregar o arquivo Excel
def carregar_arquivo():
    root = Tk()
    root.withdraw()  # Esconde a janela principal do Tkinter
    root.update()  # Força a atualização da janela
    caminho_arquivo = filedialog.askopenfilename(title="Selecione o arquivo Excel", filetypes=[("Arquivos Excel", "*.xlsx")])
    root.quit()  # Fecha a janela do Tkinter após a escolha do arquivo
    return caminho_arquivo

# Função para criar a barra de progresso
def mostrar_barra_progresso(total):
    root = Tk()
    root.title("Processando Planilha")

    # Configuração da barra de progresso
    barra = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
    barra.grid(row=0, column=0, padx=20, pady=20)
    barra["maximum"] = total  # Total de etapas

    # Exibição de um título ou rótulo para a barra
    label = ttk.Label(root, text="Processando, aguarde...")
    label.grid(row=1, column=0, padx=20, pady=10)

    return root, barra

# Função para realizar a análise do arquivo
def analisar_arquivo(caminho_arquivo, barra, root):
    # Carregar o arquivo Excel
    df = pd.read_excel(caminho_arquivo)

    # Garantir que a coluna de horário está no formato datetime
    df['Data'] = pd.to_datetime(df['Data'], format='%Y-%m-%dT%H:%M:%S.%fZ')

    # Criar a coluna de sinalização de soma 15 a 19
    df['soma_15_19'] = False
    df['Soma'] = None  # Nova coluna para armazenar a soma das jogadas (15 a 19)

    # Adicionar a coluna para marcar o acerto ou erro
    df['acerto_erro'] = None  # Inicializando a coluna
    df['minuto_acerto'] = None  # Nova coluna para armazenar o minuto de cada acerto

    # Loop para verificar as condições e analisar a soma 15, 16, 17, 18, 19
    for i in range(len(df) - 1):
        current_row = df.iloc[i]
        next_row = df.iloc[i + 1]

        # Verificar se as jogadas são no mesmo minuto e somam entre 15 e 19
        soma_jogadas = current_row['Número'] + next_row['Número']
        if current_row['Data'].minute == next_row['Data'].minute and 15 <= soma_jogadas <= 19:
            # Verificar se há uma jogada Red e Black, com Red sendo entre 1 a 7
            if (current_row['Cor'] == 'red' and 1 <= current_row['Número'] <= 7 and next_row['Cor'] == 'black') or \
               (next_row['Cor'] == 'red' and 1 <= next_row['Número'] <= 7 and current_row['Cor'] == 'black'):
                # Encontrar o menor número e somar ao minuto
                menor_numero = min(current_row['Número'], next_row['Número'])
                if current_row['Número'] == menor_numero:
                    df.at[i, 'soma_15_19'] = True  # Marcar a jogada com o menor número
                    df.at[i, 'Soma'] = soma_jogadas  # Armazenar a soma das jogadas
                    df.at[i, 'Data'] = current_row['Data'] + timedelta(minutes=int(menor_numero))  # Somar o número da jogada ao horário
                else:
                    df.at[i + 1, 'soma_15_19'] = True  # Marcar a jogada com o menor número
                    df.at[i + 1, 'Soma'] = soma_jogadas  # Armazenar a soma das jogadas
                    df.at[i + 1, 'Data'] = next_row['Data'] + timedelta(minutes=int(menor_numero))  # Somar o número da jogada ao horário

        # Atualizar a barra de progresso
        barra["value"] = i + 1
        root.update()  # Atualiza a barra de progresso e a interface gráfica

    # Agora, analisar se o acerto é "red", "white" ou "erro" nas jogadas seguintes após a hora somada
    for i in range(len(df)):
        current_row = df.iloc[i]
        if current_row['soma_15_19'] == True:
            # A hora do verdadeiro foi alterada, vamos encontrar esse minuto
            altered_time = current_row['Data'].replace(second=0, microsecond=0)

            # Procurar as jogadas no mesmo minuto ou no minuto seguinte
            future_rows = df[i+1:]  # Pega todas as linhas abaixo da linha atual

            # Procurar as jogadas no mesmo minuto
            future_same_minute = future_rows[future_rows['Data'].dt.minute == altered_time.minute].head(2)

            # Procurar as jogadas no minuto seguinte
            future_next_minute = future_rows[future_rows['Data'].dt.minute == altered_time.minute + 1].head(2)

            # Juntar as jogadas dos dois minutos
            all_next_rows = pd.concat([future_same_minute, future_next_minute])

            # Variáveis de controle
            acerto_count = 0
            acerto_branco_count = 0
            erro_count = 0

            # Analisar as 4 jogadas subsequentes
            for idx, row in all_next_rows.iterrows():
                if row['Cor'] == 'white' and acerto_branco_count == 0:  # Marcar apenas o primeiro acerto branco
                    df.at[i, 'acerto_erro'] = 'acerto branco'
                    df.at[i, 'minuto_acerto'] = row['Data'].minute
                    acerto_branco_count += 1
                    acerto_count += 1
                elif row['Cor'] == 'red' and acerto_count == 0:  # Marcar apenas o primeiro acerto red
                    df.at[i, 'acerto_erro'] = 'acerto'
                    df.at[i, 'minuto_acerto'] = row['Data'].minute
                    acerto_count += 1
                elif row['Cor'] == 'black':
                    erro_count += 1

                # Se houver 4 jogadas e nenhum red ou white, marcar erro na 4ª jogada
                if erro_count == 4 and acerto_count == 0 and acerto_branco_count == 0:
                    df.at[i, 'acerto_erro'] = 'erro'
                    df.at[i, 'minuto_acerto'] = row['Data'].minute

                # Limitar a contagem a 4 acertos para red e acerto branco
                if acerto_count > 0 or acerto_branco_count > 0:
                    break

    # Fechar a janela da barra de progresso após o processamento
    root.destroy()

    # Obter o caminho do Desktop e incluir o número escolhido no nome do arquivo
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", "historico com soma_15 e minutos", "dados_com_analise_soma.xlsx")
    
    # Salvar o arquivo com as alterações no Desktop
    df.to_excel(desktop_path, index=False)
    print(f"Arquivo processado e salvo como '{desktop_path}'.")

# Função principal para execução
def main():
    # Executar o processo para um arquivo
    caminho_arquivo = carregar_arquivo()
    if caminho_arquivo:
        print("Iniciando processamento do arquivo.")
        root, barra = mostrar_barra_progresso(0)  # Inicializa a barra com valor 0
        analisar_arquivo(caminho_arquivo, barra, root)  # Passa a barra para a função
    else:
        print("Nenhum arquivo selecionado.")

if __name__ == "__main__":
    main()
