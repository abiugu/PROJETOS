import os

# Função para comparar as porcentagens entre as cores


def comparar_porcentagens(cor_atual, cor_oposta, porcentagens_atual, porcentagens_oposta):
    if cor_atual == "red":
        red_atual = porcentagens_atual[2]
        red_oposta = porcentagens_oposta[1]  # Correção aqui
        if red_atual > red_oposta:
            return ">"
        elif red_atual < red_oposta:
            return "<"
        else:
            return "="
    elif cor_atual == "black":
        black_atual = porcentagens_atual[1]
        black_oposta = porcentagens_oposta[2]
        if black_atual > black_oposta:
            return ">"
        elif black_atual < black_oposta:
            return "<"
        else:
            return "="
    else:  # Cor atual é white
        white_atual = porcentagens_atual[0]
        white_oposta = porcentagens_oposta[2]
        if white_atual > white_oposta:
            return ">"
        elif white_atual < white_oposta:
            return "<"
        else:
            return "="

# Função para identificar os alarmes e suas informações relevantes


def identificar_alarmes(arquivo):
    alarmes = []
    black_count = 0  # Contador para alarmes "black"
    red_count = 0   # Contador para alarmes "red"
    with open(arquivo, 'r') as file:
        info = {}
        for linha in file:
            if "Ultimos 3 resultados:" in linha:
                cores = linha.split(":")[1].strip().split(", ")
                cor_atual = cores[0]
                info["cor"] = cor_atual
            elif "Ultimas 25 porcentagens:" in linha:
                info["comp_25"] = [float(p)
                                   for p in linha.split(":")[1].split(", ")]
            elif "Ultimas 50 porcentagens:" in linha:
                info["comp_50"] = [float(p)
                                   for p in linha.split(":")[1].split(", ")]
            elif "Ultimas 100 porcentagens:" in linha:
                info["comp_100"] = [float(p)
                                    for p in linha.split(":")[1].split(", ")]
            elif "Ultimas 500 porcentagens:" in linha:
                info["comp_500"] = [float(p)
                                    for p in linha.split(":")[1].split(", ")]
            elif "Alarme acionado" in linha:
                try:
                    info["alarme"] = int(linha.split(":")[1])
                    if info["cor"] == "black":
                        black_count += 1
                    elif info["cor"] == "red":
                        red_count += 1
                    alarmes.append(info.copy())
                    info.clear()
                except IndexError:
                    # Ignorar linhas que não estão no formato esperado
                    pass
    return alarmes, black_count, red_count


# Diretório onde estão os arquivos
diretorio_logs = os.path.join(os.path.expanduser("~"), "Desktop", "LOGS")

# Arquivo a ser lido
arquivo_entrada = os.path.join(
    diretorio_logs, "acertos", "acertos_branco 100 mod.txt")
# Arquivo de saída
arquivo_saida = os.path.join(
    diretorio_logs, 'resultados', "resultados_acertos_branco_100 direto mod.txt")

# Identificar alarmes e contar quantos black e quantos red
alarmes, black_count, red_count = identificar_alarmes(arquivo_entrada)

# Função para imprimir os resultados e contar as ocorrências


def imprimir_resultados(alarmes, black_count, red_count):
    contagem = {"25": {"<": 0, "=": 0, ">": 0},
                "50": {"<": 0, "=": 0, ">": 0},
                "100": {"<": 0, "=": 0, ">": 0},
                "500": {"<": 0, "=": 0, ">": 0}}
    possibilidades = {}
    with open(arquivo_saida, 'w') as file:
        for info in alarmes:
            cor_atual = info["cor"]
            cor_oposta = "red" if cor_atual == "black" else "black"
            sequencia = ""
            file.write("Ultimos 3 resultados: {}, {}, {}\n".format(
                cor_atual, cor_atual, cor_atual))
            file.write("Ultimas 25 porcentagens: {}\n".format(
                ", ".join(map(str, info["comp_25"]))))
            file.write("Ultimas 50 porcentagens: {}\n".format(
                ", ".join(map(str, info["comp_50"]))))
            file.write("Ultimas 100 porcentagens: {}\n".format(
                ", ".join(map(str, info["comp_100"]))))
            file.write("Ultimas 500 porcentagens: {}\n".format(
                ", ".join(map(str, info["comp_500"]))))
            for rodadas in ["25", "50", "100", "500"]:
                comp = comparar_porcentagens(cor_atual, cor_oposta, info.get(
                    "comp_" + rodadas, [0, 0, 0]), info.get("comp_" + rodadas, [0, 0, 0]))
                file.write("Percentual {} rodadas: {}\n".format(rodadas, comp))
                contagem[rodadas][comp] += 1
                # Construindo a sequência de contagem
                sequencia += comp
            if sequencia in possibilidades:
                possibilidades[sequencia] += 1
            else:
                possibilidades[sequencia] = 1

        file.write("\nContagem:\n")
        file.write("Black: {}\n".format(black_count))
        file.write("Red: {}\n".format(red_count))

        file.write("\nContagem dos sinais:\n")
        for rodadas in ["25", "50", "100", "500"]:
            file.write("Percentual {} rodadas\n".format(rodadas))
            for sinal in ["<", "=", ">"]:
                file.write("Sinal {}: {}\n".format(
                    sinal, contagem[rodadas][sinal]))
            file.write("\n")

        file.write("\nPossibilidades:\n")
        for seq, count in sorted(possibilidades.items(), key=lambda x: x[1], reverse=True):
            # Convertendo seq para uma lista de inteiros
            file.write("Sequencia: {}\n".format(", ".join(seq)))
            file.write("Quantidade: {}\n".format(count))
            file.write("\n")


# Imprimir resultados
imprimir_resultados(alarmes, black_count, red_count)
print("Informaçoes extraidas com sucesso!")
