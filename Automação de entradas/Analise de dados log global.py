import os
import re
from collections import defaultdict

def ler_e_analisar_log(caminho_arquivo_log):
    with open(caminho_arquivo_log, 'r') as f:
        log_data = f.read()
    
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
    
    return resultados, porcentagens_25, porcentagens_50, porcentagens_100, porcentagens_500

def comparar_percentuais(atual, oposta):
    if atual > oposta:
        return '>'
    elif atual < oposta:
        return '<'
    else:
        return '='

def analisar_padroes(resultados, porcentagens_25, porcentagens_50, porcentagens_100, porcentagens_500):
    padroes_analise = defaultdict(lambda: {'acertos': 0, 'total': 0})

    for i in range(len(resultados) - 2):
        cor_atual = resultados[i][0]
        if resultados[i][0] == resultados[i][1] == resultados[i][2]:
            if cor_atual == "black":
                cor_oposta = "red"
            elif cor_atual == "red":
                cor_oposta = "black"
            else:
                continue

            try:
                porcentagem_atual_25 = float(porcentagens_25[i][2] if cor_atual == "red" else porcentagens_25[i][1])
                porcentagem_oposta_25 = float(porcentagens_25[i][1] if cor_atual == "red" else porcentagens_25[i][2])
                porcentagem_atual_50 = float(porcentagens_50[i][2] if cor_atual == "red" else porcentagens_50[i][1])
                porcentagem_oposta_50 = float(porcentagens_50[i][1] if cor_atual == "red" else porcentagens_50[i][2])
                porcentagem_atual_100 = float(porcentagens_100[i][2] if cor_atual == "red" else porcentagens_100[i][1])
                porcentagem_oposta_100 = float(porcentagens_100[i][1] if cor_atual == "red" else porcentagens_100[i][2])
                porcentagem_atual_500 = float(porcentagens_500[i][2] if cor_atual == "red" else porcentagens_500[i][1])
                porcentagem_oposta_500 = float(porcentagens_500[i][1] if cor_atual == "red" else porcentagens_500[i][2])
            except IndexError:
                continue

            comparacao_25 = comparar_percentuais(porcentagem_atual_25, porcentagem_oposta_25)
            comparacao_50 = comparar_percentuais(porcentagem_atual_50, porcentagem_oposta_50)
            comparacao_100 = comparar_percentuais(porcentagem_atual_100, porcentagem_oposta_100)
            comparacao_500 = comparar_percentuais(porcentagem_atual_500, porcentagem_oposta_500)

            chave_padrao = (cor_atual, porcentagem_atual_25, comparacao_25, comparacao_50, comparacao_100, comparacao_500)
            
            # Verificar os próximos dois resultados
            if i + 2 < len(resultados):
                acerto = resultados[i + 1][0] != cor_atual or resultados[i + 2][0] != cor_atual

                padroes_analise[chave_padrao]['total'] += 1
                if acerto:
                    padroes_analise[chave_padrao]['acertos'] += 1

    return padroes_analise

def main():
    desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
    arquivo_log = os.path.join(desktop_path, 'LOGS', 'log global.txt')
    
    resultados, porcentagens_25, porcentagens_50, porcentagens_100, porcentagens_500 = ler_e_analisar_log(arquivo_log)
    padroes_analise = analisar_padroes(resultados, porcentagens_25, porcentagens_50, porcentagens_100, porcentagens_500)
    
    arquivo_previsoes = os.path.join(desktop_path, 'previsoes_quebras_padrao.txt')
    
    with open(arquivo_previsoes, 'w') as f:
        f.write("Análise de Comparações de Percentuais:\n\n")
        
        # Ordenando os padrões pela assertividade em ordem decrescente
        padroes_ordenados = sorted(padroes_analise.items(), key=lambda x: (x[1]['acertos'] / x[1]['total']) if x[1]['total'] > 0 else 0, reverse=True)
        
        for chave_padrao, dados in padroes_ordenados:
            cor_atual, percentual_atual, comp_25, comp_50, comp_100, comp_500 = chave_padrao
            total = dados['total']
            acertos = dados['acertos']
            assertividade = (acertos / total) * 100 if total > 0 else 0

            if assertividade > 80:
                f.write(f"Ultimos 3 resultados: {cor_atual}, {cor_atual}, {cor_atual}\n")
                f.write(f"percentual cor atual: {percentual_atual}%\n")
                f.write(f"Ultimas 25 porcentagens: {comp_25}\n")
                f.write(f"Ultimas 50 porcentagens: {comp_50}\n")
                f.write(f"Ultimas 100 porcentagens: {comp_100}\n")
                f.write(f"Ultimas 500 porcentagens: {comp_500}\n")
                f.write(f"acertos: {acertos}\n")
                f.write(f"total: {total}\n")
                f.write(f"assertividade: {assertividade:.2f}%\n\n")
