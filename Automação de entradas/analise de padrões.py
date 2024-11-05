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
    "padrao 70": (["black", "red", "red", "white", "black", "black"], ["white", "black"]),
    "padrao 71": (["white", "red", "white", "black", "red", "white"], ["white", "red"]),
    "padrao 72": (["black", "red", "white", "black", "white"], ["white", "black"]),
    "padrao 73": (["white", "white", "black", "red", "black"], ["white", "black"]),
    "padrao 74": (["red", "white", "red", "black", "black"], ["white", "red"]),
    "padrao 75": (["white", "red", "black", "white", "red", "black"], ["white", "red"]),
    "padrao 76": (["black", "black", "red", "white"], ["white", "black"]),
    "padrao 77": (["white", "black", "red", "black", "white"], ["white", "black"]),
    "padrao 78": (["red", "red", "black", "white", "black"], ["white", "red"]),
    "padrao 79": (["black", "white", "black", "red", "white", "red"], ["white", "black"]),
    "padrao 80": (["white", "black", "red", "white", "red", "black"], ["white", "black"]),
    "padrao 81": (["red", "white", "black", "black", "white"], ["white", "red"]),
    "padrao 82": (["black", "red", "white", "black", "red", "white"], ["white", "black"]),
    "padrao 83": (["white", "black", "white", "red", "black"], ["white", "black"]),
    "padrao 84": (["red", "black", "red", "white", "black"], ["white", "red"]),
    "padrao 85": (["white", "red", "black", "black", "red", "white"], ["white", "red"]),
    "padrao 86": (["black", "white", "red", "black", "red", "white"], ["white", "black"]),
    "padrao 87": (["red", "black", "white", "red", "white"], ["white", "red"]),
    "padrao 88": (["black", "red", "black", "white", "white", "red"], ["white", "black"]),
    "padrao 89": (["white", "white", "red", "black", "white", "black"], ["white", "red"]),
    "padrao 90": (["red", "black", "white", "black", "white", "red"], ["white", "black"]),
    "padrao 91": (["white", "red", "black", "white", "black", "red"], ["white", "red"]),
    "padrao 92": (["black", "white", "red", "black", "white", "black"], ["white", "black"]),
    "padrao 93": (["white", "black", "white", "red", "black", "red"], ["white", "black"]),
    "padrao 94": (["red", "white", "black", "red", "white", "black"], ["white", "red"]),
    "padrao 95": (["black", "black", "white", "red", "black", "white"], ["white", "black"]),
    "padrao 96": (["white", "red", "white", "black", "red", "black"], ["white", "red"]),
    "padrao 97": (["black", "red", "black", "white", "red"], ["white", "black"]),
    "padrao 98": (["red", "white", "black", "white", "red", "black"], ["white", "red"]),
    "padrao 99": (["white", "black", "red", "white", "black"], ["white", "black"]),
    "padrao 100": (["black", "red", "white", "black", "red"], ["white", "red"]),
    "padrao 101": (["red", "white", "red", "black", "white"], ["white", "red"]),
    "padrao 102": (["white", "black", "white", "red", "black"], ["white", "black"]),
    "padrao 103": (["black", "red", "white", "black", "white"], ["white", "black"]),
    "padrao 104": (["white", "red", "black", "red", "black"], ["white", "red"]),
    "padrao 105": (["red", "white", "black", "red", "black"], ["white", "red"]),
    "padrao 106": (["black", "white", "black", "red"], ["white", "black"]),
    "padrao 107": (["white", "red", "black", "black", "red"], ["white", "red"]),
    "padrao 108": (["red", "black", "white", "red"], ["white", "black"]),
    "padrao 109": (["black", "white", "red", "black", "red"], ["white", "black"]),
    "padrao 110": (["white", "black", "white", "red", "black"], ["white", "black"]),
    "padrao 111": (["red", "black", "white", "black"], ["white", "red"]),
    "padrao 112": (["black", "red", "white", "red"], ["white", "black"]),
    "padrao 113": (["white", "black", "red", "white"], ["white", "red"]),
    "padrao 114": (["red", "black", "white", "red"], ["white", "black"]),
    "padrao 115": (["white", "red", "black", "red"], ["white", "red"]),
    "padrao 116": (["black", "white", "black", "red"], ["white", "black"]),
    "padrao 117": (["red", "black", "white", "black"], ["white", "red"]),
    "padrao 118": (["white", "black", "red", "white"], ["white", "black"]),
    "padrao 119": (["red", "white", "black", "red"], ["white", "red"]),
    "padrao 120": (["black", "red", "white", "black"], ["white", "black"]),
    "padrao 121": (["white", "black", "red", "white"], ["white", "red"]),
    "padrao 122": (["red", "white", "black", "red"], ["white", "black"]),
    "padrao 123": (["black", "white", "red", "black"], ["white", "red"]),
    "padrao 124": (["white", "red", "black", "white"], ["white", "black"]),
    "padrao 125": (["red", "black", "white", "red"], ["white", "red"]),
    "padrao 126": (["black", "white", "red", "white"], ["white", "black"]),
    "padrao 127": (["white", "red", "black", "red"], ["white", "black"]),
    "padrao 128": (["red", "black", "white", "black"], ["white", "red"]),
    "padrao 129": (["white", "black", "red", "white"], ["white", "red"]),
    "padrao 130": (["black", "red", "white", "black"], ["white", "black"]),
    "padrao 131": (["red", "black", "white", "red"], ["white", "black"]),
    "padrao 132": (["white", "red", "black", "black"], ["white", "black"]),
    "padrao 133": (["black", "white", "red", "white"], ["white", "red"]),
    "padrao 134": (["red", "white", "black", "red"], ["white", "black"]),
    "padrao 135": (["white", "black", "red", "white"], ["white", "red"]),
    "padrao 136": (["red", "black", "white", "red"], ["white", "black"]),
    "padrao 137": (["black", "red", "white", "black"], ["white", "black"]),
    "padrao 138": (["red", "black", "white", "red"], ["white", "red"]),
    "padrao 139": (["white", "black", "red", "black"], ["white", "black"]),
    "padrao 140": (["black", "red", "white", "white"], ["white", "black"]),
    "padrao 141": (["red", "black", "white", "white"], ["white", "black"]),
    "padrao 142": (["black", "red", "white", "red"], ["white", "red"]),
    "padrao 143": (["white", "black", "red", "black"], ["white", "black"]),
    "padrao 144": (["black", "white", "red", "red"], ["white", "red"]),
    "padrao 145": (["red", "black", "white", "black"], ["white", "red"]),
    "padrao 146": (["white", "red", "black", "black"], ["white", "red"]),
    "padrao 147": (["black", "red", "white", "white"], ["white", "black"]),
    "padrao 148": (["white", "black", "red", "red"], ["white", "red"]),
    "padrao 149": (["black", "white", "red", "black"], ["white", "black"]),
    "padrao 150": (["white", "black", "white", "red"], ["white", "red"]),
    "padrao 151": (["red", "white", "black", "black"], ["white", "red"]),
    "padrao 152": (["black", "red", "white", "black"], ["white", "black"]),
    "padrao 153": (["white", "red", "black", "white"], ["white", "red"]),
    "padrao 154": (["black", "white", "red", "black"], ["white", "black"]),
    "padrao 155": (["red", "black", "white", "red"], ["white", "red"]),
    "padrao 156": (["white", "red", "black", "white"], ["white", "red"]),
    "padrao 157": (["black", "red", "white", "black"], ["white", "black"]),
    "padrao 158": (["white", "black", "red", "red"], ["white", "black"]),
    "padrao 159": (["red", "black", "white", "black"], ["white", "red"]),
    "padrao 160": (["black", "white", "red", "black"], ["white", "red"]),
    "padrao 161": (["white", "red", "black", "black"], ["white", "black"]),
    "padrao 162": (["red", "white", "black", "black"], ["white", "black"]),
    "padrao 163": (["black", "red", "white", "black"], ["white", "black"]),
    "padrao 164": (["white", "black", "red", "red"], ["white", "black"]),
    "padrao 165": (["black", "white", "red", "black"], ["white", "red"]),
    "padrao 166": (["red", "black", "white", "black"], ["white", "red"]),
    "padrao 167": (["white", "red", "black", "black"], ["white", "black"]),
    "padrao 168": (["black", "white", "red", "white"], ["white", "black"]),
    "padrao 169": (["red", "black", "white", "black"], ["white", "red"]),
    "padrao 170": (["white", "red", "black", "white"], ["white", "black"]),
    "padrao 171": (["black", "white", "red", "black"], ["white", "red"]),
    "padrao 172": (["white", "black", "red", "red"], ["white", "black"]),
    "padrao 173": (["red", "white", "black", "white"], ["white", "red"]),
    "padrao 174": (["black", "red", "white", "black"], ["white", "black"]),
    "padrao 175": (["white", "black", "red", "black"], ["white", "black"]),
    "padrao 176": (["black", "red", "white", "black"], ["white", "red"]),
    "padrao 177": (["red", "black", "white", "red"], ["white", "black"]),
    "padrao 178": (["white", "black", "red", "white"], ["white", "red"]),
    "padrao 179": (["black", "red", "white", "red"], ["white", "black"]),
    "padrao 180": (["white", "red", "black", "white"], ["white", "black"]),
    "padrao 181": (["black", "white", "red", "black"], ["white", "red"]),
    "padrao 182": (["red", "black", "white", "red"], ["white", "black"]),
    "padrao 183": (["white", "red", "black", "white"], ["white", "black"]),
    "padrao 184": (["black", "red", "white", "black"], ["white", "black"]),
    "padrao 185": (["red", "black", "white", "black"], ["white", "red"]),
    "padrao 186": (["white", "red", "black", "black"], ["white", "black"]),
    "padrao 187": (["black", "white", "red", "white"], ["white", "red"]),
    "padrao 188": (["red", "white", "black", "black"], ["white", "black"]),
    "padrao 189": (["white", "black", "red", "black"], ["white", "black"]),
    "padrao 190": (["red", "white", "black", "white"], ["white", "red"]),
    "padrao 191": (["black", "red", "white", "red"], ["white", "black"]),
    "padrao 192": (["white", "black", "red", "white"], ["white", "red"]),
    "padrao 193": (["red", "white", "black", "black"], ["white", "black"]),
    "padrao 194": (["white", "red", "black", "red"], ["white", "red"]),
    "padrao 195": (["black", "white", "red", "white"], ["white", "black"]),
    "padrao 196": (["red", "black", "white", "black"], ["white", "red"]),
    "padrao 197": (["white", "red", "black", "white"], ["white", "black"]),
    "padrao 198": (["black", "red", "white", "red"], ["white", "black"]),
    "padrao 199": (["red", "white", "black", "black"], ["white", "red"]),
    "padrao 200": (["white", "black", "red", "white"], ["white", "black"]),

}

    # Contadores de acertos, acertos gale, erros e totais de padrões
    resultados = {padrao: {"acertos": 0, "acertos_gale": 0, "erros": 0, "total": 0, "max_acertos_consecutivos": 0, "max_erros_consecutivos": 0} for padrao in padroes}
    log_padroes = []  # Para armazenar informações sobre as ocorrências dos padrões
    
    # Variáveis para contar acertos e erros consecutivos para cada padrão
    acertos_consecutivos = {padrao: 0 for padrao in padroes}
    erros_consecutivos = {padrao: 0 for padrao in padroes}
    
    # Processar o histórico de jogadas, extraindo a cor de cada linha no novo formato
    linhas = historico.strip().split("\n")
    sequencias = [re.search(r"Cor: (white|black|red)", linha).group(1) for linha in linhas if re.search(r"Cor: (white|black|red)", linha)]
    
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
log_file_path = os.path.join(logs_path, "resultados_double.txt")
log_padroes_path = os.path.join(desktop_path, "log_padroes_encontrados.txt")
planilha_path = os.path.join(desktop_path, "resultados_padroes.xlsx")

# Leitura do arquivo de histórico no novo formato
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
