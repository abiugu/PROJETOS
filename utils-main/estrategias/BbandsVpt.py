import logging
import pandas as pd
import pandas_ta as ta
from ta.momentum import RSIIndicator
from ta.volume import VolumePriceTrendIndicator
import GerenciamentoRisco as gr
import config.config as k
import time

# Configurando o logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def startStrategy(symbol, send_message):
    exchange = gr.binance
    timeframe = '15m'

    # Fechando posições com PNL
    await gr.fecha_pnl(symbol, k.loss, k.target, send_message, timeframe)

    # Definindo parâmetros de posição e capital
    total_usdt = 20
    leverage = 20
    capital_usado = total_usdt * leverage

    ticker = exchange.fetch_ticker(symbol)
    current_price = ticker['last']
    amount = capital_usado / current_price
    amount = exchange.amount_to_precision(symbol, amount)
    posicao_max = float(amount) * 2

    # Coletando dados históricos de velas
    bars = exchange.fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit=100)
    df_candles = pd.DataFrame(bars, columns=['time', 'abertura', 'max', 'min', 'fechamento', 'volume'])
    df_candles['time'] = pd.to_datetime(df_candles['time'], unit='ms', utc=True).map(lambda x: x.tz_convert('America/Sao_Paulo'))

    # Calculando RSI
    rsi = RSIIndicator(df_candles['fechamento'])
    df_candles['RSI'] = rsi.rsi()

    # Calculando Bandas de Bollinger
    bbands = ta.bbands(df_candles.fechamento, length=20, std=2)
    bbands = bbands.iloc[:, [0, 1, 2]]
    bbands.columns = ['BBL', 'BBM', 'BBU']
    bbands['largura'] = (bbands.BBU - bbands.BBL) / bbands.BBM
    df_candles = pd.concat([df_candles, bbands], axis=1)

    # Definindo o threshold baseado na largura das Bandas de Bollinger
    threshold = df_candles['largura'].iloc[-1] * 0.50

    # Calculando VPT (Volume Price Trend)
    vpt = VolumePriceTrendIndicator(close=df_candles['fechamento'], volume=df_candles['volume'])
    df_candles['VPT'] = vpt.volume_price_trend()

    # Obtendo o preço atual do símbolo
    price = float(exchange.fetch_trades(symbol)[-1]['price'])
    price = float(exchange.price_to_precision(symbol, price))

    # Determinando a tendência do VPT
    if df_candles['VPT'].iloc[-1] > df_candles['VPT'].iloc[-2]:
        vpt_trend = 'alta'
    elif df_candles['VPT'].iloc[-1] < df_candles['VPT'].iloc[-2]:
        vpt_trend = 'baixa'
    else:
        vpt_trend = 'sem mudança significativa'

    # Parâmetros para a ordem
    params = {
        'symbol': exchange.market_id(symbol),
        'marginMode': 'isolated',  # ou 'cross'
    }

    # Função para verificar condições de entrada em posição long
    def should_open_long(df_candles, price, symbol, threshold):
        return (
            df_candles['largura'].iloc[-1] >= threshold and
            df_candles['fechamento'].iloc[-2] <= df_candles['BBL'].iloc[-1] and
            df_candles['RSI'].iloc[-1] <= 32 and
            df_candles['VPT'].iloc[-1] > df_candles['VPT'].iloc[-2]
        )

    # Função para verificar condições de entrada em posição short
    def should_open_short(df_candles, price, symbol, threshold):
        return (
            df_candles['largura'].iloc[-1] >= threshold and
            df_candles['fechamento'].iloc[-2] >= df_candles['BBU'].iloc[-1] and
            df_candles['RSI'].iloc[-1] >= 68 and
            df_candles['VPT'].iloc[-1] < df_candles['VPT'].iloc[-2]
        )

    # Lógica principal de negociação
    # async def trade_logic(df_candles, price, symbol, amount, threshold, vpt_trend):
    if should_open_long(df_candles, price, symbol, threshold) and vpt_trend == 'alta':
        if not gr.posicao_max(symbol, posicao_max) and gr.posicoes_abertas(symbol)[0] != 'short' and not gr.ultima_ordem_aberta(symbol):
            try:
                bid, ask = gr.livro_ofertas(symbol)
                bid = exchange.price_to_precision(symbol, bid)
                exchange.create_order(symbol, side='buy', type='LIMIT', price=bid, amount=amount, params={'hedged': 'true'})
                message = f"******* ABRINDO LONG DE {amount} MOEDAS EM {symbol} BBANDS! *******"
                logger.info(message)
                await send_message(message)
            except Exception as e:
                error_message = f"******* PROBLEMA AO ABRIR LONG: {e} *******"
                logger.error(error_message)

    elif should_open_short(df_candles, price, symbol, threshold) and vpt_trend == 'baixa':
        if not gr.posicao_max(symbol, posicao_max) and gr.posicoes_abertas(symbol)[0] != 'long' and not gr.ultima_ordem_aberta(symbol):
            try:
                bid, ask = gr.livro_ofertas(symbol)
                ask = exchange.price_to_precision(symbol, ask)
                exchange.create_order(symbol, side='sell', type='LIMIT', price=ask, amount=amount, params={'hedged': 'true'})
                message = f"******* ABRINDO SHORT DE {amount} MOEDAS EM {symbol} BBANDS! *******"
                logger.info(message)
                await send_message(message)
            except Exception as e:
                error_message = f"******* PROBLEMA AO ABRIR SHORT: {e} *******"
                logger.error(error_message)

    else:
        logger.info('Nada para fazer')
