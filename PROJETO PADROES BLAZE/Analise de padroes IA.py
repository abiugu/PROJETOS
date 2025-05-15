import sys
import pandas as pd
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, QMessageBox
from collections import Counter
from datetime import timedelta


class BlazeAnalyzer(QWidget):
    def __init__(self):
        super().__init__()
        self.df = None  # Variável para armazenar os dados carregados
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Analisador de Padrões - Blaze")
        self.setGeometry(100, 100, 400, 200)

        layout = QVBoxLayout()

        self.label = QLabel("Selecione um arquivo Excel para análise", self)
        layout.addWidget(self.label)

        self.btnLoad = QPushButton("Carregar Arquivo Excel", self)
        self.btnLoad.clicked.connect(self.loadFile)
        layout.addWidget(self.btnLoad)

        self.btnAnalyze = QPushButton("Executar Análises", self)
        self.btnAnalyze.clicked.connect(self.executar_analises)
        self.btnAnalyze.setEnabled(False)  # Desabilitado até carregar um arquivo
        layout.addWidget(self.btnAnalyze)

        self.setLayout(layout)

    def loadFile(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar arquivo", "",
            "Excel Files (*.xlsx;*.xls);;Todos os Arquivos (*)"
        )

        if file_path:
            try:
                self.df = pd.read_excel(file_path)
                self.df['data'] = pd.to_datetime(self.df['data'], dayfirst=True, errors='coerce')  
                self.df = self.df.sort_values(by='data').reset_index(drop=True)

                QMessageBox.information(self, "Sucesso", "Arquivo carregado com sucesso!")
                self.btnAnalyze.setEnabled(True)  # Habilita o botão de análise

            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Falha ao carregar o arquivo: {str(e)}")

    def encontrar_padroes_repetidos(self):
        """Identifica sequências de jogadas que antecedem um branco (0)."""
        if self.df is None:
            QMessageBox.warning(self, "Aviso", "Nenhum dado carregado!")
            return

        sequencias = []
        min_seq, max_seq = 5, 8

        for i in range(len(self.df) - min_seq):
            for seq_tam in range(min_seq, max_seq + 1):
                if i + seq_tam >= len(self.df):
                    break

                if self.df.iloc[i + seq_tam]['numero'] == 0:
                    sequencia = tuple(self.df.iloc[i:i + seq_tam]['cor'])
                    sequencias.append(sequencia)

        contagem = Counter(sequencias)

        resultado = "Top 10 padrões mais frequentes antes do branco (0):\n"
        for padrao, freq in contagem.most_common(10):
            resultado += f"{padrao}: {freq} vezes\n"

        QMessageBox.information(self, "Padrões Repetidos", resultado)

    def analisar_recuperacao(self):
        """Analisa minutos com poucos brancos seguidos de aumento na frequência."""
        if self.df is None:
            QMessageBox.warning(self, "Aviso", "Nenhum dado carregado!")
            return

        self.df['minuto'] = self.df['data'].dt.strftime('%H:%M')
        contagem_brancos = self.df[self.df['numero'] == 0]['minuto'].value_counts()

        resultado = "Minutos com baixa frequência seguidos de aumento:\n"
        for minuto, count in contagem_brancos.items():
            if count < 2 and contagem_brancos.get(minuto, 0) >= 2:
                resultado += f"Minuto {minuto} teve baixa ocorrência e depois aumento!\n"

        QMessageBox.information(self, "Análise de Recuperação", resultado)

    def analisar_numeros_repetidos(self):
        """Verifica a frequência de números que aparecem repetidamente."""
        if self.df is None:
            QMessageBox.warning(self, "Aviso", "Nenhum dado carregado!")
            return

        contagem_numeros = Counter(self.df['numero'])

        resultado = "Números mais frequentes:\n"
        for numero, freq in contagem_numeros.most_common(10):
            resultado += f"Número {numero}: {freq} vezes\n"

        QMessageBox.information(self, "Números Repetidos", resultado)

    def analisar_padroes_horarios(self):
        """Verifica padrões de sequências ocorrendo exatamente 1 hora antes ou com margem de ±1 minuto."""
        if self.df is None:
            QMessageBox.warning(self, "Aviso", "Nenhum dado carregado!")
            return

        padroes = {}

        for i, row in self.df.iterrows():
            hora_atual = row['data']
            candidatos = self.df[
                (self.df['data'] >= hora_atual - timedelta(minutes=1)) &
                (self.df['data'] <= hora_atual + timedelta(minutes=1))
            ]

            padrao = tuple(candidatos['cor'])
            padroes[padrao] = padroes.get(padrao, 0) + 1

        resultado = "Padrões recorrentes em horários semelhantes:\n"
        for padrao, freq in sorted(padroes.items(), key=lambda x: x[1], reverse=True)[:10]:
            resultado += f"{padrao}: {freq} vezes\n"

        QMessageBox.information(self, "Padrões por Horário", resultado)

    def executar_analises(self):
        """Executa todas as análises."""
        if self.df is None:
            QMessageBox.warning(self, "Aviso", "Nenhum dado carregado!")
            return

        self.encontrar_padroes_repetidos()
        self.analisar_recuperacao()
        self.analisar_numeros_repetidos()
        self.analisar_padroes_horarios()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BlazeAnalyzer()
    window.show()
    sys.exit(app.exec())
