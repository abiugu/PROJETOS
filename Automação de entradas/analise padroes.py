import re
import os
import pandas as pd

# Função para analisar o histórico e contar acertos, acertos gale, erros e totais de padrões
def analisar_historico(historico):
    # Definição dos padrões e cores esperadas
    padroes = {
    "padrao 1": (["black", "red", "white", "black"], ["black", "white"]),
    "padrao 2": (["red", "black", "white", "red"], ["red", "white"]),
    "padrao 3": (["white", "red", "black"], ["black", "white"]),
    "padrao 4": (["white", "black", "red"], ["red", "white"]),
    "padrao 5": (["white", "white", "black"], ["red", "white"]),
    "padrao 6": (["white", "white", "red"], ["black", "white"]),
    "padrao 7": (["black", "black", "white", "red", "black"], ["black", "white"]),
    "padrao 8": (["red", "red", "white", "black", "red"], ["red", "white"]),
    "padrao 9": (["black", "red", "black", "red", "black", "black", "red"], ["red", "white"]),
    "padrao 10": (["red", "black", "red", "black", "red", "red", "black"], ["black", "white"]),
    "padrao 11": (["black", "white", "white"], ["black", "white"]),
    "padrao 12": (["red", "white", "white"], ["red", "white"]),
    "padrao 13": (["black", "black", "white", "red", "black", "black"], ["black", "white"]),
    "padrao 14": (["red", "red", "white", "black", "red", "red"], ["red", "white"]),
    "padrao 15": (["black", "red", "white", "black", "red"], ["red", "white"]),
    "padrao 16": (["red", "black", "black", "white"], ["black", "white"]),
    "padrao 17": (["white", "black", "black", "red"], ["black", "white"]),
    "padrao 18": (["black", "white", "red", "white", "black"], ["black", "white"]),
    "padrao 19": (["red", "red", "black", "white"], ["red", "white"]),
    "padrao 20": (["black", "white", "black", "red"], ["red", "white"]),
    "padrao 21": (["black", "red", "red", "white", "white", "black"], ["white", "red"]),
    "padrao 22": (["black", "black", "white", "white", "black", "red"], ["white", "black"]),
    "padrao 23": (["black", "white", "black"], ["white", "black"]),
    "padrao 24": (["red", "white", "black", "red"], ["white", "red"]),
    "padrao 25": (["black", "white", "red", "red", "black"], ["white", "black"]),
    "padrao 26": (["white", "red", "black", "black"], ["white", "black"]),
    "padrao 27": (["white", "black", "white"], ["white", "black"]),
    "padrao 28": (["white", "white", "red", "red", "black"], ["white", "red"]),
    "padrao 29": (["black", "white", "black", "red", "black"], ["white", "black"]),
    "padrao 30": (["red", "white", "black"], ["white", "red"]),
    "padrao 31": (["white", "white", "red"], ["white", "red"]),
    "padrao 32": (["white", "black", "white", "black"], ["white", "black"]),
    "padrao 33": (["white", "red", "black"], ["white", "black"]),
    "padrao 34": (["black", "black", "black"], ["white", "black"]),
    "padrao 35": (["red", "white", "red", "black", "red"], ["white", "red"]),
    "padrao 36": (["white", "black", "red", "white", "white"], ["white", "red"]),
    "padrao 37": (["black", "red", "black"], ["white", "red"]),
    "padrao 38": (["red", "black", "white"], ["white", "black"]),
    "padrao 39": (["white", "red", "red", "black"], ["white", "black"]),
    "padrao 40": (["red", "red", "red"], ["white", "red"]),
    "padrao 41": (["black", "black", "white", "white", "red", "black"], ["white", "black"]),
    "padrao 42": (["black", "white", "white", "red"], ["white", "red"]),
    "padrao 43": (["white", "black", "white", "red", "white", "white"], ["white", "red"]),
    "padrao 44": (["red", "black", "white", "white"], ["white", "red"]),
    "padrao 45": (["white", "red", "white", "black"], ["white", "black"]),
    "padrao 46": (["black", "red", "black", "black"], ["white", "black"]),
    "padrao 47": (["red", "black", "black"], ["white", "black"]),
    "padrao 48": (["red", "white", "red", "red", "red"], ["white", "red"]),
    "padrao 49": (["red", "red", "white", "white", "black", "black"], ["white", "black"]),
    "padrao 50": (["black", "black", "red", "white", "white", "red"], ["white", "black"]),
    "padrao 51": (["black", "white", "white", "red", "black"], ["white", "black"]),
    "padrao 52": (["black", "black", "black", "white", "red"], ["white", "black"]),
    "padrao 53": (["white", "red", "white", "black", "black"], ["white", "black"]),
    "padrao 54": (["black", "black", "black", "black", "black"], ["white", "black"]),
    "padrao 55": (["white", "red", "white", "white", "red", "black"], ["white", "red"]),
    "padrao 56": (["white", "red", "black", "red"], ["white", "black"]),
    "padrao 57": (["red", "black", "white", "red", "red", "red"], ["white", "red"]),
    "padrao 58": (["white", "red", "red", "black", "white"], ["white", "red"]),
    "padrao 59": (["black", "red", "black", "black", "red", "white"], ["white", "black"]),
    "padrao 60": (["black", "red", "white", "white", "red"], ["white", "black"]),
    "padrao 61": (["red", "red", "black", "white", "white"], ["white", "red"]),
    "padrao 62": (["white", "white", "black", "white", "black"], ["white", "black"]),
    "padrao 63": (["red", "red", "red", "black", "black", "black"], ["white", "red"]),
    "padrao 64": (["black", "white", "black", "white"], ["white", "black"]),
    "padrao 65": (["red", "white", "white", "red"], ["white", "red"]),
    "padrao 66": (["red", "white", "black", "red", "red"], ["white", "red"]),
    "padrao 67": (["red", "red", "white"], ["white", "red"]),
    "padrao 68": (["black", "red", "red", "red", "white"], ["white", "red"]),
    "padrao 69": (["white", "black", "red", "red", "red", "black"], ["white", "black"]),
    "padrao 70": (["black", "red", "red", "white", "black", "black"], ["white", "black"])
}

    
    # Contadores de acertos, acertos gale, erros e totais de padrões
    resultados = {padrao: {"acertos": 0, "acertos_gale": 0, "erros": 0, "total": 0, "max_acertos_consecutivos": 0, "max_erros_consecutivos": 0} for padrao in padroes}
    log_padroes = []  # Para armazenar informações sobre as ocorrências dos padrões
    
    # Variáveis para contar acertos e erros consecutivos para cada padrão
    acertos_consecutivos = {padrao: 0 for padrao in padroes}
    erros_consecutivos = {padrao: 0 for padrao in padroes}
    
    # Processar o histórico de jogadas, extraindo a primeira cor de cada linha
    linhas = historico.strip().split("\n")
    sequencias = [re.findall(r"(red|black|white)", linha)[0] for linha in linhas if re.findall(r"(red|black|white)", linha)]
    
    # Iteração sobre a sequência de cores para detectar padrões e próximas jogadas
    for i in range(len(sequencias)):
        for padrao, (sequencia_padrao, cores_esperadas) in padroes.items():
            len_padrao = len(sequencia_padrao)
            
            # Verifica se o padrão cabe na posição atual e as próximas jogadas existem
            if i + len_padrao < len(sequencias):
                atual_sequencia = sequencias[i:i + len_padrao]
                proximas_jogadas = sequencias[i + len_padrao:i + len_padrao + 2]
                
                # Verifica correspondência com o padrão atual
                if atual_sequencia == sequencia_padrao:
                    resultados[padrao]["total"] += 1  # Conta o total de vezes que o padrão foi visto
                    linha_info = f"Linha {i+1} - {padrao} encontrado: {atual_sequencia} | Próximas: {proximas_jogadas} -> "
                    
                    # Verifica acertos e erros
                    if proximas_jogadas and proximas_jogadas[0] in cores_esperadas:
                        resultados[padrao]["acertos"] += 1
                        acertos_consecutivos[padrao] += 1
                        erros_consecutivos[padrao] = 0
                        linha_info += "Acerto"
                    elif len(proximas_jogadas) > 1 and proximas_jogadas[1] in cores_esperadas:
                        resultados[padrao]["acertos_gale"] += 1
                        acertos_consecutivos[padrao] += 1
                        erros_consecutivos[padrao] = 0
                        linha_info += "Acerto Gale"
                    else:
                        resultados[padrao]["erros"] += 1
                        erros_consecutivos[padrao] += 1
                        acertos_consecutivos[padrao] = 0
                        linha_info += "Erro"
                    
                    # Armazena a informação no log de padrões
                    log_padroes.append(linha_info)
                    
                    # Atualiza os máximos para cada padrão
                    resultados[padrao]["max_acertos_consecutivos"] = max(resultados[padrao]["max_acertos_consecutivos"], acertos_consecutivos[padrao])
                    resultados[padrao]["max_erros_consecutivos"] = max(resultados[padrao]["max_erros_consecutivos"], erros_consecutivos[padrao])
    
    return resultados, log_padroes

# Caminhos para a área de trabalho e o log
desktop_path = os.path.join(os.path.expanduser("~"), 'Desktop')
logs_path = os.path.join(desktop_path, "LOGS")
log_file_path = os.path.join(logs_path, "log 36.txt")
log_padroes_path = os.path.join(desktop_path, "log_padroes_encontrados.txt")
planilha_path = os.path.join(desktop_path, "resultados_padroes.xlsx")

# Leitura do arquivo de histórico
with open(log_file_path, "r") as arquivo:
    historico = arquivo.read()

# Análise do histórico
resultados, log_padroes = analisar_historico(historico)

# Salva o log detalhado dos padrões encontrados
with open(log_padroes_path, "w") as log_padroes_file:
    for linha in log_padroes:
        log_padroes_file.write(linha + "\n")

# Criação de uma lista de dicionários para facilitar a conversão em DataFrame
dados_padroes = []
for padrao, resultado in resultados.items():
    total_tentativas = resultado["acertos"] + resultado["acertos_gale"] + resultado["erros"]
    percentual_acerto = (resultado["acertos"] / total_tentativas * 100) if total_tentativas > 0 else 0
    percentual_acerto_gale = (resultado["acertos_gale"] / total_tentativas * 100) if total_tentativas > 0 else 0
    percentual_erro = (resultado["erros"] / total_tentativas * 100) if total_tentativas > 0 else 0

    dados_padroes.append({
        "Padrão": padrao,
        "Total": resultado["total"],
        "Acertos": resultado["acertos"],
        "Acertos Gale": resultado["acertos_gale"],
        "Erros": resultado["erros"],
        "Percentual Acerto (%)": percentual_acerto,
        "Percentual Acerto Gale (%)": percentual_acerto_gale,
        "Percentual Erro (%)": percentual_erro,
        "Máximo de Acertos Consecutivos": resultado["max_acertos_consecutivos"],
        "Máximo de Erros Consecutivos": resultado["max_erros_consecutivos"]
    })

# Criação do DataFrame e salvamento em uma planilha Excel
df = pd.DataFrame(dados_padroes)
df.to_excel(planilha_path, index=False)

# Exibir resultados gerais para cada padrão
print("\nResultados dos Padroes:")
for padrao, resultado in resultados.items():
    total_tentativas = resultado["acertos"] + resultado["acertos_gale"] + resultado["erros"]
    percentual_acerto = (resultado["acertos"] / total_tentativas * 100) if total_tentativas > 0 else 0
    percentual_acerto_gale = (resultado["acertos_gale"] / total_tentativas * 100) if total_tentativas > 0 else 0
    percentual_erro = (resultado["erros"] / total_tentativas * 100) if total_tentativas > 0 else 0
    
    print(f"{padrao} - Total: {resultado['total']}, Acertos: {resultado['acertos']} ({percentual_acerto:.2f}%), "
          f"Acertos Gale: {resultado['acertos_gale']} ({percentual_acerto_gale:.2f}%), Erros: {resultado['erros']} "
          f"({percentual_erro:.2f}%), Maximo de Acertos Consecutivos: {resultado['max_acertos_consecutivos']}, "
          f"Maximo de Erros Consecutivos: {resultado['max_erros_consecutivos']}")

print(f"\nLog detalhado salvo em {log_padroes_path}")
print(f"Resultados salvos em {planilha_path}")
