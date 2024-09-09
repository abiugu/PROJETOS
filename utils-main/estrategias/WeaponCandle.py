import GerenciamentoRisco as gr
import config.config as k
import pandas as pd
import pandas_ta as ta
from ta.momentum import RSIIndicator
import time
import datetime
import logging
# from ta.volume import VolumePriceTrendIndicator as vol

# Ativando o logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

async def startStrategy(symbol,send_message):
    try:
        binance = gr.binance
        # symbol = 'BTCUSDT'

        await gr.fecha_pnl(symbol, k.loss, k.target, send_message, '5m')

        total_usdt = 20
        leverage = 10

        capital_usado = total_usdt * leverage

        
        # threshold = 0.0015

        ticker = binance.fetch_ticker(symbol)
        current_price = ticker['last']
        amount = capital_usado / current_price
        amount = binance.amount_to_precision(symbol, amount)
        posicao_max = float(amount) * 2


        # # Define o valor total em USDT que você deseja usar
        # total_usdt = 20  # por exemplo, você quer comprar BTC com 100 USDT


        # # Obtém o preço atual de mercado
        # ticker = binance.fetch_ticker(symbol)
        # current_price = ticker['last']  # ou use 'bid' ou 'ask' dependendo da sua necessidade

        # # Calcula a quantidade de BTC a comprar
        # amount = total_usdt / current_price



        # importar candles

        timeframe = '5m'
        bars = binance.fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit = 35)
        df_candles = pd.DataFrame(bars, columns=['time','abertura','max','min','fechamento','volume'])
        df_candles['time'] = pd.to_datetime(df_candles['time'], unit = 'ms', utc=True).map(lambda x: x.tz_convert('America/Sao_Paulo'))

        # criar métricas da estrategia
        rsi = RSIIndicator(df_candles['fechamento'])
        df_candles['RSI'] = rsi.rsi()

        df_candles['EMA_20'] = ta.ema(close = df_candles['fechamento'], length=20)

        macd = df_candles.ta.macd(close='fechamento',fast=12,slow=26, signal = 9, append =True)
        # df_candles = pd.concat([df_candles, macd], axis=1)

        df_vwap = pd.DataFrame()
        df_vwap[['fechamento','volume']] = df_candles[['fechamento','volume']][25:35]
        df_vwap['preco_ponderado'] = df_vwap['fechamento'] * df_vwap['volume']
        df_candles['VWAP'] = df_vwap['preco_ponderado'].sum()/df_candles['volume'].sum()


        # logger.info(f"RSI : {df_candles.iloc[-1]['RSI']}")
        # logger.info(f"EMA20 : {df_candles.iloc[-1]['EMA_20']}")
        # logger.info(f"MACD : {df_candles.iloc[-1]['MACD_12_26_9']}")
        # logger.info(f"VWAP : {df_candles.iloc[-1]['VWAP']}")


        # print(df_candles) # FUNCAO tail() mostra a ultima linha

        price = binance.fetch_trades(symbol=symbol)[-1]['price']
        price = float(binance.price_to_precision(symbol,price))

        if df_candles.iloc[-2]['RSI'] <= 35 and price >= df_candles.iloc[-1]['EMA_20'] and price >= df_candles.iloc[-1]['VWAP']:
            if df_candles.iloc[-1]['MACD_12_26_9'] >= df_candles.iloc[-1]['MACDs_12_26_9']:
                if not gr.posicao_max(symbol, posicao_max) and gr.posicoes_abertas(symbol)[0] != 'short' and not gr.ultima_ordem_aberta(symbol):
                    try:
                        # binance.set_leverage(10, symbol, datetime.now())
                        # bid, ask = gr.livro_ofertas(symbol)
                        # bid = binance.price_to_precision(symbol, bid)
                        binance.create_order(symbol, side= 'buy', type='market', amount = amount, params={'hedged':'true'})
                        message = f"******* ABRINDO LONG DE {amount} MOEDAS EM {symbol} WPC!*******"
                        logger.info(message)
                        await send_message(message)
                    except:
                        logger.info(f"******* PROBLEMA AO ABRIR LONG !*******")
        elif df_candles.iloc[-2]['RSI'] >= 65 and price <= df_candles.iloc[-1]['EMA_20'] and price <= df_candles.iloc[-1]['VWAP']:
            if df_candles.iloc[-1]['MACD_12_26_9'] <= df_candles.iloc[-1]['MACDs_12_26_9']:
                if not gr.posicao_max(symbol, posicao_max) and gr.posicoes_abertas(symbol)[0] != 'long' and not gr.ultima_ordem_aberta(symbol):
                    try:
                        binance.create_order(symbol, side= 'sell', type='market', amount = amount, params={'hedged':'true'})
                        message = f"******* ABRINDO SHORT DE {amount} MOEDAS EM {symbol} WPC!*******"
                        logger.info(message)
                        await send_message(message)         
                    except:
                        logger.info(f"******* PROBLEMA AO ABRIR SHORT !*******")
        else:
            logger.info(f"******* SEM TENDENCIA PARA LONG OU SHORT!*******")
    except Exception as e:
        logger.error(f"Erro na estratégia {symbol}: {e}")
        await send_message(f"Erro na estratégia {symbol}: {e}")