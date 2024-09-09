import logging
import pandas as pd
import pandas_ta as ta
from ta.momentum import RSIIndicator
from ta.volume import VolumePriceTrendIndicator
import time
import GerenciamentoRisco as gr
import config.config as k
# from telegram_bot import send_message

# Ativando o logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

async def startStrategy(symbol,send_message):
    exchange = gr.binance

    timeframe = '15m'

    await gr.fecha_pnl(symbol, k.loss, k.target, send_message,timeframe)


  # posicao = 0.015
    # total_usdt = gr.get_balance['free_usdt']
    total_usdt = 50
    leverage = 10

    capital_usado = total_usdt * leverage

    
    # threshold = 0.0015

    ticker = exchange.fetch_ticker(symbol)
    current_price = ticker['last']
    amount = capital_usado / current_price
    amount = exchange.amount_to_precision(symbol, amount)
    posicao_max = float(amount) * 2

 
    bars = exchange.fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit=200)
    df_candles = pd.DataFrame(bars, columns=['time', 'abertura', 'max', 'min', 'fechamento', 'volume'])
    df_candles['time'] = pd.to_datetime(df_candles['time'], unit='ms', utc=True).map(lambda x: x.tz_convert('America/Sao_Paulo'))

    def identifica_estrutura_mercado(df):
        df['topo_valido'] = False
        df['fundo_valido'] = False
        df['choch'] = False
        df['buy_signal'] = False
        df['sell_signal'] = False
        
        last_valid_high = None
        last_valid_low = None
        
        for i in range(2, len(df)):
            current_high = df['max'].iloc[i]
            current_low = df['min'].iloc[i]
            
            # Identificando topos válidos
            if current_high > df['max'].iloc[i-1] and df['min'].iloc[i-1] < df['min'].iloc[i-2]:
                df.at[i, 'topo_valido'] = True
                last_valid_high = current_high
                # logger.info(f"Novo topo válido detectado em {df['time'].iloc[i]}: {last_valid_high}")
            
            # Identificando fundos válidos
            if current_low < df['min'].iloc[i-1] and df['max'].iloc[i-1] > df['max'].iloc[i-2]:
                df.at[i, 'fundo_valido'] = True
                last_valid_low = current_low
                # logger.info(f"Novo fundo válido detectado em {df['time'].iloc[i]}: {last_valid_low}")
            
            # Detectando CHoCH e gerando sinais
            if last_valid_high is not None and last_valid_low is not None:
                if current_low < last_valid_low:
                    df.at[i, 'choch'] = True
                    df.at[i, 'sell_signal'] = True  # Sinal de venda após CHoCH Bearish
                    last_valid_low = current_low
                    # logger.info(f"CHoCH Bearish detectado em {df['time'].iloc[i]}: rompimento do fundo válido {last_valid_low}")
                
                elif current_high > last_valid_high:
                    df.at[i, 'choch'] = True
                    df.at[i, 'buy_signal'] = True  # Sinal de compra após CHoCH Bullish
                    last_valid_high = current_high
                    # logger.info(f"CHoCH Bullish detectado em {df['time'].iloc[i]}: rompimento do topo válido {last_valid_high}")
        
        return df

    # Exemplo de uso com o DataFrame df_candles
    df_candles = identifica_estrutura_mercado(df_candles)

    # Exibe os sinais gerados
    # print(df_candles[['time', 'fechamento', 'choch', 'buy_signal', 'sell_signal']])

    if df_candles['sell_signal'].iloc[-1] == True:
          if not gr.posicao_max(symbol, posicao_max) and gr.posicoes_abertas(symbol)[0] != 'long' and not gr.ultima_ordem_aberta(symbol):
                try:
                    bid, ask = gr.livro_ofertas(symbol)
                    ask = exchange.price_to_precision(symbol, ask)
                    # leverage = exchange.set_leverage(30,symbol,params)
                    exchange.create_order(symbol, side='sell', type='LIMIT', price=ask, amount=amount, params={'hedged':'true'})
                    message = f"******* ABRINDO SHORT DE {amount} MOEDAS EM {symbol} SMC!*******"
                    logger.info(message)
                    await send_message(message)
                except Exception as e:
                    error_message = f"******* PROBLEMA AO ABRIR SHORT: {e} *******"
                    logger.error(error_message)
                    # await send_message(error_message)
    elif df_candles['buy_signal'].iloc[-1] == True:
         if not gr.posicao_max(symbol, posicao_max) and gr.posicoes_abertas(symbol)[0] != 'short' and not gr.ultima_ordem_aberta(symbol):
                try:
                    bid, ask = gr.livro_ofertas(symbol)
                    bid = exchange.price_to_precision(symbol, bid)
                    # leverage = exchange.set_leverage(30,symbol,params)
                    exchange.create_order(symbol, side='buy', type='LIMIT', price=bid, amount=amount, params={'hedged':'true'})
                    message = f"******* ABRINDO LONG DE {amount} MOEDAS EM {symbol} SMC !*******"
                    logger.info(message)
                    await send_message(message)
                except Exception as e:
                    error_message = f"******* PROBLEMA AO ABRIR LONG: {e} *******"
                    logger.error(error_message)
                    # await send_message(error_message)
    else:
        logger.info('Nada para fazer')
        # await send_message('Nada para fazer')


