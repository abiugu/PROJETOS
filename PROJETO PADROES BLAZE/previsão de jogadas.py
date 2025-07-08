import pandas as pd
import requests
import time
import os
import joblib
import re
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier

# Caminho do Excel no Desktop
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", "historico blaze.xlsx")
df_excel = pd.read_excel(desktop_path)

# Função para classificar a cor das jogadas
def classificar_cor_num(n):
    if n == 0:
        return 0  # Branco
    elif 1 <= n <= 7:
        return 1  # Vermelho
    else:
        return 2  # Preto

df_excel['cor_num'] = df_excel['Número'].apply(classificar_cor_num)

# Caminho do arquivo Excel único para salvar abas
planilha_resultado_path = os.path.join(os.path.expanduser("~"), "Desktop", "resultados_blaze.xlsx")

# Criar dataset com sequência de jogadas
def gerar_dados(df, sequencia_tamanho):
    X, y = [], []
    for i in range(len(df) - sequencia_tamanho):
        X.append(df['cor_num'].iloc[i:i+sequencia_tamanho].tolist())
        y.append(df['cor_num'].iloc[i+sequencia_tamanho])
    return pd.DataFrame(X), pd.Series(y)

# Função para limpar nomes de abas do Excel
def limpar_nome_aba(nome):
    return re.sub(r'[:\\/*?\[\]]', '-', nome)[:31]

# Modelos
modelos = {
    'Random Forest': RandomForestClassifier(n_estimators=100),
}

# Diretório para armazenar os modelos
modelos_dir = os.path.join(os.path.expanduser("~"), "Desktop", "modelos treinados completo")
os.makedirs(modelos_dir, exist_ok=True)

modelos_treinados = {}
acertos = {}
erros = {}
total_jogadas = {}
pending_preds = {}
resultados_dfs = {}

# Função para treinar ou carregar modelos (ambas direções)
def carregar_ou_treinar_modelos(sequencia_tamanho, modo="normal"):
    df_base = df_excel if modo == "normal" else df_excel[::-1]
    X_train, y_train = gerar_dados(df_base, sequencia_tamanho)
    treinados = {}
    for nome, modelo in modelos.items():
        chave = f"{nome} ({sequencia_tamanho}) [{modo}]"
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
        resultados_dfs[chave] = pd.DataFrame(columns=["Hora", "Modelo", "Previsao", "Cor Real", "Resultado", "Resultado Gale", "Confianca"])
    return treinados

# Carregar ou treinar modelos
print("🔁 Carregando ou treinando modelos...")
for modo in ["normal", "invertido"]:
    modelos_treinados.update(carregar_ou_treinar_modelos(50, modo))
    modelos_treinados.update(carregar_ou_treinar_modelos(100, modo))
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

        # Atualiza o DataFrame principal com as últimas 100 rodadas da API
        df_excel = pd.concat([df_excel, df_api[['cor_num']].reset_index(drop=True)], ignore_index=True)

        rodada_atual = df_api.iloc[0]['id']

        if rodada_atual != ultima_rodada_id:
            hora = datetime.now().strftime("%H:%M:%S")
            ultima_rodada_id = rodada_atual
            cor_real = df_api.iloc[0]['cor_num']

            print(f"\n🕒 {hora} | 🎲 Cor atual: {cor_real} ({['BRANCO', 'VERMELHO', 'PRETO'][cor_real]})")

            # Verificando a previsão com os modelos
            for chave, info in pending_preds.items():
                total_jogadas[chave] += 1
                if info['previsao'] == cor_real or cor_real == 0:
                    acertos[chave] += 1
                    resultado = "Acerto"
                    resultado_gale = ""
                else:
                    erros[chave] += 1
                    resultado = "Erro"
                    resultado_gale = ""
                resultados_dfs[chave].loc[len(resultados_dfs[chave])] = [hora, chave, info['previsao'], cor_real, resultado, resultado_gale, info.get('confianca')]

            pending_preds = {}

            # Previsão com os modelos
            for seq_tam in [50, 100]:
                if len(df_excel) >= seq_tam:
                    for chave, modelo in modelos_treinados.items():
                        if f"({seq_tam})" in chave:
                            try:
                                is_invertido = "[invertido]" in chave
                                dados_base = df_excel['cor_num'].iloc[-seq_tam:]  # Usar as últimas 'seq_tam' rodadas
                                entrada = [dados_base[::-1].tolist() if is_invertido else dados_base.tolist()]

                                if hasattr(modelo, 'n_features_in_') and len(entrada[0]) != modelo.n_features_in_:
                                    continue
                                if hasattr(modelo, "predict_proba"):
                                    proba = modelo.predict_proba(entrada)[0]
                                    previsao = proba.argmax()
                                    confianca = proba[previsao]
                                else:
                                    previsao = modelo.predict(entrada)[0]
                                    confianca = None
                                pending_preds[chave] = {'previsao': previsao, 'confianca': confianca}

                                total_tentativas = total_jogadas.get(chave, 0)
                                taxa = (acertos[chave]) / total_tentativas * 100 if total_tentativas else 0.0
                                cor_nome = ['BRANCO', 'VERMELHO', 'PRETO'][previsao]
                                if confianca is not None:
                                    print(f"📈 {chave} => Previsão: {cor_nome} | Força: {confianca*100:.1f}% | Assertividade: {taxa:.2f}% | Total: {total_tentativas} | Acertos: {acertos[chave]} | Erros: {erros[chave]}")
                                else:
                                    print(f"📈 {chave} => Previsão: {cor_nome} | Assertividade: {taxa:.2f}% | Total: {total_tentativas} | Acertos: {acertos[chave]} | Erros: {erros[chave]}")
                            except Exception as e:
                                print(f"⚠️ Erro na previsão com {chave}: {e}")

            # Salvar resultados no Excel com várias abas
            with pd.ExcelWriter(planilha_resultado_path, engine="openpyxl", mode="w") as writer:
                for chave, df_result in resultados_dfs.items():
                    aba = limpar_nome_aba(chave)
                    df_result.to_excel(writer, sheet_name=aba, index=False)

                    from openpyxl.utils import get_column_letter
                    worksheet = writer.sheets[aba]
                    linha_fim = len(df_result) + 3
                    worksheet[f'A{linha_fim}'] = "Desempenho Final:"
                    worksheet[f'B{linha_fim}'] = "=CONT.SES(E:E,\"Acerto\") - CONT.SES(E:E,\"Erro\")"

        time.sleep(1)

    except Exception as e:
        print(f"⚠️ Erro: {e}")
        time.sleep(5)
