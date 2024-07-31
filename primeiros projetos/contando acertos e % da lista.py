import os

desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
log_file_path = os.path.join(desktop_path, "historico total.txt")

def ler_arquivo():
    with open(log_file_path, "r") as file:
        linhas = file.readlines()
    return linhas

def calcular_acertos_erros(linhas):
    acertos_martingale_XouMenos = acertos_martingale_maisDeX = acertos_martingale_XouMenos_oposta = acertos_martingale_maisDeX_oposta = erros_martingale_XouMenos_oposta = erros_martingale_maisDeX_oposta = erros_martingale_XouMenos_mesmaCor = erros_martingale_maisDeX_mesmaCor = total_acertos_martingale = total_erros_martingale = 0

    index = 0
    while index < len(linhas):
        line = linhas[index].strip()
        if "Acerto no Martingale !! Cor atual:" in line:
            total_acertos_martingale += 1
            cor_atual = line.split(":")[-1].strip()
            index += 1
            porcentagens = linhas[index].split("Ultimas 25 rodadas:")[-1].replace("[", "").replace("]", "").split(", ")
            if cor_atual in {"black", "red"}:
                try:
                    porcentagem_cor_atual = int(''.join(filter(str.isdigit, porcentagens[["white", "black", "red"].index(cor_atual)].replace("%", "").strip())))
                except ValueError:
                    porcentagem_cor_atual = 0
                
                if porcentagem_cor_atual <= 42:
                    acertos_martingale_XouMenos += 1
                else:
                    acertos_martingale_maisDeX += 1
                
                cor_oposta = {"black": "red", "red": "black"}[cor_atual]
                if cor_oposta in {"black", "red"}:
                    try:
                        porcentagem_cor_oposta = int(''.join(filter(str.isdigit, porcentagens[["white", "black", "red"].index(cor_oposta)].replace("%", "").strip())))
                    except ValueError:
                        porcentagem_cor_oposta = 0

                    if porcentagem_cor_oposta <= 42:
                        acertos_martingale_XouMenos_oposta += 1
                    else:
                        acertos_martingale_maisDeX_oposta += 1
                    
        elif "Erro no Martingale !! Cor atual:" in line:
            total_erros_martingale += 1
            cor_atual = line.split(":")[-1].strip()
            index += 1
            porcentagens = linhas[index].split("Ultimas 25 rodadas:")[-1].replace("[", "").replace("]", "").split(", ")
            if cor_atual in {"black", "red"}:
                try:
                    porcentagem_cor_atual = int(''.join(filter(str.isdigit, porcentagens[["white", "black", "red"].index(cor_atual)].replace("%", "").strip())))
                except ValueError:
                    porcentagem_cor_atual = 0

                cor_oposta = {"black": "red", "red": "black"}[cor_atual]
                if cor_oposta in {"black", "red"}:
                    try:
                        porcentagem_cor_oposta = int(''.join(filter(str.isdigit, porcentagens[["white", "black", "red"].index(cor_oposta)].replace("%", "").strip())))
                    except ValueError:
                        porcentagem_cor_oposta = 0

                    if porcentagem_cor_oposta <= 42:
                        erros_martingale_XouMenos_oposta += 1
                    else:
                        erros_martingale_maisDeX_oposta += 1
                    if porcentagem_cor_atual <= 42:
                        erros_martingale_XouMenos_mesmaCor += 1
                    else:
                        erros_martingale_maisDeX_mesmaCor += 1
        index += 1

    return (acertos_martingale_XouMenos, acertos_martingale_maisDeX, acertos_martingale_XouMenos_oposta, acertos_martingale_maisDeX_oposta, erros_martingale_XouMenos_oposta, erros_martingale_maisDeX_oposta, erros_martingale_XouMenos_mesmaCor, erros_martingale_maisDeX_mesmaCor, total_acertos_martingale, total_erros_martingale)

def main():
    linhas = ler_arquivo()
    (
        acertos_martingale_XouMenos,
        acertos_martingale_maisDeX,
        acertos_martingale_XouMenos_oposta,
        acertos_martingale_maisDeX_oposta,
        erros_martingale_XouMenos_oposta,
        erros_martingale_maisDeX_oposta,
        erros_martingale_XouMenos_mesmaCor,
        erros_martingale_maisDeX_mesmaCor,
        total_acertos_martingale,
        total_erros_martingale
    ) = calcular_acertos_erros(linhas)

    porcentagem_acertos_martingale_XouMenos = (acertos_martingale_XouMenos / total_acertos_martingale) * 100 if total_acertos_martingale else 0
    porcentagem_acertos_martingale_maisDeX = (acertos_martingale_maisDeX / total_acertos_martingale) * 100 if total_acertos_martingale else 0
    porcentagem_acertos_martingale_XouMenos_oposta = (acertos_martingale_XouMenos_oposta / total_acertos_martingale) * 100 if total_acertos_martingale else 0
    porcentagem_acertos_martingale_maisDeX_oposta = (acertos_martingale_maisDeX_oposta / total_acertos_martingale) * 100 if total_acertos_martingale else 0
    porcentagem_erros_martingale_XouMenos_oposta = (erros_martingale_XouMenos_oposta / total_erros_martingale) * 100 if total_erros_martingale else 0
    porcentagem_erros_martingale_maisDeX_oposta = (erros_martingale_maisDeX_oposta / total_erros_martingale) * 100 if total_erros_martingale else 0
    porcentagem_erros_martingale_XouMenos_mesmaCor = (erros_martingale_XouMenos_mesmaCor / total_erros_martingale) * 100 if total_erros_martingale else 0
    porcentagem_erros_martingale_maisDeX_mesmaCor = (erros_martingale_maisDeX_mesmaCor / total_erros_martingale) * 100 if total_erros_martingale else 0

    print("Acertos Martingale com 40% ou menos:", acertos_martingale_XouMenos, f"({porcentagem_acertos_martingale_XouMenos:.2f}%)")
    print("Acertos Martingale com mais de 40%:", acertos_martingale_maisDeX, f"({porcentagem_acertos_martingale_maisDeX:.2f}%)")
    print("*******************Acertos Martingale com 40% ou menos da cor oposta:", acertos_martingale_XouMenos_oposta, f"({porcentagem_acertos_martingale_XouMenos_oposta:.2f}%)")
    print("Acertos Martingale com mais de 40% da cor oposta:", acertos_martingale_maisDeX_oposta, f"({porcentagem_acertos_martingale_maisDeX_oposta:.2f}%)")
    print("Erros Martingale com 40% ou menos da cor oposta:", erros_martingale_XouMenos_oposta, f"({porcentagem_erros_martingale_XouMenos_oposta:.2f}%)")
    print("Erros Martingale com mais de 40% da cor oposta:", erros_martingale_maisDeX_oposta, f"({porcentagem_erros_martingale_maisDeX_oposta:.2f}%)")
    print("*******************Erros Martingale com 40% ou menos da mesma cor:", erros_martingale_XouMenos_mesmaCor, f"({porcentagem_erros_martingale_XouMenos_mesmaCor:.2f}%)")
    print("Erros Martingale com mais de 40% da mesma cor:", erros_martingale_maisDeX_mesmaCor, f"({porcentagem_erros_martingale_maisDeX_mesmaCor:.2f}%)")

if __name__ == "__main__":
    main()


