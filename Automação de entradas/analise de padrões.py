import itertools
import re
import os
import pandas as pd


def obter_comprimento_sequencia():
    """Solicita ao usuário o comprimento da sequência e retorna um inteiro."""
    try:
        comprimento = int(input("Digite o comprimento da sequência (número inteiro): "))
        print(f"Comprimento escolhido: {comprimento}")
        return comprimento
    except ValueError:
        print("Entrada inválida. Usando comprimento padrão: 8")
        return 8


def gerar_combinacoes_possiveis(comprimento):
    """Gera todas as combinações possíveis de cores para um determinado comprimento (black, red, white)."""
    cores = ["black", "red", "white"]  # Agora temos black, red e white
    combinacoes = list(itertools.product(cores, repeat=comprimento))
    padroes = {}
    
    for i, combinacao in enumerate(combinacoes):
        # A cor esperada será black ou red, e white será apenas proteção
        cor_esperada = "black" if i % 2 == 0 else "red"  # Alterna entre black e red
        padroes[f"sequencia_{i}"] = {
            "sequencia": list(combinacao),
            "cor_esperada": cor_esperada,
        }
    return padroes


def analisar_historico(historico, padroes):
    """Analisa o histórico de jogadas e verifica acertos, erros e acertos por gale."""
    # Inicializa os resultados
    resultados = {
        padrao: {
            "acertos": 0,
            "acertos_gale1": 0,
            "acertos_gale2": 0,
            "erros": 0,
            "total": 0,
        }
        for padrao in padroes
    }

    log_padroes = []  # Para armazenar o log detalhado
    linhas = historico.strip().split("\n")
    sequencias = [
        re.search(r"Cor: (white|black|red)", linha).group(1)
        for linha in linhas if re.search(r"Cor: (white|black|red)", linha)
    ]

    # Iterar pelas sequências do histórico
    for i in range(len(sequencias)):
        for padrao, dados in padroes.items():
            sequencia_padrao = dados["sequencia"]
            cor_esperada = dados["cor_esperada"]
            len_padrao = len(sequencia_padrao)

            # Verifica se a sequência atual corresponde ao padrão
            if i + len_padrao < len(sequencias):
                atual_sequencia = sequencias[i:i + len_padrao]
                proximas_jogadas = sequencias[i + len_padrao:i + len_padrao + 3]

                if atual_sequencia == sequencia_padrao:
                    resultados[padrao]["total"] += 1
                    log_info = (
                        f"Linha {i+1}: Padrão {padrao} encontrado -> "
                        f"Sequência: {atual_sequencia} | Próximas: {proximas_jogadas} -> "
                    )

                    # Verifica acertos diretos ou por gales
                    if proximas_jogadas and proximas_jogadas[0] in [cor_esperada, "white"]:
                        resultados[padrao]["acertos"] += 1
                        log_info += f"Acerto Direto (Cor Esperada: {cor_esperada}, Aceito: {proximas_jogadas[0]})"
                    elif len(proximas_jogadas) > 1 and proximas_jogadas[1] in [cor_esperada, "white"]:
                        resultados[padrao]["acertos_gale1"] += 1
                        log_info += f"Acerto Gale 1 (Cor Esperada: {cor_esperada}, Aceito: {proximas_jogadas[1]})"
                    elif len(proximas_jogadas) > 2 and proximas_jogadas[2] in [cor_esperada, "white"]:
                        resultados[padrao]["acertos_gale2"] += 1
                        log_info += f"Acerto Gale 2 (Cor Esperada: {cor_esperada}, Aceito: {proximas_jogadas[2]})"
                    else:
                        resultados[padrao]["erros"] += 1
                        log_info += f"Erro (Cor Esperada: {cor_esperada})"

                    log_padroes.append(log_info)

    return resultados, log_padroes


def salvar_resultados_excel(resultados, padroes, caminho):
    """Salva os resultados em uma planilha Excel."""
    dados_padroes = [
        {
            "Padrão": padrao,
            "Sequência": " ".join(padroes[padrao]["sequencia"]),
            "Cor Esperada": padroes[padrao]["cor_esperada"],
            "Total Tentativas": resultado["total"],
            "Acertos Diretos": resultado["acertos"],
            "Acertos Gale 1": resultado["acertos_gale1"],
            "Acertos Gale 2": resultado["acertos_gale2"],
            "Erros": resultado["erros"],
            "Percentual de Acertos (%)": (
                (resultado["acertos"] + resultado["acertos_gale1"] + resultado["acertos_gale2"]) / resultado["total"] * 100
                if resultado["total"] > 0 else 0
            ),
        }
        for padrao, resultado in resultados.items()
    ]
    df = pd.DataFrame(dados_padroes)
    df.to_excel(caminho, index=False)
    print(f"Resultados salvos em {caminho}")


def salvar_log_detalhado(log_padroes, caminho):
    """Salva o log detalhado de padrões encontrados em um arquivo de texto."""
    with open(caminho, "w") as log_file:
        for linha in log_padroes:
            log_file.write(linha + "\n")
    print(f"Log detalhado salvo em {caminho}")


# Main
if __name__ == "__main__":
    # Obtém o comprimento da sequência
    comprimento_sequencia = obter_comprimento_sequencia()

    # Gera todas as combinações possíveis de padrões
    padroes = gerar_combinacoes_possiveis(comprimento_sequencia)

    # Caminhos dos arquivos
    desktop_path = os.path.join(os.path.expanduser("~"), 'Desktop')
    logs_path = os.path.join(desktop_path, "LOGS")
    log_file_path = os.path.join(logs_path, "resultados_double2.txt")
    planilha_path = os.path.join(desktop_path, f"resultados_padroes_{comprimento_sequencia}.xlsx")
    log_detalhado_path = os.path.join(desktop_path, f"log_padroes_{comprimento_sequencia}.txt")

    # Leitura do histórico de jogadas
    with open(log_file_path, "r") as arquivo:
        historico = arquivo.read()

    # Analisa o histórico e obtém os resultados e o log
    resultados, log_padroes = analisar_historico(historico, padroes)

    # Salva os resultados em uma planilha Excel
    salvar_resultados_excel(resultados, padroes, planilha_path)

    # Salva o log detalhado
    salvar_log_detalhado(log_padroes, log_detalhado_path)

    print("\nAnálise concluída com sucesso!")
