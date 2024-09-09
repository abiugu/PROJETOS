import logging
import pandas as pd
import pandas_ta as ta
from ta.momentum import RSIIndicator
from ta.volume import VolumePriceTrendIndicator
import time
import GerenciamentoRisco as gr
import config.config as k
from smartmoneyconcepts import smc



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

        timeframe = '15m'
        bars = exchange.fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit=100)
        df_candles = pd.DataFrame(bars, columns=['time','open','high','low','close','volume'])
        df_candles['time'] = pd.to_datetime(df_candles['time'], unit='ms', utc=True).map(lambda x: x.tz_convert('America/Sao_Paulo'))
        
        # Calculate SMC Indicators
        fvg = smc.fvg(df_candles)
        swing_hl = smc.swing_highs_lows(df_candles)
        bos_choch = smc.bos_choch(df_candles, swing_hl)
        order_blocks = smc.ob(df_candles, swing_hl)
        liquidity = smc.liquidity(df_candles, swing_hl)


        if bos_choch['CHOCH'].iloc[-1] == 1 and order_blocks['OB'].iloc[-1] == 1 and liquidity['Liquidity'].iloc[-1] == 1:
              if not gr.posicao_max(symbol, posicao_max) and gr.posicoes_abertas(symbol)[0] != 'short' and not gr.ultima_ordem_aberta(symbol):
                try:
                    exchange.create_order(symbol=symbol, side='buy', type='market', amount=amount, params={'hedged': 'true'})
                    message = f"******* ABRINDO LONG DE {amount} MOEDAS EM {symbol} SMC !*******"
                    logger.info(message)
                    await send_message(message)
                except Exception as e:
                    error_message = f"******* PROBLEMA AO ABRIR LONG: {e} *******"
                    logger.error(error_message)
        elif bos_choch['CHOCH'].iloc[-1] == -1 and order_blocks['OB'].iloc[-1] == -1 and liquidity['Liquidity'].iloc[-1] == -1:
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