import pandas as pd
import requests
import time
import os
import random
import joblib
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.neural_network import MLPClassifier

# Caminho do Excel no Desktop
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", "historico blaze teste.xlsx")
df_excel = pd.read_excel(desktop_path)
df_excel = df_excel[::-1]  # Ordem cronológica

# Caminho do arquivo Excel único para salvar abas
planilha_resultado_path = os.path.join(os.path.expanduser("~"), "Desktop", "resultados_blaze.xlsx")

# Classificar a cor em número: 0 = branco, 1 = vermelho, 2 = preto
def classificar_cor_num(n):
    if n == 0:
        return 0
    elif 1 <= n <= 7:
        return 1
    else:
        return 2

df_excel['cor_num'] = df_excel['Número'].apply(classificar_cor_num)

# Criar dataset com sequência de jogadas
def gerar_dados(df, sequencia_tamanho):
    X, y = [], []
    for i in range(len(df) - sequencia_tamanho):
        X.append(df['cor_num'].iloc[i:i+sequencia_tamanho].tolist())
        y.append(df['cor_num'].iloc[i+sequencia_tamanho])
    return pd.DataFrame(X), pd.Series(y)

# Modelos
modelos = {
    'Random Forest': RandomForestClassifier(n_estimators=100),
    'KNN': KNeighborsClassifier(),
    'Logistic Regression': LogisticRegression(max_iter=1000),
    'Gradient Boosting': GradientBoostingClassifier(),
    'Decision Tree': DecisionTreeClassifier(),
    'MLP Classifier': MLPClassifier(max_iter=1000)
}

# Diretório para armazenar os modelos
modelos_dir = os.path.join(os.path.expanduser("~"), "Desktop", "modelos treinados completos")
os.makedirs(modelos_dir, exist_ok=True)

modelos_treinados = {}
acertos = {}
erros = {}
total_jogadas = {}
pending_preds = {}
resultados_dfs = {}

# Função para treinar ou carregar modelos
def carregar_ou_treinar_modelos(sequencia_tamanho):
    X_train, y_train = gerar_dados(df_excel, sequencia_tamanho)
    treinados = {}
    for nome, modelo in modelos.items():
        chave = f"{nome} ({sequencia_tamanho})"
        caminho_modelo = os.path.join(modelos_dir, f"{chave}.pkl")
        if os.path.exists(caminho_modelo):
            treinados[chave] = joblib.load(caminho_modelo)
        else:
            modelo.fit(X_train, y_train)
            joblib.dump(modelo, caminho_modelo)
            treinados[chave] = modelo
        acertos[chave] = 0
        erros[chave] = 0
        total_jogadas[chave] = 0
        resultados_dfs[chave] = pd.DataFrame(columns=["Hora", "Modelo", "Previsao", "Cor Real", "Resultado", "Resultado Gale"])
    return treinados

print("🔁 Carregando ou treinando modelos...")
modelos_treinados.update(carregar_ou_treinar_modelos(5))
modelos_treinados.update(carregar_ou_treinar_modelos(100))
print("✅ Modelos prontos para uso.")

ultima_rodada_id = None

print("\n🎯 Iniciando monitoramento da Blaze...")
while True:
    try:
        url = "https://blaze.bet.br/api/singleplayer-originals/originals/roulette_games/recent/history/1"
        response = requests.get(url)
        data = response.json()
        registros = data['records'][:100]
        df_api = pd.DataFrame(registros)
        df_api['cor_num'] = df_api['roll'].apply(classificar_cor_num)

        rodada_atual = df_api.iloc[0]['id']

        if rodada_atual != ultima_rodada_id:
            hora = datetime.now().strftime("%H:%M:%S")
            ultima_rodada_id = rodada_atual
            cor_real = df_api.iloc[0]['cor_num']

            print(f"\n🕒 {hora} | 🎲 Cor atual: {cor_real} ({['BRANCO', 'VERMELHO', 'PRETO'][cor_real]})")

            for chave, info in pending_preds.items():
                total_jogadas[chave] += 1
                if info['previsao'] == cor_real:
                    acertos[chave] += 1
                    resultado = "Acerto"
                    resultado_gale = ""
                else:
                    erros[chave] += 1
                    resultado = "Erro"
                    resultado_gale = ""
                resultados_dfs[chave].loc[len(resultados_dfs[chave])] = [hora, chave, info['previsao'], cor_real, resultado, resultado_gale]

            pending_preds = {}

            for seq_tam in [5, 100]:
                if len(df_api) >= seq_tam:
                    ultimos_n = df_api['cor_num'].iloc[:seq_tam][::-1].tolist()
                    entrada = [ultimos_n]

                    for chave, modelo in modelos_treinados.items():
                        if f"({seq_tam})" in chave:
                            try:
                                if hasattr(modelo, 'n_features_in_') and len(entrada[0]) != modelo.n_features_in_:
                                    continue
                                previsao = modelo.predict(entrada)[0]
                                pending_preds[chave] = {'previsao': previsao}

                                total_tentativas = total_jogadas.get(chave, 0)
                                taxa = (acertos[chave]) / total_tentativas * 100 if total_tentativas else 0.0
                                print(f"📈 {chave} => Previsão: {['BRANCO', 'VERMELHO', 'PRETO'][previsao]} | Assertividade: {taxa:.2f}% | Total: {total_tentativas} | Acertos: {acertos[chave]} | Erros: {erros[chave]}")
                            except Exception as e:
                                print(f"⚠️ Erro na previsão com {chave}: {e}")

            # Salvar resultados no Excel com várias abas
            with pd.ExcelWriter(planilha_resultado_path, engine="openpyxl", mode="w") as writer:
                for chave, df_result in resultados_dfs.items():
                    aba = chave.replace(":", "-").replace("/", "-")[:31]  # Limite de 31 caracteres
                    df_result.to_excel(writer, sheet_name=aba, index=False)
                    from openpyxl.utils import get_column_letter

                    worksheet = writer.sheets[aba]

                    # Inserir fórmula na coluna F, a partir da linha 2 até a última linha do DataFrame
                    for row in range(2, len(df_result) + 2):
                        formula = f'=SE(E{row}="Erro";SE(C{row}=D{row+1};"Acerto G1";"Erro G1");"")'
                        worksheet[f'F{row}'] = formula

                    # Inserir fórmula final de desempenho com penalidade
                    linha_fim = len(df_result) + 3
                    worksheet[f'A{linha_fim}'] = '=CONT.SES(F:F,"Acerto G1") + CONT.SES(E:E,"Acerto") - (CONT.SES(F:F,"Erro G1") * 3)'


                    time.sleep(1)

    except Exception as e:
        print(f"⚠️ Erro: {e}")
        time.sleep(5)
