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

        await gr.fecha_pnl(symbol, 10, 20, send_message, '1m')

        total_usdt = 20
        leverage = 30
        capital_usado = total_usdt * leverage

        ticker = exchange.fetch_ticker(symbol)
        current_price = ticker['last']
        amount = capital_usado / current_price
        amount = exchange.amount_to_precision(symbol, amount)
        posicao_max = float(amount) * 2

        timeframe = '1m'
        bars = exchange.fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit=100)
        df_candles = pd.DataFrame(bars, columns=['time', 'Open', 'High', 'Low', 'Close', 'Volume'])
        df_candles['time'] = pd.to_datetime(df_candles['time'], unit='ms', utc=True).map(lambda x: x.tz_convert('America/Sao_Paulo'))

                # Calculate the 50 EMA and 100 EMA
        df_candles['EMA_50'] = ta.ema(df_candles['Close'], length=50)
        df_candles['EMA_100'] = ta.ema(df_candles['Close'], length=100)

        # Calculate the Stochastic Oscillator with settings (3, 2, 2)
        stoch = ta.stoch(df_candles['High'], df_candles['Low'], df_candles['Close'], k=3, d=2, smooth_k=2)
        df_candles['Stoch_K'] = stoch['STOCHk_3_2_2']
        df_candles['Stoch_D'] = stoch['STOCHd_3_2_2']

        tolerancia = 0.01  
        df_candles['Signal'] = 0  
        for i in range(1, len(df_candles)):
            if (df_candles['EMA_50'].iloc[i-1] > df_candles['EMA_100'].iloc[i-1]) and \
            (df_candles['EMA_50'].iloc[i-2] <= df_candles['EMA_100'].iloc[i-2]):  
                
                if (abs(df_candles['Close'].iloc[i-1] - df_candles['EMA_50'].iloc[i-1]) / df_candles['EMA_50'].iloc[i-1] <= tolerancia or \
                    abs(df_candles['Close'].iloc[i-1] - df_candles['EMA_100'].iloc[i-1]) / df_candles['EMA_100'].iloc[i-1] <= tolerancia) and \
                (df_candles['Stoch_K'].iloc[i-1] > 20): 
                    df_candles.at[i, 'Signal'] = 1  
            elif (df_candles['EMA_50'].iloc[i-1] < df_candles['EMA_100'].iloc[i-1]) and \
                (df_candles['EMA_50'].iloc[i-2] >= df_candles['EMA_100'].iloc[i-2]):  
                if (abs(df_candles['Close'].iloc[i-1] - df_candles['EMA_50'].iloc[i-1]) / df_candles['EMA_50'].iloc[i-1] <= tolerancia or \
                    abs(df_candles['Close'].iloc[i-1] - df_candles['EMA_100'].iloc[i-1]) / df_candles['EMA_100'].iloc[i-1] <= tolerancia) and \
                (df_candles['Stoch_K'].iloc[i-1] < 80):  
                    df_candles.at[i, 'Signal'] = -1 
                  
        if df_candles['Signal'].iloc[-1] == 1:
              if not gr.posicao_max(symbol, posicao_max) and gr.posicoes_abertas(symbol)[0] != 'short' and not gr.ultima_ordem_aberta(symbol):
                try:
                    exchange.create_order(symbol=symbol, side='buy', type='market', amount=amount, params={'hedged': 'true'})
                    message = f"******* ABRINDO LONG DE {amount} MOEDAS EM {symbol} 5T !*******"
                    logger.info(message)
                    await send_message(message)
                except Exception as e:
                    error_message = f"******* PROBLEMA AO ABRIR LONG: {e} *******"
                    logger.error(error_message)
        elif df_candles['Signal'].iloc[-1] == -1:
               if not gr.posicao_max(symbol, posicao_max) and gr.posicoes_abertas(symbol)[0] != 'long' and not gr.ultima_ordem_aberta(symbol):
                try:
                    exchange.create_order(symbol=symbol, side='sell', type='market', amount=amount, params={'hedged': 'true'})
                    message = f"******* ABRINDO SHORT DE {amount} MOEDAS EM {symbol} 5T!*******"
                    logger.info(message)
                    await send_message(message)
                except Exception as e:
                    error_message = f"******* PROBLEMA AO ABRIR SHORT: {e} *******"
                    logger.error(error_message)
        else:
            logger.info('Nada para fazer')
            # await send_message('Nada para fazer')
    
    except Exception as e:
        logger.error(f"Erro na estratégia {symbol}: {e}")
        await send_message(f"Erro na estratégia {symbol}: {e}")
