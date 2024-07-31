import os
import re

# Definindo o caminho do arquivo de texto no desktop
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
file_name = "historico_do_dia.txt"
file_path = os.path.join(desktop_path, file_name)


# Função para extrair a cor de uma linha
def extrair_cor(linha):
    cor_regex = re.compile(r"Cor atual: (\w+)")
    match = cor_regex.search(linha)
    if match:
        return match.group(1)
    return None


# Função para contar os acertos e erros no martingale após um erro
def contar_acertos_erros(file_path):
    with open(file_path, 'r') as file:
        linhas = file.readlines()

    # Inicializando contadores e dicionários de cores
    acerto_direto = 0
    erro_direto = 0
    acertos_apos_erro = 0
    erros_apos_erro = 0
    erro_encontrado = False
    cores_acerto_direto = {}
    cores_erro_direto = {}
    cores_acertos_martingale = {}
    cores_erros_martingale = {}

    # Iterando pelas linhas do arquivo
    for linha in linhas:
        cor = extrair_cor(linha)  # Definindo a cor antes de usar
        if "Acerto !!" in linha:
            acerto_direto += 1
            if cor:
                cores_acerto_direto[cor] = cores_acerto_direto.get(cor, 0) + 1
        elif "Erro !!" in linha:
            erro_direto += 1
            erro_encontrado = True
            cor = extrair_cor(linha)
            if cor:
                cores_erro_direto[cor] = cores_erro_direto.get(cor, 0) + 1
        elif erro_encontrado:
            if "Acerto no Martingale !!" in linha:
                acertos_apos_erro += 1
                erro_encontrado = False
                cor = extrair_cor(linha)
                if cor:
                    cores_acertos_martingale[cor] = cores_acertos_martingale.get(
                        cor, 0) + 1
            elif "Erro no Martingale !!" in linha:
                erros_apos_erro += 1
                erro_encontrado = False
                cor = extrair_cor(linha)
                if cor:
                    cores_erros_martingale[cor] = cores_erros_martingale.get(
                        cor, 0) + 1
        elif "Acerto no Martingale !!" in linha and "Cor atual:" in linha:
            acertos_apos_erro += 1
            cor = extrair_cor(linha)
            if cor:
                cores_acertos_martingale[cor] = cores_acertos_martingale.get(
                    cor, 0) + 1
        elif "Erro no Martingale !!" in linha and "Cor atual:" in linha:
            erros_apos_erro += 1
            cor = extrair_cor(linha)
            if cor:
                cores_erros_martingale[cor] = cores_erros_martingale.get(
                    cor, 0) + 1

    return (acertos_apos_erro, erros_apos_erro,
            erro_direto, acerto_direto,
            cores_acerto_direto, cores_erro_direto,
            cores_acertos_martingale, cores_erros_martingale)


# Chamando a função para contar os acertos e erros
(acertos, erros, erro, acerto,
 cores_acerto_direto, cores_erro_direto,
 cores_acertos_martingale, cores_erros_martingale) = contar_acertos_erros(file_path)

# Exibindo os resultados
print("Número de acertos diretos:", acerto)
print("Cores dos acertos diretos:", ", ".join(
    f"{cor}: {qtd}" for cor, qtd in cores_acerto_direto.items()))
print("Número de erros diretos:", erro)
print("Cores dos erros diretos:", ", ".join(
    f"{cor}: {qtd}" for cor, qtd in cores_erro_direto.items()))
print("Número de acertos no martingale após um erro:", acertos)
print("Cores dos acertos no martingale após um erro:", ", ".join(
    f"{cor}: {qtd}" for cor, qtd in cores_acertos_martingale.items()))
print("Número de erros no martingale após um erro:", erros)
print("Cores dos erros no martingale após um erro:", ", ".join(
    f"{cor}: {qtd}" for cor, qtd in cores_erros_martingale.items()))
