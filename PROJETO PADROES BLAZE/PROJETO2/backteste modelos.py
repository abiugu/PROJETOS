import pandas as pd
import os
import joblib

# Caminho da planilha com as jogadas reais
caminho_excel = os.path.join(os.path.expanduser("~"), "Desktop", "historico blaze teste2.xlsx")
df = pd.read_excel(caminho_excel)

# Inverter para ordem cronológica (do mais antigo para o mais recente)
df = df[::-1]

# Verificação da ordem
print("\n🧪 Verificando as primeiras e últimas jogadas após inversão:")
print("🟢 Primeiras 5 jogadas (mais antigas):", df['Número'].head(5).tolist())
print("🔴 Últimas 5 jogadas (mais recentes):", df['Número'].tail(5).tolist())

# Caminho dos modelos salvos
modelos_dir = os.path.join(os.path.expanduser("~"), "Desktop", "modelos treinados completo")

# Função para classificar a cor
def classificar_cor_num(n):
    if n == 0:
        return 0
    elif 1 <= n <= 7:
        return 1
    else:
        return 2

df['cor_num'] = df['Número'].apply(classificar_cor_num)

# Sequências usadas nos modelos salvos
sequencias = [5, 10, 25, 50, 100]

# Modelos disponíveis
nomes_modelos = [
    'Random Forest', 'KNN', 'Logistic Regression',
    'Gradient Boosting', 'Decision Tree', 'MLP Classifier'
]

resultados = []

print("\n🔁 Iniciando backtest do mais antigo para o mais recente...")

for seq in sequencias:
    X_teste, y_real = [], []

    print(f"\n🔎 Analisando sequência {seq} na ordem cronológica correta...")

    for i in range(seq, len(df)):
        entrada = df['cor_num'].iloc[i - seq:i].tolist()
        if len(entrada) == seq:
            X_teste.append(entrada)
            y_real.append(df['cor_num'].iloc[i])

    print(f"✅ Primeiro número analisado: {y_real[0]}")
    print(f"✅ Último número analisado: {y_real[-1]}")

    for nome_modelo in nomes_modelos:
        chave = f"{nome_modelo} ({seq})"
        caminho_modelo = os.path.join(modelos_dir, f"{chave}.pkl")

        if not os.path.exists(caminho_modelo):
            continue

        modelo = joblib.load(caminho_modelo)

        try:
            y_pred = modelo.predict(X_teste)
            acertos = sum((pred == real or real == 0) for pred, real in zip(y_pred, y_real))
            total = len(y_real)
            taxa = (acertos / total * 100) if total > 0 else 0
            print(f"📊 {chave}: {acertos}/{total} => {taxa:.2f}%")
            resultados.append([chave, acertos, total, taxa])
        except Exception as e:
            print(f"⚠️ Erro com {chave}: {e}")

# Salvar resultado no Excel
df_result = pd.DataFrame(resultados, columns=["Modelo", "Acertos", "Total", "Assertividade"])
caminho_saida = os.path.join(os.path.expanduser("~"), "Desktop", "avaliacao_modelos_backtest.xlsx")
df_result.to_excel(caminho_saida, index=False)

print("\n✅ Backtest completo. Resultados salvos em:", caminho_saida)
