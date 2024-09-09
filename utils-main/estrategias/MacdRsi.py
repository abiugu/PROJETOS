import logging
import pandas as pd
import pandas_ta as ta
from ta.momentum import RSIIndicator
from ta.volume import VolumePriceTrendIndicator
import time
import asyncio
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

        
        await gr.fecha_pnl(symbol=symbol,send_message=send_message,timeframe='1h', loss=k.loss, target=k.target)
        # trailing_stop = None  
        total_usdt = k.amount
        leverage = 10
        capital_usado = total_usdt * leverage

        ticker = exchange.fetch_ticker(symbol)
        current_price = ticker['last']
        amount = capital_usado / current_price
        amount = exchange.amount_to_precision(symbol, amount)
        posicao_max = float(amount) * 2

        timeframe = '1h'
        bars = exchange.fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit=100)
        df_candles = pd.DataFrame(bars, columns=['time', 'abertura', 'max', 'min', 'fechamento', 'volume'])
        df_candles['time'] = pd.to_datetime(df_candles['time'], unit='ms', utc=True).map(lambda x: x.tz_convert('America/Sao_Paulo'))

        # Cálculo do RSI
        rsi = RSIIndicator(close=df_candles['fechamento'], window=14)
        df_candles['RSI'] = rsi.rsi()

        macd_df = ta.macd(df_candles['fechamento'], fast=12, slow=26, signal=9)
        df_candles['MACD'] = macd_df['MACD_12_26_9']
        df_candles['Signal'] = macd_df['MACDs_12_26_9']

        if df_candles.iloc[-1]['RSI'] >= 55 and df_candles.iloc[-1]['RSI'] <= 70:
            if df_candles.iloc[-1]['MACD'] >= df_candles.iloc[-1]['Signal'] and df_candles.iloc[-2]['MACD'] <= df_candles.iloc[-2]['Signal']:
                if not gr.posicao_max(symbol, posicao_max) and gr.posicoes_abertas(symbol)[0] != 'short' and not gr.ultima_ordem_aberta(symbol):
                    try:
                        exchange.create_order(symbol=symbol, side='buy', type='market', amount=amount, params={'hedged': 'true'})
                        message = f"🚀 Abrindo Long em {symbol} com MACD! Boa sorte! 📈"
                        logger.info(message)
                        await send_message(message)
                    except:
                        logger.info(f"⚠️ Problema ao abrir Long em {symbol}!")
                        # await send_message(f"⚠️ Problema ao abrir Long em {symbol}!")
        elif df_candles.iloc[-1]['RSI'] <= 45 and df_candles.iloc[-1]['RSI'] >= 30:
            if df_candles.iloc[-1]['MACD'] <= df_candles.iloc[-1]['Signal'] and df_candles.iloc[-2]['MACD'] >= df_candles.iloc[-2]['Signal']:
                if not gr.posicao_max(symbol, posicao_max) and gr.posicoes_abertas(symbol)[0] != 'long' and not gr.ultima_ordem_aberta(symbol):
                    try:
                        exchange.create_order(symbol=symbol, side='sell', type='market', amount=amount, params={'hedged': 'true'})
                        message = f"🔻 Abrindo Short em {symbol} com MACD! Vamos lá! 📉"
                        logger.info(message)
                        await send_message(message)
                    except:
                        logger.info(f"⚠️ Problema ao abrir Short em {symbol}!")
                        # await send_message(f"⚠️ Problema ao abrir Short em {symbol}!")
        else:
            logger.info(f"💤 Sem tendência clara para Long ou Short em {symbol}.")
            # await send_message(f"💤 Sem tendência clara para Long ou Short em {symbol}.")


    except Exception as e:
        logger.error(f"Erro na estratégia {symbol}: {e}")
        await send_message(f"⚠️ Erro na estratégia {symbol}: {e}")