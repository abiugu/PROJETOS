import sys
import os
import pandas as pd
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QTableWidget, QTableWidgetItem, QDialog
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from collections import defaultdict


class PopupPadroes(QDialog):
        def __init__(self, padroes_detectados):
            super().__init__()
            self.setWindowTitle("Padrões Detectados")
            self.setGeometry(100, 100, 400, 300)

            layout = QVBoxLayout()

            if padroes_detectados:
                for padrao in padroes_detectados:
                    layout.addWidget(QLabel(padrao))
            else:
                layout.addWidget(QLabel("Nenhum padrão detectado."))

            btn_fechar = QPushButton("Fechar")
            btn_fechar.clicked.connect(self.close)
            layout.addWidget(btn_fechar)

            self.setLayout(layout)


class HistoricoBlaze(QWidget):
    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout(self)
        self.label_padroes = QLabel(self)
        self.label_padroes.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.label_padroes)

        self.setWindowTitle("Histórico de Jogadas - Blaze")
        self.setGeometry(100, 100, 1000, 600)
        self.setMinimumSize(800, 600)

        self.data_atual_index = 0
        self.historico = self.carregar_dados()

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

        self.btn_detectar_padroes = QPushButton("Detectar Padrões", self)
        self.btn_detectar_padroes.clicked.connect(self.detectar_padroes)
        self.layout.addWidget(self.btn_detectar_padroes)

        self.setLayout(self.layout)
        self.exibir_dia()


    def detectar_padroes_antes_branco(self):
        """Verifica sequências de jogadas que ocorrem frequentemente antes do branco (0)."""
        dados_organizados = self.capturar_dados_da_tabela()
        sequencias_antes_do_branco = defaultdict(list)

        for hora, minutos in dados_organizados.items():
            for minuto, jogadas in minutos.items():
                for i in range(len(jogadas) - 1):  # Evita index error
                    cor_atual, num_atual = jogadas[i]
                    cor_proxima, num_proxima = jogadas[i + 1]

                    if num_proxima == "0":  # Se a próxima jogada for branco (0)
                        padrao = (cor_atual, num_atual)  # Guarda a jogada que ocorreu antes
                        sequencias_antes_do_branco[padrao].append(f"{hora}h{minuto}")

        padroes_relevantes = [
            f"Padrão {cor}-{num} ocorreu antes do branco nos minutos: {', '.join(ocorrencias)}"
            for (cor, num), ocorrencias in sequencias_antes_do_branco.items()
            if len(ocorrencias) > 1
        ]
        return padroes_relevantes


    def detectar_tendencias_branco(self):
        """Detecta padrões que indicam possível ocorrência de branco (0)."""
        dados_organizados = self.capturar_dados_da_tabela()
        tendencias = []

        contagem_branco = defaultdict(int)
        for hora, minutos in dados_organizados.items():
            for minuto, jogadas in minutos.items():
                for _, numero in jogadas:
                    if numero == "0":
                        contagem_branco[minuto] += 1

        for minuto, ocorrencias in contagem_branco.items():
            if ocorrencias == 0:
                tendencias.append(f"Nenhum branco no minuto {minuto}, possível tendência futura.")

        return tendencias


    def capturar_dados_da_tabela(self):
        """Captura os dados exibidos na tabela, organizando-os por data, hora e minuto."""
        dados_organizados = defaultdict(lambda: defaultdict(list))

        for row in range(self.tabela.rowCount()):
            for col in range(self.tabela.columnCount()):
                item = self.tabela.item(row, col)
                if item:
                    hora = int(self.tabela.verticalHeaderItem(row).text().rstrip("h"))
                    minuto = int(self.tabela.horizontalHeaderItem(col).text().split("m")[0])

                    cor = self.get_cor_from_item(item)
                    numero = item.text()

                    dados_organizados[hora][minuto].append((cor, numero))
        return dados_organizados

    def detectar_padroes_de_dias(self):
        """Detecta padrões de jogadas que se repetem entre múltiplos dias."""
        # Organize o histórico por dia, hora e minuto
        dados_organizados = self.capturar_dados_da_tabela()

        padroes_encontrados = []

        # Iterando sobre os dias no histórico
        for data, horas in dados_organizados.items():
            for hora, minutos in horas.items():
                if isinstance(minutos, list):  # Verificando se minutos é uma lista (caso seja uma lista de jogadas)
                    for minuto, jogadas in enumerate(minutos):

                        # Verificando se jogadas tem exatamente 2 itens
                        if len(jogadas) == 2:
                            try:
                                cor_1, numero_1 = jogadas  # Agora jogadas já é uma tupla com 2 elementos

                                # Crie um padrão para comparar
                                padrao = (cor_1, numero_1)

                                # Compare com padrões anteriores em outros dias
                                for dia_anterior, horas_anterior in dados_organizados.items():
                                    if dia_anterior != data:  # Compare com dias diferentes
                                        for hora_anterior, minutos_anterior in horas_anterior.items():
                                            if isinstance(minutos_anterior, list):
                                                for minuto_anterior, jogadas_anterior in enumerate(minutos_anterior):
                                                    # Verificando se há exatamente 2 jogadas por minuto
                                                    if len(jogadas_anterior) == 2:
                                                        cor_1_anterior, numero_1_anterior = jogadas_anterior
                                                        padrao_anterior = (cor_1_anterior, numero_1_anterior)

                                                        if padrao == padrao_anterior:
                                                            padroes_encontrados.append(f"Em {data} às {hora}h{minuto} e em {dia_anterior} às {hora_anterior}h{minuto_anterior}, "
                                                                                   f"ocorreram duas jogadas da sequência {cor_1}-{numero_1}.")
                            except ValueError as e:
                                print(f"Erro ao desempacotar jogadas no minuto {minuto}: {jogadas} - Erro: {e}")
                                continue
        return padroes_encontrados



    def get_cor_from_item(self, item):
        """Retorna a cor baseada no fundo da célula (vermelho, preto ou branco)."""
        background_color = item.background().color()
        if background_color == QColor(255, 0, 0):
            return 'red'
        elif background_color == QColor(0, 0, 0):
            return 'black'
        elif background_color == QColor(255, 255, 255):
            return 'white'
        return None
    
    def detectar_padroes(self):
        """Detecta padrões antes do branco e tendências gerais."""
        padroes = self.detectar_tendencias_branco()
        padroes_antes_branco = self.detectar_padroes_antes_branco()

        padroes.extend(padroes_antes_branco)
        self.exibir_padroes_na_janela(padroes)



    def exibir_padroes_na_janela(self, padroes):
        """Exibe os padrões encontrados em uma janela pop-up."""
        popup = self.PopupPadroes(padroes)
        popup.exec()

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
        """Captura os dados exibidos na tabela, organizando-os por data, hora e minuto."""
        dados_organizados = defaultdict(lambda: defaultdict(list))

        horas_disponiveis = [int(self.tabela.verticalHeaderItem(i).text().rstrip("h")) for i in range(self.tabela.rowCount())]
        minutos_disponiveis = sorted(set(int(self.tabela.horizontalHeaderItem(col).text().split("m")[0]) for col in range(self.tabela.columnCount())))

        for row in range(self.tabela.rowCount()):
            for col in range(self.tabela.columnCount()):
                item = self.tabela.item(row, col)
                if item:
                    hora = horas_disponiveis[row]
                    minuto = minutos_disponiveis[col // 2]

                    cor = self.get_cor_from_item(item)
                    numero = item.text()
                    dados_organizados[hora][minuto].append((cor, numero))

        return dados_organizados


    def detectar_padroes(self):
        padroes = self.detectar_tendencias_branco()
        padroes_antes_branco = self.detectar_padroes_antes_branco()
    
        if padroes is None:
            padroes = []
    
        padroes.extend(padroes_antes_branco)
    
        # Criar um dicionário para contar quantas vezes cada padrão aparece
        contagem_padroes = {}
    
        for padrao in padroes:
            descricao_limpa = " ".join(padrao.split()[:-1])  # Remove a última parte (horário)
            
            if descricao_limpa in contagem_padroes:
                contagem_padroes[descricao_limpa] += 1
            else:
                contagem_padroes[descricao_limpa] = 1
    
        # Criar a lista formatada para o pop-up
        padroes_formatados = [
            f"{descricao} - visto {quantidade} vezes"
            for descricao, quantidade in contagem_padroes.items()
        ]
    
        # Exibir pop-up com os padrões
        popup = PopupPadroes(padroes_formatados)
        popup.exec()



if __name__ == "__main__":
    app = QApplication(sys.argv)
    janela = HistoricoBlaze()
    janela.show()
    sys.exit(app.exec())
