import pandas as pd
import os

def formatar_planilha():
    """Carrega a planilha, formata a data e hora e salva a alteração no Excel."""

    # Caminho da planilha
    caminho_desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    caminho_excel = os.path.join(caminho_desktop, "historico blaze.xlsx")

    if not os.path.exists(caminho_excel):
        print(f"Arquivo {caminho_excel} não encontrado!")
        return

    try:
        # Carregar a planilha
        df = pd.read_excel(caminho_excel)

        # Converter a coluna "Data" para datetime
        df["Data"] = pd.to_datetime(df["Data"], errors="coerce")

        # Criar uma nova coluna 'DataHora' com o formato desejado
        df["DataHora"] = df["Data"].dt.strftime("%d/%m/%Y %Hh%M")

        # Excluir a coluna original "Data" se não precisar dela
        df.drop(columns=["Data"], inplace=True)

        # Salvar a planilha com as alterações
        df.to_excel(caminho_excel, index=False)
        print("Planilha formatada e salva com sucesso!")

    except Exception as e:
        print(f"Erro ao formatar a planilha: {e}")

# Executar a função para formatar a planilha
formatar_planilha()
