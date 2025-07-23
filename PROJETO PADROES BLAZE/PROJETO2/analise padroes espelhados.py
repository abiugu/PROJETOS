import os
import pandas as pd
import time
from collections import defaultdict
from tqdm import tqdm

def ler_lista_cores():
    """Lê a planilha de histórico de jogadas e retorna a lista de cores na ordem correta (de baixo para cima)."""
    desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
    arquivo_path = os.path.join(desktop_path, 'historico blaze.xlsx')

    try:
        print("Carregando dados da planilha...")
        for _ in tqdm(range(10), desc="Carregando", ncols=100):
            time.sleep(0.1)  # Simula o carregamento
        
        df = pd.read_excel(arquivo_path)
        df = df.iloc[::-1].reset_index(drop=True)
        lista_cores = df["Cor"].str.lower().tolist()
        return lista_cores, df
    except Exception as e:
        print(f"Erro ao ler a planilha: {e}")
        return [], None

def analisar_padroes_espelhados(lista_cores, tamanho_sequencia, df):
    """Analisa padrões que possuem uma sequência espelhada imediatamente após eles."""
    padroes = defaultdict(lambda: {
        "Total": 0,
        "BW_Acerto_Direto": 0,
        "BW_Acerto_Gale": 0,
        "RW_Acerto_Direto": 0,
        "RW_Acerto_Gale": 0,
        "Erros": 0,
        "Linhas_Acertos": []
    })

    log_linhas = []
    total_sequencias = len(lista_cores) - (2 * tamanho_sequencia) - 1
    if total_sequencias < 1:
        print("Poucos dados para análise. Escolha um tamanho de sequência menor.")
        return padroes

    for i in tqdm(range(total_sequencias), desc="Analisando padrões", ncols=100):
        sequencia = tuple(lista_cores[i:i + tamanho_sequencia])
        sequencia_espelhada = tuple(lista_cores[i + tamanho_sequencia:i + 2 * tamanho_sequencia][::-1])
        
        if sequencia == sequencia_espelhada:
            proxima_cor = lista_cores[i + 2 * tamanho_sequencia]
            segunda_cor = lista_cores[i + 2 * tamanho_sequencia + 1] if i + 2 * tamanho_sequencia + 1 < len(lista_cores) else None
            
            padroes[sequencia]["Total"] += 1
            
            if proxima_cor in ["black", "white"]:
                padroes[sequencia]["BW_Acerto_Direto"] += 1
                padroes[sequencia]["Linhas_Acertos"].append(df.index[i + 2 * tamanho_sequencia])
            elif segunda_cor in ["black", "white"]:
                padroes[sequencia]["BW_Acerto_Gale"] += 1

            if proxima_cor in ["red", "white"]:
                padroes[sequencia]["RW_Acerto_Direto"] += 1
                padroes[sequencia]["Linhas_Acertos"].append(df.index[i + 2 * tamanho_sequencia])
            elif segunda_cor in ["red", "white"]:
                padroes[sequencia]["RW_Acerto_Gale"] += 1
            
            log_linhas.append(f"Sequência: {sequencia}, Linha: {i + 2 * tamanho_sequencia}, Cor Esperada: {proxima_cor}")

    salvar_log(log_linhas, tamanho_sequencia)
    salvar_resultado(padroes, tamanho_sequencia)
    return padroes

def salvar_log(log_linhas, tamanho_sequencia):
    """Salva o log das análises em um arquivo de texto na área de trabalho."""
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", "Logs padroes espelhados")
    log_path = os.path.join(desktop_path, f"log_padroes_espelhados{tamanho_sequencia}.txt")

    with open(log_path, "w", encoding="utf-8") as file:
        for linha in log_linhas:
            file.write(linha + "\n")

    print(f"Log salvo em: {log_path}")

def salvar_resultado(padroes, tamanho_sequencia):
    """Salva o resultado da análise em uma planilha Excel."""
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", "Resultados padroes double")
    os.makedirs(desktop_path, exist_ok=True)
    resultado_path = os.path.join(desktop_path, f"Analise_espelhada{tamanho_sequencia}.xlsx")

    df_resultado = []

    for padrao, dados in padroes.items():
        sequencia_formatada = " → ".join(padrao)
        total = dados["Total"]
        acertos_bw = dados["BW_Acerto_Direto"] + dados["BW_Acerto_Gale"]
        acertos_rw = dados["RW_Acerto_Direto"] + dados["RW_Acerto_Gale"]
        percentual_acertos_bw = round((acertos_bw / total * 100), 1) if total > 0 else 0
        percentual_acertos_rw = round((acertos_rw / total * 100), 1) if total > 0 else 0

        df_resultado.append({
            "Sequência": sequencia_formatada,
            "Total Tentativas": total,
            "BW Acertos Diretos": dados["BW_Acerto_Direto"],
            "BW Acertos Gale 1": dados["BW_Acerto_Gale"],
            "RW Acertos Diretos": dados["RW_Acerto_Direto"],
            "RW Acertos Gale 1": dados["RW_Acerto_Gale"],
            "Erros": dados["Erros"],
            "Percentual Acertos BW": percentual_acertos_bw,
            "Percentual Acertos RW": percentual_acertos_rw,
        })

    df_resultado = pd.DataFrame(df_resultado)

    with pd.ExcelWriter(resultado_path, engine="xlsxwriter") as writer:
        df_resultado.to_excel(writer, index=False, sheet_name="Análise Espelhada")
        workbook = writer.book
        worksheet = writer.sheets["Análise Espelhada"]
        formato = workbook.add_format({"bold": True, "border": 1, "align": "center"})

        for col_num, value in enumerate(df_resultado.columns.values):
            worksheet.write(0, col_num, value, formato)

        worksheet.set_column(0, len(df_resultado.columns) - 1, 15)

    print(f"Resultado salvo em: {resultado_path}")


def main():
    lista_cores, df = ler_lista_cores()
    if not lista_cores:
        print("Não foi possível carregar os dados da planilha.")
        return
    while True:
        try:
            comprimento_sequencia = int(input("\nDigite o comprimento da sequência desejada (ou 0 para sair): "))
            if comprimento_sequencia == 0:
                print("Finalizando o programa...")
                break
            padroes = analisar_padroes_espelhados(lista_cores, comprimento_sequencia, df)
            if padroes:
                print("Análise concluída! Verifique a planilha e o log de acertos.")
            else:
                print("Nenhum padrão encontrado.")
        except ValueError:
            print("Erro: Digite um número válido.")

if __name__ == "__main__":
    main()
