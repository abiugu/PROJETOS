import sys
import os
import pandas as pd
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QTableWidget, QTableWidgetItem
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from collections import defaultdict

class HistoricoBlaze(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Histórico de Jogadas - Blaze")
        self.setGeometry(100, 100, 1000, 600)

        self.data_atual_index = 0
        self.historico = self.carregar_dados()

        self.layout = QVBoxLayout()

        self.label_data = QLabel("", self)
        self.label_data.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.label_data)

        self.tabela = QTableWidget()
        self.layout.addWidget(self.tabela)

        self.btn_anterior = QPushButton("⬅ Dia Anterior", self)
        self.btn_anterior.clicked.connect(self.dia_anterior)
        self.layout.addWidget(self.btn_anterior)

        self.btn_proximo = QPushButton("Dia Seguinte ➡", self)
        self.btn_proximo.clicked.connect(self.dia_proximo)
        self.layout.addWidget(self.btn_proximo)

        # Adicionando o botão para detectar padrões
        self.btn_detectar_padroes = QPushButton("Detectar Padrões", self)
        self.btn_detectar_padroes.clicked.connect(self.detectar_padroes)
        self.layout.addWidget(self.btn_detectar_padroes)

        self.setLayout(self.layout)

        self.exibir_dia()

    def carregar_dados(self):
        """Carrega os dados da planilha localizada no Desktop e ajusta o formato da data e hora."""
        caminho_desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        caminho_excel = os.path.join(caminho_desktop, "historico blaze.xlsx")

        if not os.path.exists(caminho_excel):
            print(f"Arquivo {caminho_excel} não encontrado!")
            return {}

        try:
            df = pd.read_excel(caminho_excel)

            # Especificando o formato de data/hora diretamente
            df["DataHora"] = pd.to_datetime(df["DataHora"], format="%d/%m/%Y %Hh%M", errors="coerce")

            # Adicionando as colunas 'Hora' e 'Minuto' para facilitar a organização
            df['Hora'] = df["DataHora"].dt.hour
            df['Minuto'] = df["DataHora"].dt.minute

            # Agora, os dados estão com a hora e minuto extraídos corretamente
            dias_unicos = sorted(df["DataHora"].dt.date.unique(), reverse=True)
            historico = {dia: df[df["DataHora"].dt.date == dia] for dia in dias_unicos}

            return historico
        except Exception as e:
            print(f"Erro ao carregar o histórico: {e}")
            return {}

    def exibir_dia(self):
        """Exibe os dados do dia atual na tabela."""
        if not self.historico:
            self.label_data.setText("Erro ao carregar dados.")
            return
    
        dias = list(self.historico.keys())
        data_atual = dias[self.data_atual_index]
        self.label_data.setText(f"Data: {data_atual}")
    
        df = self.historico[data_atual]
    
        # Extraindo hora e minuto para garantir que as jogadas estejam no formato correto
        df['Hora'] = df["DataHora"].dt.hour
        df['Minuto'] = df["DataHora"].dt.minute
    
        # Ordenar os dados para garantir a ordem correta de hora e minuto
        df = df.sort_values(by=["Hora", "Minuto"])
    
        
        # Criar um conjunto apenas com os minutos reais existentes no DataFrame
        horas_disponiveis = sorted(df["Hora"].unique())
        minutos_disponiveis = { (row["Hora"], row["Minuto"]) for _, row in df.iterrows() }

    
        max_jogadas_por_minuto = 2  # Sempre no máximo 2 jogadas por minuto

        # Filtrar apenas os minutos reais do dataframe
        minutos_disponiveis = sorted(df["Minuto"].unique())
        
        # Criar colunas apenas para os minutos reais e no máximo 2 por minuto
        self.tabela.setColumnCount(len(minutos_disponiveis) * max_jogadas_por_minuto)
        self.tabela.setHorizontalHeaderLabels(
            [f"{minuto}m ({i+1})" for minuto in minutos_disponiveis for i in range(max_jogadas_por_minuto)]
        )

    
        # Definindo a tabela para mostrar
        self.tabela.setRowCount(len(horas_disponiveis))
    
        self.tabela.setVerticalHeaderLabels([f"{h}h" for h in horas_disponiveis])
    
        # Criando uma estrutura para armazenar as jogadas por minuto
        jogadas_por_minuto = {}
    
        for _, row in df.iterrows():
            hora = row["Hora"]
            minuto = row["Minuto"]
            numero = str(row["Número"])  # Obtendo o número
            cor = row["Cor"].lower()
    
            # Agrupando as jogadas por minuto
            if (hora, minuto) not in jogadas_por_minuto:
                jogadas_por_minuto[(hora, minuto)] = []
    
            jogadas_por_minuto[(hora, minuto)].append((numero, cor))
    
        # Exibir as jogadas na tabela
        for i, hora in enumerate(horas_disponiveis):
            for minuto in range(60):
                jogadas = jogadas_por_minuto.get((hora, minuto), [])
    
                # Garantir que tenha no máximo 2 jogadas por minuto (caso haja mais, vamos descartar as extras)
                if len(jogadas) > 2:
                    jogadas = jogadas[:2]  # Limitar a 2 jogadas por minuto
    
                # Inverter as jogadas dentro do minuto (se houver 2 jogadas)
                jogadas_invertidas = jogadas[::-1]  # Inverte a lista
    
                # Se houver jogadas para esse minuto
                for idx, (numero, cor) in enumerate(jogadas_invertidas):
                    item = QTableWidgetItem(numero)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
    
                    # Definição das cores de fundo e do texto
                    if cor == "red":
                        item.setForeground(QColor(0, 0, 0))  # Número preto
                        item.setBackground(QColor(255, 0, 0))  # Fundo vermelho
                    elif cor == "black":
                        item.setForeground(QColor(255, 255, 255))  # Número branco
                        item.setBackground(QColor(0, 0, 0))  # Fundo preto
                    elif cor == "white":
                        item.setForeground(QColor(0, 0, 0))  # Número preto
                        item.setBackground(QColor(255, 255, 255))  # Fundo branco
    
                    # Ajustando as células para garantir que as jogadas no mesmo minuto apareçam separadas
                    row_index = i
                    col_index = minuto * max_jogadas_por_minuto + idx  # Desloca a coluna para a segunda jogada, se existir
    
                    # Colocando o item na célula da tabela
                    self.tabela.setItem(row_index, col_index, item)
    
        # Ajustando o tamanho das células para que caibam melhor na janela
        for col in range(self.tabela.columnCount()):
            self.tabela.setColumnWidth(col, 50)  # Reduzindo a largura das colunas para metade (30 pixels, por exemplo)
    
        for row in range(self.tabela.rowCount()):
            self.tabela.setRowHeight(row, 35)  # Reduzindo a altura das linhas para metade (20 pixels, por exemplo)




    def dia_anterior(self):
        """Mostra o dia anterior."""
        if self.data_atual_index < len(self.historico) - 1:
            self.data_atual_index += 1
            self.exibir_dia()

    def dia_proximo(self):
        """Mostra o próximo dia."""
        if self.data_atual_index > 0:
            self.data_atual_index -= 1
            self.exibir_dia()

    def capturar_dados_da_tabela(self):
        """Captura os dados (cores e números) da tabela e os organiza por data, hora e minuto."""
        dados_organizados = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        
        for row in range(self.tabela.rowCount()):
            for col in range(self.tabela.columnCount()):
                item = self.tabela.item(row, col)
                if item is None:
                    continue

                numero = item.text()  # Número na célula
                cor = None

                # Identificar a cor de fundo
                background_color = item.background().color()
                if background_color == QColor(255, 0, 0):  # Cor de fundo vermelho
                    cor = 'red'
                elif background_color == QColor(0, 0, 0):  # Cor de fundo preto
                    cor = 'black'
                elif background_color == QColor(255, 255, 255):  # Cor de fundo branco
                    cor = 'white'

                if cor:
                    # Captura de hora e minuto
                    hora = row  # Você precisaria mapear para a hora correta, dependendo do seu layout
                    minuto = col  # Você precisaria mapear para o minuto correto

                    # Organizando os dados
                    dados_organizados['2025-02-27'][hora][minuto].append((cor, numero))  # Exemplo de data fixa

        return dados_organizados

    def detectar_padroes_ao_longos_dos_dias(self, dados_organizados):
        """Detecta padrões baseados em hora, minuto e cor para todos os dias."""
        padroes_encontrados = []

        # Iterando sobre os dados de todos os dias
        for data, horas in dados_organizados.items():
            for hora, minutos in horas.items():
                for minuto, jogadas in minutos.items():
                    if len(jogadas) == 2:  # Verifica se há duas jogadas no mesmo minuto
                        cor_1, _ = jogadas[0]
                        cor_2, _ = jogadas[1]

                        # Caso as cores sejam iguais (dois vermelhos, dois pretos, etc.)
                        if cor_1 == cor_2:
                            padroes_encontrados.append(f"Em {data} às {hora}h{minuto} ocorreram 2 jogadas da cor {cor_1}.")
                        
                            # Verificando o próximo minuto
                            proximo_minuto = minuto + 1 if minuto < 59 else 0
                            proxima_hora = hora + 1 if proximo_minuto == 0 else hora

                            # Se o próximo minuto da próxima hora existir, verificamos as cores
                            if proxima_hora in horas and proximo_minuto in horas[proxima_hora]:
                                jogadas_proximas = horas[proxima_hora][proximo_minuto]
                                if len(jogadas_proximas) == 2:
                                    cor_1_proxima, _ = jogadas_proximas[0]
                                    cor_2_proxima, _ = jogadas_proximas[1]
                                    if cor_1_proxima == cor_2_proxima:
                                        padroes_encontrados.append(f"Após duas jogadas de {cor_1} em {data} às {hora}h{minuto}, "
                                                                  f"no próximo minuto às {proxima_hora}h{proximo_minuto}, "
                                                                  f"ocorrem duas jogadas da cor {cor_1_proxima}.")
        
        return padroes_encontrados

    def rodar_ia_na_janela(self):
        # Captura os dados da tabela
        dados_organizados = self.capturar_dados_da_tabela()

        # Detecta padrões nos dados capturados
        padroes = self.detectar_padroes_ao_longos_dos_dias(dados_organizados)

        # Exibe os padrões encontrados
        if padroes:
            for padrao in padroes:
                print(padrao)
        else:
            print("Nenhum padrão encontrado.")

    def detectar_padroes(self):
        # Chama a função de IA para detectar padrões
        self.rodar_ia_na_janela()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    janela = HistoricoBlaze()
    janela.show()
    sys.exit(app.exec())
