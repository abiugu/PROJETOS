import re
import os

# Função para extrair os resultados e as porcentagens
def extrair_resultados_porcentagens(arquivo_entrada, arquivo_saida):
    resultados = {'red': 0, 'black': 0}
    porcentagens = {}
    resultados_porcentagens = []
    
    with open(arquivo_entrada, 'r') as f:
        linhas = f.readlines()
        i = 0
        while i < len(linhas):
            if "Ultimos 3 resultados:" in linhas[i]:
                resultados_encontrados = re.findall(r'red|black', linhas[i])
                if resultados_encontrados:
                    resultado = resultados_encontrados[0]
                    porcentagens_linha = [float(p) for p in linhas[i + 1].split(':')[1].strip().split(',')]
                    valor_usado = porcentagens_linha[1] if resultado == 'black' else porcentagens_linha[2]
                    resultados_porcentagens.append((resultado, valor_usado))
                    resultados[resultado] += 1
                    porcentagens[valor_usado] = porcentagens.get(valor_usado, 0) + 1
                    i += 2  # Pula para a próxima linha após porcentagens
                else:
                    i += 1
            else:
                i += 1

    # Escreve os resultados extraídos no arquivo de saída
    with open(arquivo_saida, 'w') as out_file:
        for resultado, valor in resultados_porcentagens:
            out_file.write(f"Resultado: {resultado}, Porcentagem: {valor}\n")
        
        # Escreve a contagem de resultados no arquivo de saída
        out_file.write("\nContagem de Resultados:\n")
        for resultado, quantidade in resultados.items():
            out_file.write(f"{resultado}: {quantidade}\n")
        
        # Escreve a contagem de porcentagens no arquivo de saída
        out_file.write("\nContagem de Porcentagens:\n")
        for porcentagem, quantidade in porcentagens.items():
            out_file.write(f"{porcentagem}: {quantidade}\n")

# Caminhos dos arquivos de entrada e saída
caminho_entrada = os.path.join(os.path.expanduser("~"), "Desktop", "LOGS","resultados", "resultados_100 direto mod.txt")
caminho_saida = os.path.join(os.path.expanduser("~"), "Desktop", "LOGS","percentual", "percentual das jogadas 100 direto mod.txt")

# Extrair resultados e porcentagens e salvar em um arquivo
extrair_resultados_porcentagens(caminho_entrada, caminho_saida)

print("Informações salvas em 'percentual das jogadas 100 direto.txt'.")
