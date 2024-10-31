import os
import re
import pandas as pd
from collections import defaultdict

def ler_e_analisar_log(caminho_arquivo_log):
    with open(caminho_arquivo_log, 'r') as f:
        log_data = f.read()
    
    # Padrões de regex para capturar os resultados e porcentagens
    resultados_re = re.compile(r'Ultimos 3 resultados: (\w+), (\w+), (\w+)')
    porcentagens_25_re = re.compile(r'Ultimas 25 porcentagens: ([\d.]+), ([\d.]+), ([\d.]+)')
    porcentagens_50_re = re.compile(r'Ultimas 50 porcentagens: ([\d.]+), ([\d.]+), ([\d.]+)')
    porcentagens_100_re = re.compile(r'Ultimas 100 porcentagens: ([\d.]+), ([\d.]+), ([\d.]+)')
    porcentagens_500_re = re.compile(r'Ultimas 500 porcentagens: ([\d.]+), ([\d.]+), ([\d.]+)')
    
    resultados = resultados_re.findall(log_data)
    porcentagens_25 = porcentagens_25_re.findall(log_data)
    porcentagens_50 = porcentagens_50_re.findall(log_data)
    porcentagens_100 = porcentagens_100_re.findall(log_data)
    porcentagens_500 = porcentagens_500_re.findall(log_data)

    # Converte as porcentagens para float
    porcentagens_25 = [(float(p[0]), float(p[1]), float(p[2])) for p in porcentagens_25]
    porcentagens_50 = [(float(p[0]), float(p[1]), float(p[2])) for p in porcentagens_50]
    porcentagens_100 = [(float(p[0]), float(p[1]), float(p[2])) for p in porcentagens_100]
    porcentagens_500 = [(float(p[0]), float(p[1]), float(p[2])) for p in porcentagens_500]

    return resultados, porcentagens_25, porcentagens_50, porcentagens_100, porcentagens_500

def analisar_padroes(resultados, porcentagens_25, porcentagens_50, porcentagens_100, porcentagens_500):
    acertos_erros = {'red': defaultdict(lambda: {'acertos': 0, 'erros': 0}),
                     'black': defaultdict(lambda: {'acertos': 0, 'erros': 0}),
                     'white': defaultdict(lambda: {'acertos': 0, 'erros': 0})}

    i = 0
    while i < len(resultados) - 2:
        cor_atual = resultados[i][0]
        
        # Verifica se os 3 últimos resultados são iguais (sequência de cores)
        if resultados[i][0] == resultados[i][1] == resultados[i][2]:
            if cor_atual not in ["black", "red", "white"]:
                i += 1
                continue

            # Captura os índices corretos para as porcentagens
            index = {"white": 0, "black": 1, "red": 2}[cor_atual]

            # Captura as porcentagens correspondentes e as rotula (percentual 25, 50, 100, 500)
            porcentagem_atual_25 = (porcentagens_25[i][index], "Percentual 25")
            porcentagem_atual_50 = (porcentagens_50[i][index], "Percentual 50")
            porcentagem_atual_100 = (porcentagens_100[i][index], "Percentual 100")
            porcentagem_atual_500 = (porcentagens_500[i][index], "Percentual 500")

            # Combinações de duas porcentagens
            combinacoes = [
                (porcentagem_atual_25, porcentagem_atual_50),
                (porcentagem_atual_50, porcentagem_atual_100),
                (porcentagem_atual_100, porcentagem_atual_500)
            ]

            # Verifica a próxima linha para determinar se houve quebra na sequência
            if i + 1 < len(resultados):
                for comb in combinacoes:
                    if resultados[i + 1][0] == cor_atual:  # Erro: manteve a sequência
                        acertos_erros[cor_atual][comb]['erros'] += 1
                    else:  # Acerto: quebrou a sequência
                        acertos_erros[cor_atual][comb]['acertos'] += 1

            # Avança até quebrar a sequência de 3 cores iguais
            while i < len(resultados) and resultados[i][0] == cor_atual:
                i += 1
        else:
            i += 1

    return acertos_erros

def salvar_resultados(acertos_erros, caminho_arquivo_saida):
    resultados_com_assertividade = []

    for cor in acertos_erros.keys():
        for combinacao, dados in acertos_erros[cor].items():
            acertos = dados['acertos']
            erros = dados['erros']
            total = acertos + erros
            
            # Calcular assertividade em percentual
            assertividade = (acertos / total * 100) if total > 0 else 0
            
            # Adiciona os dados à lista para o DataFrame
            resultados_com_assertividade.append({
                'Cor': cor,
                'Combinação': f"{combinacao[0][1]} ({combinacao[0][0]:.1f}%) e {combinacao[1][1]} ({combinacao[1][0]:.1f}%)",
                'Acertos': acertos,
                'Erros': erros,
                'Total de Jogadas': total,
                'Assertividade (%)': f"{assertividade:.1f}"
            })

    # Cria um DataFrame com os resultados
    df_resultados = pd.DataFrame(resultados_com_assertividade)

    # Ordenar os resultados pela assertividade (decrescente) e, em seguida, pela quantidade de jogadas (total)
    df_resultados.sort_values(by=['Assertividade (%)', 'Total de Jogadas'], ascending=[False, False], inplace=True)

    # Salvar os resultados em um arquivo Excel
    df_resultados.to_excel(caminho_arquivo_saida, index=False)

def main():
    desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
    arquivo_log = os.path.join(desktop_path, 'LOGS', 'log 36.txt')
    
    # Ler o log e capturar resultados e porcentagens
    resultados, porcentagens_25, porcentagens_50, porcentagens_100, porcentagens_500 = ler_e_analisar_log(arquivo_log)
    
    # Analisar padrões de acertos e erros
    acertos_erros = analisar_padroes(resultados, porcentagens_25, porcentagens_50, porcentagens_100, porcentagens_500)
    
    # Salvar resultados no arquivo "resultados.xlsx" na área de trabalho
    arquivo_saida = os.path.join(desktop_path, 'resultados.xlsx')
    salvar_resultados(acertos_erros, arquivo_saida)

if __name__ == "__main__":
    main()
