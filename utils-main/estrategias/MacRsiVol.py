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

        await gr.fecha_pnl(symbol, k.loss, k.target, send_message, '15m')

        total_usdt = 20
        leverage = 30
        capital_usado = total_usdt * leverage

        ticker = exchange.fetch_ticker(symbol)
        current_price = ticker['last']
        amount = capital_usado / current_price
        amount = exchange.amount_to_precision(symbol, amount)
        posicao_max = float(amount) * 2

        timeframe = '15m'
        bars = exchange.fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit=100)
        df_candles = pd.DataFrame(bars, columns=['time', 'open', 'max', 'min', 'close', 'volume'])
        df_candles['time'] = pd.to_datetime(df_candles['time'], unit='ms', utc=True).map(lambda x: x.tz_convert('America/Sao_Paulo'))

        df = df_candles

        # stoch = ta.stoch()

        macd = ta.macd(df['close'], fast=12, slow=26, signal=9)
        df['MACD'] = macd['MACD_12_26_9']
        df['Signal'] = macd['MACDs_12_26_9']

        # Calculate RSI using pandas_ta
        df['RSI'] = ta.rsi(df['close'], length=14)

        # Calculate Volume moving average
        df['Volume_Mean'] = df['volume'].rolling(window=20).mean()
        
        # Condições de entrada para Long
        if (df['MACD'].iloc[-1] > df['Signal'].iloc[-1]) & (df['RSI'].iloc[-1] < 35) & (df['volume'].iloc[-1] > df['Volume_Mean'].iloc[-1]):
            if not gr.posicao_max(symbol, posicao_max) and gr.posicoes_abertas(symbol)[0] != 'short' and not gr.ultima_ordem_aberta(symbol):
                try:
                    exchange.create_order(symbol=symbol, side='buy', type='market', amount=amount, params={'hedged': 'true'})
                    message = f"******* ABRINDO LONG DE {amount} MOEDAS EM {symbol} BBMAC !*******"
                    logger.info(message)
                    await send_message(message)
                except Exception as e:
                    error_message = f"******* PROBLEMA AO ABRIR LONG: {e} *******"
                    logger.error(error_message)

        # Condições de entrada para Short
        elif (df['RSI'].iloc[-1] > 70) & (df['MACD'].iloc[-1] < df['Signal'].iloc[-1]) & (df['volume'].iloc[-1] < df['Volume_Mean'].iloc[-1]):
            if not gr.posicao_max(symbol, posicao_max) and gr.posicoes_abertas(symbol)[0] != 'long' and not gr.ultima_ordem_aberta(symbol):
                try:
                    exchange.create_order(symbol=symbol, side='sell', type='market', amount=amount, params={'hedged': 'true'})
                    message = f"******* ABRINDO SHORT DE {amount} MOEDAS EM {symbol} BBMAC!*******"
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
