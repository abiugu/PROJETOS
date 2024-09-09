import pandas as pd
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, f1_score
from ta.momentum import RSIIndicator
from ta.volume import VolumePriceTrendIndicator
import pandas_ta as ta
import numpy as np
import GerenciamentoRisco as gr
from datetime import datetime, timedelta
import logging
import time
from imblearn.over_sampling import SMOTE
from requests.exceptions import ReadTimeout
from ccxt.base.errors import RequestTimeout
import joblib

# Configurando o logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_historical_data(exchange, symbol, timeframe, years=5, retries=5, timeout=30):
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=years*365)
    
    all_bars = []
    since = int(start_time.timestamp() * 1000)

    while True:
        try:
            bars = exchange.fetch_ohlcv(symbol=symbol, timeframe=timeframe, since=since, limit=500, params={'timeout': timeout})
            if not bars:
                break
            all_bars.extend(bars)
            since = bars[-1][0]
            time.sleep(1)  # Prevenção contra limite de chamadas à API
            if pd.to_datetime(bars[-1][0], unit='ms') >= end_time:
                break
        except (RequestTimeout, ReadTimeout) as e:
            logging.warning(f"Timeout ocorreu: {e}. Tentando novamente...")
            retries -= 1
            if retries <= 0:
                raise e
            time.sleep(5)  # Espera antes de tentar novamente

    df_candles = pd.DataFrame(all_bars, columns=['time', 'abertura', 'max', 'min', 'fechamento', 'volume'])
    df_candles['time'] = pd.to_datetime(df_candles['time'], unit='ms', utc=True).map(lambda x: x.tz_convert('America/Sao_Paulo'))

    return df_candles

# Coletar dados históricos para treino
df_candles = fetch_historical_data(gr.binance, 'BTCUSDT', '15m')

# Calcular indicadores técnicos e preparar os dados
rsi = RSIIndicator(df_candles['fechamento'])
df_candles['RSI'] = rsi.rsi()

bbands = ta.bbands(df_candles['fechamento'], length=20, std=2)
bbands = bbands.iloc[:, [0, 1, 2]]
bbands.columns = ['BBL', 'BBM', 'BBU']
bbands['largura'] = (bbands['BBU'] - bbands['BBL']) / bbands['BBM']
df_candles['EMA26'] = ta.ema(df_candles['fechamento'], length=26)
df_candles = pd.concat([df_candles, bbands], axis=1)

vpt = VolumePriceTrendIndicator(close=df_candles['fechamento'], volume=df_candles['volume'])
df_candles['VPT'] = vpt.volume_price_trend()

# Ajustar os critérios de geração de sinais
df_candles['long_signal'] = ((df_candles['fechamento'] < df_candles['BBL']) & 
                             (df_candles['RSI'] < 35) &  # Ajustando RSI para 40
                             (df_candles['VPT'] > df_candles['VPT'].shift(1))).astype(int)

df_candles['short_signal'] = ((df_candles['fechamento'] > df_candles['BBU']) & 
                              (df_candles['RSI'] > 65) &  # Ajustando RSI para 60
                              (df_candles['VPT'] < df_candles['VPT'].shift(1))).astype(int)

# Definir o target como 1 (long) ou -1 (short)
df_candles['target'] = df_candles['long_signal'] - df_candles['short_signal']

# Remover NaNs
df_candles.dropna(inplace=True)

# Mapear as classes: -1 -> 0, 0 -> 1, 1 -> 2
target_mapped = df_candles['target'].map({-1: 0, 0: 1, 1: 2})

# Preparar os dados
features = df_candles[['RSI', 'BBL', 'BBM', 'EMA26', 'BBU', 'largura', 'VPT']]
X_train, X_test, y_train, y_test = train_test_split(features, target_mapped, test_size=0.2, shuffle=False)

# Normalizar os dados
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Aplicar SMOTE para balanceamento das classes
smote = SMOTE(random_state=42)
X_resampled, y_resampled = smote.fit_resample(X_train_scaled, y_train)

# Treinar o modelo XGBoost
model = XGBClassifier(n_estimators=100, random_state=42, use_label_encoder=False, eval_metric='mlogloss')
model.fit(X_resampled, y_resampled)

# Avaliar o modelo
y_pred = model.predict(X_test_scaled)

# Salvar o modelo treinado
joblib.dump(model, 'xgboost_model.pkl')
print("Modelo salvo como 'xgboost_model.pkl'")

# Reverter o mapeamento das classes para a interpretação original
y_pred_original = pd.Series(y_pred).map({0: -1, 1: 0, 2: 1})
y_test_original = y_test.map({0: -1, 1: 0, 2: 1})

# Avaliar o modelo com as classes originais
accuracy = accuracy_score(y_test_original, y_pred_original)
f1 = f1_score(y_test_original, y_pred_original, average='weighted')

# Importância das features
importances = model.feature_importances_
feature_names = features.columns
for name, importance in zip(feature_names, importances):
    print(f'{name}: {importance:.2f}')

# Verificando o balanceamento das classes
class_distribution = df_candles['target'].value_counts()
print("Distribuição das classes:")
print(class_distribution)

print(f"Acurácia: {accuracy:.2f}")
print(f"F1-Score: {f1:.2f}")
