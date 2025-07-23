import os
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.neural_network import MLPClassifier

# Caminho para planilha no Desktop
desktop = os.path.join(os.path.expanduser("~"), "Desktop")
excel_path = os.path.join(desktop, "historico blaze.xlsx")
modelos_dir = os.path.join(desktop, "modelos treinados completo")
os.makedirs(modelos_dir, exist_ok=True)

# Carregar dados
df = pd.read_excel(excel_path)
df = df[::-1]  # ordem cronológica

# Converter número para cor
def classificar_cor_num(n):
    if n == 0:
        return 0
    elif 1 <= n <= 7:
        return 1
    else:
        return 2

df['cor_num'] = df['Número'].apply(classificar_cor_num)

# Função para criar dataset com janelas de sequência
def gerar_dados(df, tamanho_seq):
    X, y = [], []
    for i in range(len(df) - tamanho_seq):
        X.append(df['cor_num'].iloc[i:i+tamanho_seq].tolist())
        y.append(df['cor_num'].iloc[i+tamanho_seq])
    return pd.DataFrame(X), pd.Series(y)

# Modelos disponíveis com otimizações
modelos = {
    'Random Forest': RandomForestClassifier(
        n_estimators=50,
        max_depth=12,
        min_samples_leaf=5,
        n_jobs=-1,
        random_state=42
    ),
    'KNN': KNeighborsClassifier(n_jobs=-1),
    'Logistic Regression': LogisticRegression(max_iter=1000),
    'Gradient Boosting': GradientBoostingClassifier(),
    'Decision Tree': DecisionTreeClassifier(max_depth=10),
    'MLP Classifier': MLPClassifier(max_iter=1000)
}

# Treinar e salvar modelos para cada sequência
sequencias = [5, 10, 25, 50, 100]

print("🔁 Iniciando treinamento dos modelos...")
for seq in sequencias:
    X, y = gerar_dados(df, seq)
    for nome, modelo in modelos.items():
        print(f"🧠 Treinando {nome} com sequência de {seq} jogadas...")
        modelo.fit(X, y)
        nome_arquivo = f"{nome} ({seq}).pkl"
        caminho_modelo = os.path.join(modelos_dir, nome_arquivo)
        joblib.dump(modelo, caminho_modelo, compress=('zlib', 3))
        print(f"✅ Modelo salvo: {nome_arquivo}")

print("\n🎉 Todos os modelos foram treinados e salvos com sucesso!")
