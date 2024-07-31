import re
import os

# Função para extrair os resultados e as porcentagens
def extrair_resultados_porcentagens(arquivo_entrada, arquivo_saida):
    resultados = {'red': 0, 'black': 0}
    porcentagens = {}
    with open(arquivo_entrada, 'r') as f:
        linhas = f.readlines()
        i = 0
        with open(arquivo_saida, 'w') as out_file:  # Abre o arquivo em modo de escrita ('w')
            while i < len(linhas):
                if "Ultimos 3 resultados:" in linhas[i]:
                    resultado = re.findall(r'red|black', linhas[i])[0]
                    porcentagens_linha = [float(p) for p in linhas[i+1].split(':')[1].strip().split(',')]
                    valor_usado = porcentagens_linha[-1] if resultado == 'red' else porcentagens_linha[-2]
                    out_file.write(f"Resultado: {resultado}, Porcentagem: {valor_usado}\n")
                    # Atualiza contagem de resultados
                    resultados[resultado] += 1
                    # Atualiza contagem de porcentagens
                    porcentagens[valor_usado] = porcentagens.get(valor_usado, 0) + 1
                    i += 11  # Pular 11 linhas para a próxima jogada
                else:
                    i += 1

            # Escreve a contagem de resultados no arquivo
            out_file.write("\nContagem de Resultados:\n")
            for resultado, quantidade in resultados.items():
                out_file.write(f"{resultado}: {quantidade}\n")

            # Escreve a contagem de porcentagens no arquivo
            out_file.write("\nContagem de Porcentagens:\n")
            for porcentagem, quantidade in porcentagens.items():
                out_file.write(f"{porcentagem}: {quantidade}\n")

# Caminhos dos arquivos de entrada e saída
caminho_entrada = os.path.join(os.path.expanduser("~"), "Desktop", "LOGS", "acertos", "acertos_direto 100 mod.txt")
caminho_saida = os.path.join(os.path.expanduser("~"), "Desktop", "LOGS","percentual", "percentual dos acertos direto 100 mod.txt")

# Extrair resultados e porcentagens e salvar em um arquivo
extrair_resultados_porcentagens(caminho_entrada, caminho_saida)

print("Informações salvas em 'percentual dos acertos direto 100.txt'.")
