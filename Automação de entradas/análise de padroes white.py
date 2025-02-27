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
    """Analisa a frequência dos padrões e os acertos diretos e Gale 1 para white."""
    padroes = defaultdict(lambda: {
        "Total": 0,
        "White_Acerto_Direto": 0, 
        "White_Acerto_Gale": 0, 
        "White_Erros": 0
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

        # Analisando apenas a cor "white"
        if proxima_cor == 'white':
            padroes[sequencia]["White_Acerto_Direto"] += 1
        elif segunda_cor == 'white':
            padroes[sequencia]["White_Acerto_Gale"] += 1
        else:
            padroes[sequencia]["White_Erros"] += 1

    return padroes

def salvar_resultado(padroes, tamanho_sequencia):
    """Salva o resultado da análise em uma planilha Excel."""
    desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop', 'Resultados padroes white')
    resultado_path = os.path.join(desktop_path, f'Analise white {tamanho_sequencia}.xlsx')

    df_resultado = []

    for padrao, dados in padroes.items():
        sequencia_formatada = " → ".join(padrao)

        total = dados["Total"]
        acertos = dados["White_Acerto_Direto"] + dados["White_Acerto_Gale"]
        percentual_acertos = round((acertos / total * 100), 1) if total > 0 else 0

        df_resultado.append({
            "Sequência": sequencia_formatada,
            "Cor Esperada": "White",
            "Total Tentativas": total,
            "Acertos Diretos": dados["White_Acerto_Direto"],
            "Acertos Gale 1": dados["White_Acerto_Gale"],
            "Erros": dados["White_Erros"],
            "Percentual Acertos": percentual_acertos
        })

    df_resultado = pd.DataFrame(df_resultado)

    # Formatar planilha
    with pd.ExcelWriter(resultado_path, engine='xlsxwriter') as writer:
        df_resultado.to_excel(writer, index=False, sheet_name="Análise White")

        workbook = writer.book
        worksheet = writer.sheets["Análise White"]

        # Aplicar formatação
        formato = workbook.add_format({'bold': True, 'border': 1, 'align': 'center'})
        for col_num, value in enumerate(df_resultado.columns.values):
            worksheet.write(0, col_num, value, formato)

        worksheet.set_column(0, len(df_resultado.columns) - 1, 15)

    print(f"Resultado salvo em: {resultado_path}")

def main():
    print("Carregando dados da planilha...")
    lista_cores = ler_lista_cores()

    if not lista_cores:
        print("Não foi possível carregar os dados da planilha.")
        return

    while True:
        try:
            comprimento_sequencia = int(input("\nDigite o comprimento da sequência desejada (ou 0 para sair): "))
            
            if comprimento_sequencia == 0:
                print("Finalizando o programa...")
                break

            padroes = analisar_padroes(lista_cores, comprimento_sequencia)

            if padroes:
                salvar_resultado(padroes, comprimento_sequencia)
                print("Análise concluída! Verifique a planilha de padrões.")
            else:
                print("Nenhum padrão encontrado.")
        
        except ValueError:
            print("Erro: Digite um número válido.")

if __name__ == "__main__":
    main()
