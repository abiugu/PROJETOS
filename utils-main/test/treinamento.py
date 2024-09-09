# treinamento.py

import logging
import pandas as pd
import pandas_ta as ta
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score, train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler
import numpy as np
import joblib

# Configuração de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Função para carregar o CSV, fazer feature engineering e treinar o modelo
def train_model_from_csv(csv_file, model_filename='eth_price_predictor_model.pkl'):
    # Carregar o CSV
    df = pd.read_csv(csv_file)
    
    # Supondo que o CSV tenha as colunas: time, open, high, low, close, volume
    df['future_close'] = df['Close'].shift(-1)
    df = df.dropna()

    # Feature Engineering
    # df['return'] = df['Close'].pct_change()  # Retornos logarítmicos
    df['volatility'] = df['Close'].rolling(window=10).std()  # Volatilidade
    df['rsi'] = ta.rsi(df['Close'], length=14)  # RSI
    df['ema'] = df['Close'].ewm(span=12, adjust=False).mean()  # Média móvel exponencial
  
    # # Corrigir a função bbands para evitar o erro
    # bbands = ta.bbands(df['Close'], length=20, std=2)
    # df['bb_upper'] = bbands['BBU_20_2.0']  # Banda superior
    # df['bb_middle'] = bbands['BBM_20_2.0']  # Banda média
    # df['bb_lower'] = bbands['BBL_20_2.0']  # Banda inferior
    
    df = df.dropna()  # Remover NaN resultantes do cálculo de indicadores

    X = df[['Open', 'High', 'Low', 'Close', 'Volume','volatility', 'rsi','ema']].values
    y = np.where(df['future_close'] > df['Close'], 1, 0)

    # Normalizar as features
    scaler = StandardScaler()
    X = scaler.fit_transform(X)

    # Divisão de dados para validação
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Ajuste de Hiperparâmetros usando GridSearchCV
    param_grid = {
        'n_estimators': [400],
        'max_depth': [20],
        'min_samples_split': [10],
        'min_samples_leaf': [2],
        'bootstrap': [False]
    }
    
    rf = RandomForestClassifier(random_state=42)
    grid_search = GridSearchCV(estimator=rf, param_grid=param_grid, cv=5, n_jobs=-1, verbose=2, scoring='accuracy')
    grid_search.fit(X_train, y_train)
    
    # Melhor modelo obtido pelo GridSearchCV
    best_rf = grid_search.best_estimator_
    logger.info(f"Melhores hiperparâmetros: {grid_search.best_params_}")

    # Avaliar o modelo com os dados de teste
    test_score = best_rf.score(X_test, y_test)
    logger.info(f"Acurácia nos dados de teste: {test_score:.4f}")

    # Salvar o modelo treinado
    joblib.dump(best_rf, model_filename)
    logger.info(f"Modelo salvo em {model_filename}")

if __name__ == "__main__":
    # Exemplo de uso
    csv_file = 'ETH-USD.csv'  # Substitua pelo caminho do seu arquivo CSV
    train_model_from_csv(csv_file)
