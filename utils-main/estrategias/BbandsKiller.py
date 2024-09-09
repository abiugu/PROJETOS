import logging
import pandas as pd
import pandas_ta as ta
from ta.momentum import RSIIndicator
from ta.volume import VolumePriceTrendIndicator

import time
import GerenciamentoRisco as gr
import config.config as k

# Ativando o logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

async def startStrategy(symbol, send_message):
    try:
        exchange = gr.binance

        await gr.fecha_pnl(symbol, k.loss, k.target, send_message, '5m')

        total_usdt = 20
        leverage = 30
        capital_usado = total_usdt * leverage

        ticker = exchange.fetch_ticker(symbol)
        current_price = ticker['last']
        amount = capital_usado / current_price
        amount = exchange.amount_to_precision(symbol, amount)
        posicao_max = float(amount) * 2
        lookback_periods = 50  # Períodos para calcular a média móvel da largura
        adjustment_factor = 1.0  # Fator de ajuste do threshold

        timeframe = '5m'
        bars = exchange.fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit=100)
        df_candles = pd.DataFrame(bars, columns=['time', 'abertura', 'max', 'min', 'fechamento', 'volume'])
        df_candles['time'] = pd.to_datetime(df_candles['time'], unit='ms', utc=True).map(lambda x: x.tz_convert('America/Sao_Paulo'))

        # Cálculo do RSI
        rsi = RSIIndicator(close=df_candles['fechamento'], window = 13)
        df_candles['RSI'] = rsi.rsi()

        # Cálculo das Bandas de Bollinger
        bbands = ta.bbands(df_candles['fechamento'], length=30, std=2)
        bbands = bbands.iloc[:, [0, 1, 2]]
        bbands.columns = ['BBL', 'BBM', 'BBU']
        bbands['largura'] = (bbands['BBU'] - bbands['BBL']) / bbands['BBM']

        # Concatenando o DataFrame de Bandas de Bollinger com df_candles
        df_candles = pd.concat([df_candles, bbands], axis=1)

        # Cálculo da média da largura das Bandas de Bollinger
        media_largura = df_candles['largura'].rolling(window=lookback_periods).mean()
        threshold = media_largura.iloc[-1] * adjustment_factor

        # Cálculo do Volume Price Trend
        vpt = VolumePriceTrendIndicator(close=df_candles['fechamento'], volume=df_candles['volume'])
        df_candles['VPT'] = vpt.volume_price_trend()

        # Cálculo do ATR
        atr = ta.atr(high=df_candles['max'], low=df_candles['min'], close=df_candles['fechamento'], length=14)
        df_candles['ATR'] = atr

        # Obtendo o preço mais recente
        price = exchange.fetch_trades(symbol)[-1]['price']
        price = float(exchange.price_to_precision(symbol, price))

        # Calculando os níveis baseados no ATR
        df_candles['atr_nivel_superior'] = df_candles['abertura'] + 1.6 * df_candles['ATR']
        df_candles['atr_nivel_inferior'] = df_candles['abertura'] - 1.0 * df_candles['ATR']

        # Condições de entrada para Long
        if (df_candles['largura'].iloc[-1] >= threshold and 
            df_candles['RSI'].iloc[-2] <= 25 and 
            df_candles['fechamento'].iloc[-2] <= df_candles['BBL'].iloc[-2] and 
            price >= df_candles['max'].iloc[-2] and 
            df_candles['VPT'].iloc[-1] > df_candles['VPT'].iloc[-2] and 
            price >= df_candles['atr_nivel_inferior'].iloc[-1] and 
            price <= df_candles['atr_nivel_superior'].iloc[-1]):
            
            if not gr.posicao_max(symbol, posicao_max) and gr.posicoes_abertas(symbol)[0] != 'short' and not gr.ultima_ordem_aberta(symbol):
                try:
                    exchange.create_order(symbol=symbol, side='buy', type='market', amount=amount, params={'hedged': 'true'})
                    message = f"******* ABRINDO LONG DE {amount} MOEDAS EM {symbol} BBANDS !*******"
                    logger.info(message)
                    await send_message(message)
                except Exception as e:
                    error_message = f"******* PROBLEMA AO ABRIR LONG: {e} *******"
                    logger.error(error_message)

        # Condições de entrada para Short
        elif (df_candles['largura'].iloc[-1] >= threshold and 
              df_candles['RSI'].iloc[-2] >= 75 and 
              df_candles['fechamento'].iloc[-2] >= df_candles['BBU'].iloc[-2] and 
              price <= df_candles['min'].iloc[-2] and 
              df_candles['VPT'].iloc[-1] < df_candles['VPT'].iloc[-2] and
              price >= df_candles['atr_nivel_inferior'].iloc[-1] and 
              price <= df_candles['atr_nivel_superior'].iloc[-1]): 
            
            if not gr.posicao_max(symbol, posicao_max) and gr.posicoes_abertas(symbol)[0] != 'long' and not gr.ultima_ordem_aberta(symbol):
                try:
                    exchange.create_order(symbol=symbol, side='sell', type='market', amount=amount, params={'hedged': 'true'})
                    message = f"******* ABRINDO SHORT DE {amount} MOEDAS EM {symbol} BBANDS!*******"
                    logger.info(message)
                    await send_message(message)
                except Exception as e:
                    error_message = f"******* PROBLEMA AO ABRIR SHORT: {e} *******"
                    logger.error(error_message)
        else:
            logger.info('Nada para fazer')

    except Exception as e:
        logger.error(f"Erro na estratégia {symbol}: {e}")
        await send_message(f"Erro na estratégia {symbol}: {e}")
