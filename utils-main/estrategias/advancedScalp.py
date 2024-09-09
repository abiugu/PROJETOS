import logging
import pandas as pd
import pandas_ta as ta
import asyncio
import GerenciamentoRisco as gr
import config.config as k
import joblib
import os

# Configuração de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Classe para carregar e usar o modelo treinado
class PricePredictor:
    def __init__(self, model=None):
        self.model = model

    def predict(self, latest_data):
        X = latest_data[['Open', 'High', 'Low', 'Close', 'Volume', 'volatility', 'rsi', 'ema']].values[-1:]
        return self.model.predict(X)[0]

async def startStrategy(symbol, send_message, model_filename='eth_price_predictor_model.pkl'):
    try:
        exchange = gr.binance

        await gr.fecha_pnl(symbol, send_message=send_message, timeframe='5m', loss=10, target=20)
        logger.info(f"Position checked and managed for {symbol}")

        # Capital e alavancagem
        total_usdt = 30  # Capital reduzido para minimizar risco e carga na VPS
        leverage = 10
        capital_usado = total_usdt * leverage

        # Função para obter o preço atual
        ticker = exchange.fetch_ticker(symbol)
        current_price = ticker['last']
        amount = 300 / current_price
        amount = exchange.amount_to_precision(symbol, amount)

        # Obter dados de mercado
        timeframe = '1m'
        bars = exchange.fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit=100)
        df = pd.DataFrame(bars, columns=['Time', 'Open', 'High', 'Low', 'Close', 'Volume'])

        # Carregar o modelo treinado
        if os.path.exists(model_filename):
            loaded_model = joblib.load(model_filename)
            predictor = PricePredictor(model=loaded_model)
            logger.info(f"Modelo carregado de {model_filename}")
        else:
            logger.error(f"Modelo {model_filename} não encontrado. Execute o treinamento primeiro.")
            return

        # Atualizar indicadores técnicos
        df['volatility'] = df['Close'].rolling(window=10).std()  # Volatilidade
        df['rsi'] = ta.rsi(df['Close'], length=14)  # RSI
        df['ema'] = df['Close'].ewm(span=12, adjust=False).mean()  # Média móvel exponencial
  
        df = df.dropna()  # Garantir que não haja NaN antes de fazer a previsão

        # Previsão de movimento de preço
        prediction = predictor.predict(df)
        last_rsi = df['rsi'].iloc[-1]
        last_close = df['Close'].iloc[-1]
        last_ema = df['ema'].iloc[-1]

        # Estratégia de trading simplificada
        if prediction == 1 and last_rsi < 30 and last_close > last_ema:
            exchange.create_order(symbol=symbol, side='buy', type='market', amount=amount, params={'hedged': 'true'})
            message = f"🚀 Abrindo Long em {symbol} com advancedScalp! Boa sorte! 📈"
            logger.info(message)
            await send_message(message)
        elif prediction == 0 and last_rsi > 70 and last_close < last_ema:
            exchange.create_order(symbol=symbol, side='sell', type='market', amount=amount, params={'hedged': 'true'})
            message = f"🔻 Abrindo Short em {symbol} com advancedScalp! Vamos lá! 📉"
            logger.info(message)
            await send_message(message)

    except Exception as e:
        logger.error(f"Error in strategy execution: {e}")
        await send_message(f"Error in strategy execution: {e}")

