import os

def extrair_texto(arquivo_entrada, caminho_saida):
    try:
        # Caminho completo para o arquivo de entrada
        caminho_entrada = os.path.join(os.path.expanduser("~"), "Desktop", "LOGS","resultados", arquivo_entrada)
        
        with open(caminho_entrada, 'r') as entrada:
            linhas = entrada.readlines()
            
            # Encontrar a linha que contém "Possibilidades:"
            index_inicio = None
            for i, linha in enumerate(linhas):
                if "Possibilidades:" in linha:
                    index_inicio = i + 1  # Próxima linha
                    break
            
            # Se não encontrar a palavra-chave, sai da função
            if index_inicio is None:
                print(f"Palavra-chave 'Possibilidades:' não encontrada no arquivo {arquivo_entrada}.")
                return
            
            # Extrair o texto a partir da linha encontrada
            texto = ''.join(linhas[index_inicio:])
            
            # Escrever o texto extraído no arquivo de saída
            with open(caminho_saida, 'w') as saida:
                saida.write(texto)
            
            print(f"Texto extraído do arquivo {arquivo_entrada} com sucesso e salvo em {caminho_saida}!")
    
    except FileNotFoundError:
        print(f"Arquivo de entrada {arquivo_entrada} não encontrado.")

# Nomes dos arquivos de entrada
arquivo_entrada1 = "resultados_60 branco.txt"
arquivo_entrada2 = "resultados_erros_60 branco.txt"
arquivo_entrada3 = "resultados_acertos_branco_60 branco.txt"
arquivo_entrada4 = "resultados_acertos_gale_branco_60 branco.txt"

# Caminhos dos arquivos de saída
caminho_saida1 = os.path.join(os.path.expanduser("~"), "Desktop", "LOGS", "sequencias", "sequencias 60 branco.txt")
caminho_saida2 = os.path.join(os.path.expanduser("~"), "Desktop", "LOGS", "sequencias", "sequencias erros 60 branco.txt")
caminho_saida3 = os.path.join(os.path.expanduser("~"), "Desktop", "LOGS", "sequencias", "sequencias acertos branco 60.txt")
caminho_saida4 = os.path.join(os.path.expanduser("~"), "Desktop", "LOGS", "sequencias", "sequencias acertos gale branco 60.txt")

# Chamar a função para extrair o texto
extrair_texto(arquivo_entrada1, caminho_saida1)
extrair_texto(arquivo_entrada2, caminho_saida2)
extrair_texto(arquivo_entrada3, caminho_saida3)
extrair_texto(arquivo_entrada4, caminho_saida4)