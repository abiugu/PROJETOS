import os
import pandas as pd
from collections import defaultdict

def ler_lista_cores():
    """Lê a planilha de histórico de jogadas e retorna a lista de cores na ordem correta (de baixo para cima)."""
    desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
    arquivo_path = os.path.join(desktop_path, 'historico blaze.xlsx')

    try:
        df = pd.read_excel(arquivo_path)

        # 🔹 Inverte a ordem das linhas para ler de baixo para cima
        df = df.iloc[::-1].reset_index(drop=True)

        lista_cores = df["Cor"].str.lower().tolist()  # Obtém a coluna "Cor" e converte para minúsculas
        return lista_cores
    except Exception as e:
        print(f"Erro ao ler a planilha: {e}")
        return []

def analisar_padroes(lista_cores, tamanho_sequencia):
    """Analisa a frequência dos padrões e os acertos diretos e Gale 1."""
    padroes = defaultdict(lambda: {
        "Total": 0,
        "RW_Acerto_Direto": 0, "RW_Acerto_Gale": 0, "RW_Erros": 0,
        "BW_Acerto_Direto": 0, "BW_Acerto_Gale": 0, "BW_Erros": 0
    })

    total_sequencias = len(lista_cores) - tamanho_sequencia - 1

    if total_sequencias < 1:
        print("Poucos dados para análise. Escolha um tamanho de sequência menor.")
        return padroes

    for i in range(total_sequencias):
        sequencia = tuple(lista_cores[i:i + tamanho_sequencia])  # Captura a sequência de X jogadas
        proxima_cor = lista_cores[i + tamanho_sequencia]  # Primeira jogada futura
        segunda_cor = lista_cores[i + tamanho_sequencia + 1] if i + tamanho_sequencia + 1 < len(lista_cores) else None  # Segunda jogada futura

        padroes[sequencia]["Total"] += 1

        # Red | White
        if proxima_cor in ['red', 'white']:
            padroes[sequencia]["RW_Acerto_Direto"] += 1
        elif segunda_cor in ['red', 'white']:
            padroes[sequencia]["RW_Acerto_Gale"] += 1
        else:
            padroes[sequencia]["RW_Erros"] += 1

        # Black | White
        if proxima_cor in ['black', 'white']:
            padroes[sequencia]["BW_Acerto_Direto"] += 1
        elif segunda_cor in ['black', 'white']:
            padroes[sequencia]["BW_Acerto_Gale"] += 1
        else:
            padroes[sequencia]["BW_Erros"] += 1

    return padroes

def salvar_resultado(padroes, tamanho_sequencia):
    """Salva o resultado da análise em uma planilha Excel."""
    desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop', 'Resultados padroes double')
    resultado_path = os.path.join(desktop_path, f'Analise padroes {tamanho_sequencia}.xlsx')

    df_resultado = []

    for padrao, dados in padroes.items():
        sequencia_formatada = " → ".join(padrao)

        rw_total = dados["Total"]
        rw_acertos = dados["RW_Acerto_Direto"] + dados["RW_Acerto_Gale"]
        rw_percentual = round((rw_acertos / rw_total * 100), 1) if rw_total > 0 else 0

        bw_total = dados["Total"]
        bw_acertos = dados["BW_Acerto_Direto"] + dados["BW_Acerto_Gale"]
        bw_percentual = round((bw_acertos / bw_total * 100), 1) if bw_total > 0 else 0

        df_resultado.append({
            "Sequência": sequencia_formatada,
            "Cor Esperada": "RW",
            "Total Tentativas": rw_total,
            "Acertos Diretos": dados["RW_Acerto_Direto"],
            "Acertos Gale 1": dados["RW_Acerto_Gale"],
            "Erros": dados["RW_Erros"],
            "Percentual Acertos": rw_percentual
        })

        df_resultado.append({
            "Sequência": sequencia_formatada,
            "Cor Esperada": "BW",
            "Total Tentativas": bw_total,
            "Acertos Diretos": dados["BW_Acerto_Direto"],
            "Acertos Gale 1": dados["BW_Acerto_Gale"],
            "Erros": dados["BW_Erros"],
            "Percentual Acertos": bw_percentual
        })

    df_resultado = pd.DataFrame(df_resultado)

    # Formatar planilha
    with pd.ExcelWriter(resultado_path, engine='xlsxwriter') as writer:
        df_resultado.to_excel(writer, index=False, sheet_name="Análise")

        workbook = writer.book
        worksheet = writer.sheets["Análise"]

        # Aplicar formatação
        formato = workbook.add_format({'bold': True, 'border': 1, 'align': 'center'})
        for col_num, value in enumerate(df_resultado.columns.values):
            worksheet.write(0, col_num, value, formato)

        worksheet.set_column(0, len(df_resultado.columns) - 1, 15)

    print(f"Resultado salvo em: {resultado_path}")

def main():
    while True:
        lista_cores = ler_lista_cores()
        
        if not lista_cores:
            print("Não foi possível carregar os dados da planilha.")
            return

        comprimento_sequencia = int(input("Digite o comprimento da sequência desejada: "))

        padroes = analisar_padroes(lista_cores, comprimento_sequencia)

        if padroes:
            salvar_resultado(padroes, comprimento_sequencia)
            print("Análise concluída! Verifique a planilha de padrões.")
        else:
            print("Nenhum padrão encontrado.")

        # 🔹 Perguntar se deseja rodar novamente
        while True:
            repetir = input("\nDeseja rodar novamente? (s/n): ").strip().lower()
            if repetir in ['s', 'n']:
                break
            print("Opção inválida! Digite 's' para sim ou 'n' para não.")

        if repetir == 'n':
            print("Finalizando o programa...")
            break

if __name__ == "__main__":
    main()
