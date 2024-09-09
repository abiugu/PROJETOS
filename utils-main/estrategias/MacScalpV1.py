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

        timeframe = '5m'
        bars = exchange.fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit=100)
        df_candles = pd.DataFrame(bars, columns=['time', 'open', 'max', 'min', 'close', 'volume'])
        df_candles['time'] = pd.to_datetime(df_candles['time'], unit='ms', utc=True).map(lambda x: x.tz_convert('America/Sao_Paulo'))

        macd_df = ta.macd(df_candles['close'], fast=12, slow=26, signal=9)
        df_candles['MACD'] = macd_df['MACD_12_26_9']
        df_candles['Signal'] = macd_df['MACDs_12_26_9']
        df_candles['RSI'] = ta.rsi(df_candles['close'], length=14)

        stoch = ta.stoch(df_candles['max'], df_candles['min'], df_candles['close'], k=14, smooth_k=3)
        df_candles['stochK'] = stoch['STOCHk_14_3_3']
        df_candles['stochD'] = stoch['STOCHd_14_3_3']
        df_candles['Volume_Mean'] = df_candles['volume'].rolling(window=30).mean()

        # RSI cruzando a linha de 50
        rsi_cruzando_50 = df_candles['RSI'].iloc[-2] < 50 and df_candles['RSI'].iloc[-1] > 50
        rsi_cruzando_50_baixo = df_candles['RSI'].iloc[-2] > 50 and df_candles['RSI'].iloc[-1] < 50

        # MACD dando sinal de compra (MACD cruzando acima da linha de sinal)
        macd_compra = df_candles['MACD'].iloc[-2] <= df_candles['Signal'].iloc[-2] and df_candles['MACD'].iloc[-1] > df_candles['Signal'].iloc[-1]
        macd_venda = df_candles['MACD'].iloc[-2] >= df_candles['Signal'].iloc[-2] and df_candles['MACD'].iloc[-1] < df_candles['Signal'].iloc[-1]

        # Stochastic saindo da região de sobrevenda (abaixo de 35)
        stoch_sobrevendido = df_candles['stochK'].iloc[-1] < 35
        stoch_sobrecompra = df_candles['stochK'].iloc[-1] > 65

        # Volume crescente (volume atual maior que a média móvel do volume)
        volume_crescente = df_candles['volume'].iloc[-1] > df_candles['Volume_Mean'].iloc[-1]

        # Verificar todas as condições
        if rsi_cruzando_50 and macd_compra and stoch_sobrevendido and volume_crescente:
              if not gr.posicao_max(symbol, posicao_max) and gr.posicoes_abertas(symbol)[0] != 'short' and not gr.ultima_ordem_aberta(symbol):
                try:
                    exchange.create_order(symbol=symbol, side='buy', type='market', amount=amount, params={'hedged': 'true'})
                    message = f"******* ABRINDO LONG DE {amount} MOEDAS EM {symbol} macRSi !*******"
                    logger.info(message)
                    await send_message(message)
                except Exception as e:
                    error_message = f"******* PROBLEMA AO ABRIR LONG: {e} *******"
                    logger.error(error_message)
        elif rsi_cruzando_50_baixo and macd_venda and stoch_sobrecompra and volume_crescente:
               if not gr.posicao_max(symbol, posicao_max) and gr.posicoes_abertas(symbol)[0] != 'long' and not gr.ultima_ordem_aberta(symbol):
                try:
                    exchange.create_order(symbol=symbol, side='sell', type='market', amount=amount, params={'hedged': 'true'})
                    message = f"******* ABRINDO SHORT DE {amount} MOEDAS EM {symbol} macRSi!*******"
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


