import logging
import pandas as pd
import pandas_ta as ta
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

        # Calcular EMAs
        df_candles['EMA_9'] = ta.ema(df_candles['Close'], length=9)
        df_candles['EMA_21'] = ta.ema(df_candles['Close'], length=21)

        # Verificar cruzamento de EMAs para sinais de compra e venda
        df_candles['crossover'] = df_candles['EMA_9'] - df_candles['EMA_21']
        df_candles['crossover_shift'] = df_candles['crossover'].shift(1)

        # Verifica apenas um sinal de cada vez
        df_candles['compra'] = (df_candles['crossover'] > 0) & (df_candles['crossover_shift'] <= 0) & (df_candles['Volume'] > df_candles['Volume'].shift(1))
        df_candles['venda'] = (df_candles['crossover'] < 0) & (df_candles['crossover_shift'] >= 0) & (df_candles['Volume'] > df_candles['Volume'].shift(1))

        last_row = df_candles.iloc[-1]
        # Lógica para impedir execução simultânea de compra e venda
        if last_row['compra']:
            # Verifica se não há uma venda em andamento
            if not gr.posicao_max(symbol, posicao_max) and gr.posicoes_abertas(symbol)[0] != 'short' and not gr.ultima_ordem_aberta(symbol):
                try:
                    exchange.create_order(symbol=symbol, side='buy', type='market', amount=amount, params={'hedged': 'true'})
                    message = f"******* ABRINDO LONG DE {amount} MOEDAS EM {symbol}! *******"
                    logger.info(message)
                    await send_message(message)
                except Exception as e:
                    error_message = f"******* PROBLEMA AO ABRIR LONG: {e} *******"
                    logger.error(error_message)
                    await send_message(error_message)
        elif last_row['venda']:
            # Verifica se não há uma compra em andamento
            if not gr.posicao_max(symbol, posicao_max) and gr.posicoes_abertas(symbol)[0] != 'long' and not gr.ultima_ordem_aberta(symbol):
                try:
                    exchange.create_order(symbol=symbol, side='sell', type='market', amount=amount, params={'hedged': 'true'})
                    message = f"******* ABRINDO SHORT DE {amount} MOEDAS EM {symbol}! *******"
                    logger.info(message)
                    await send_message(message)
                except Exception as e:
                    error_message = f"******* PROBLEMA AO ABRIR SHORT: {e} *******"
                    logger.error(error_message)
                    await send_message(error_message)
        else:
            logger.info('Nada para fazer')
            # await send_message('Nada para fazer')

    except Exception as e:
        logger.error(f"Erro na estratégia {symbol}: {e}")
        await send_message(f"Erro na estratégia {symbol}: {e}")
