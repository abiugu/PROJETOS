import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error
from statsmodels.tsa.arima.model import ARIMA
import random
import tensorflow as tf
import tkinter as tk
from tkinter import messagebox
from pmdarima import auto_arima

Adam = tf.keras.optimizers.Adam
Sequential = tf.keras.models.Sequential
Dense = tf.keras.layers.Dense
LSTM = tf.keras.layers.LSTM
Dropout = tf.keras.layers.Dropout

def carregar_dados(arquivo):
    df = pd.read_excel(arquivo)
    df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
    df = df.sort_values(by='data').reset_index(drop=True)
    return df

def preparar_dados_lstm(df, seq_length=10):
    scaler = MinMaxScaler(feature_range=(0, 1))
    df['numero'] = scaler.fit_transform(df[['numero']])
    
    X, y = [], []
    for i in range(len(df) - seq_length):
        X.append(df['numero'].iloc[i:i + seq_length].values)
        y.append(df['numero'].iloc[i + seq_length])
    
    X, y = np.array(X), np.array(y)
    X = np.reshape(X, (X.shape[0], X.shape[1], 1))
    
    return X, y, scaler

def treinar_lstm(X_train, y_train, epochs=20, batch_size=64):
    model = Sequential([
        LSTM(100, return_sequences=True, input_shape=(X_train.shape[1], X_train.shape[2]))
        , Dropout(0.3), LSTM(50), Dense(50, activation='relu'), Dense(1, activation='linear')
    ])
    
    model.compile(optimizer=Adam(learning_rate=0.001), loss='mse')
    model.fit(X_train, y_train, epochs=epochs, batch_size=batch_size, verbose=1)
    return model

def prever_lstm(model, X_test, scaler):
    previsoes = model.predict(X_test)
    return scaler.inverse_transform(previsoes.reshape(-1, 1))

def modelo_markov(df):
    transicoes = {}
    for i in range(len(df) - 1):
        estado_atual = df.iloc[i]['numero']
        proximo_estado = df.iloc[i + 1]['numero']
        if estado_atual not in transicoes:
            transicoes[estado_atual] = []
        transicoes[estado_atual].append(proximo_estado)
    return transicoes

def prever_markov(transicoes, estado_atual, n=5):
    if estado_atual in transicoes:
        return random.choices(transicoes[estado_atual], k=n)
    return random.sample(list(transicoes.keys()), min(n, len(transicoes)))

def modelo_arima(df):
    model = auto_arima(df['numero'], seasonal=False, stepwise=True, suppress_warnings=True)
    return model.fit(df['numero'])

def prever_arima(model_fit, steps=5):
    return model_fit.predict(n_periods=steps)

def avaliar_previsoes(real, previsto):
    return mean_absolute_error(real, previsto)

def mostrar_resultados(acuracia_lstm, acuracia_markov, acuracia_arima):
    root = tk.Tk()
    root.withdraw()
    
    msg = f"""
    **Resultados da Análise**
    
    - Erro Médio Absoluto LSTM: {acuracia_lstm:.2f}
    - Erro Médio Absoluto Markov: {acuracia_markov:.2f}
    - Erro Médio Absoluto ARIMA: {acuracia_arima:.2f}
    """
    messagebox.showinfo("Análise Concluída", msg)

if __name__ == "__main__":
    df = carregar_dados("historico blaze.xlsx")
    X, y, scaler = preparar_dados_lstm(df)
    
    split = int(0.8 * len(X))
    X_train, y_train = X[:split], y[:split]
    X_test, y_test = X[split:], y[split:]
    
    print("Treinando LSTM...")
    model_lstm = treinar_lstm(X_train, y_train)
    previsoes_lstm = prever_lstm(model_lstm, X_test, scaler)
    
    print("Treinando modelo de Markov...")
    transicoes = modelo_markov(df)
    previsoes_markov = prever_markov(transicoes, df.iloc[-1]['numero'])
    
    print("Treinando modelo ARIMA...")
    model_arima_fit = modelo_arima(df)
    previsoes_arima = prever_arima(model_arima_fit)
    
    print("Avaliando modelos...")
    acuracia_lstm = avaliar_previsoes(y_test.flatten(), previsoes_lstm.flatten())
    acuracia_markov = avaliar_previsoes(df['numero'][-len(previsoes_markov):], previsoes_markov)
    acuracia_arima = avaliar_previsoes(df['numero'][-len(previsoes_arima):], previsoes_arima)
    
    mostrar_resultados(acuracia_lstm, acuracia_markov, acuracia_arima)
