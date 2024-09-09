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

async def startStrategy(symbol, send_message):
    exchange = gr.binance
    timeframe = '5m'

    # Fechar PnL de posições abertas, se necessário
    await gr.fecha_pnl(symbol, 1.5 , 5 , send_message, timeframe)

    total_usdt = 50  # Ajuste o valor conforme necessário
    leverage = 10
    capital_usado = total_usdt * leverage

    # Obter o preço atual e calcular o tamanho da posição
    ticker = exchange.fetch_ticker(symbol)
    current_price = ticker['last']
    amount = capital_usado / current_price
    amount = exchange.amount_to_precision(symbol, amount)
    posicao_max = float(amount) * 2

    # Obter dados históricos para o timeframe de 1 hora
    bars = exchange.fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit=250)
    df_candles = pd.DataFrame(bars, columns=['time', 'abertura', 'max', 'min', 'fechamento', 'volume'])
    df_candles['time'] = pd.to_datetime(df_candles['time'], unit='ms', utc=True).map(lambda x: x.tz_convert('America/Sao_Paulo'))
    # Calcular indicadores Ichimoku e EMAs
    df_candles['EMA_5m'] = ta.ema(df_candles['fechamento'], length=5)
    df_candles['EMA_15m'] = ta.ema(df_candles['fechamento'], length=15)
    df_candles['EMA_30m'] = ta.ema(df_candles['fechamento'], length=30)
    df_candles['EMA_1h'] = ta.ema(df_candles['fechamento'], length=60)
    df_candles['EMA_2h'] = ta.ema(df_candles['fechamento'], length=120)

    # Calcular o indicador Ichimoku
    ichimoku_df, ichimoku_displacement = ta.ichimoku(
        df_candles['max'], df_candles['min'], df_candles['fechamento'], 
        conversion_line_period=9, base_line_periods=26, span_b_periods=52, displacement=26
    )

    # Renomear colunas de Ichimoku para evitar duplicação
    ichimoku_df.columns = [f'{col}_ichimoku' for col in ichimoku_df.columns]

    # Adicionar as colunas do Ichimoku ao DataFrame principal
    df_candles = pd.concat([df_candles, ichimoku_df], axis=1)

    # Calcular ATR
    df_candles['ATR'] = ta.atr(df_candles['max'], df_candles['min'], df_candles['fechamento'])

    # Função para gerar sinais de compra e venda
    def generate_signals(df):
        # Inicializa sem sinal
        df['signal'] = 0

        for i in range(1, len(df)):
            # Acessar valores escalares usando .iloc[i] para garantir que estamos acessando um único valor
            fechamento = df['fechamento'].iloc[i]
            isa_9 = df['ISA_9_ichimoku'].iloc[i]
            isb_26 = df['ISB_26_ichimoku'].iloc[i]
            ema_5m = df['EMA_5m'].iloc[i]
            ema_15m = df['EMA_15m'].iloc[i]
            ema_30m = df['EMA_30m'].iloc[i]

            # Verificação de NaN para cada valor individualmente
            if pd.isna(fechamento) or pd.isna(isa_9) or pd.isna(isb_26) or pd.isna(ema_5m) or pd.isna(ema_15m) or pd.isna(ema_30m):
                continue  # Pula para o próximo loop se houver NaN

            # Condição de Compra
            if fechamento > isa_9 and fechamento > isb_26 and ema_5m > ema_15m and ema_15m > ema_30m:
                df.loc[i, 'signal'] = 1  # Sinal de compra

            # Condição de Venda
            elif fechamento < ema_5m:
                df.loc[i, 'signal'] = -1  # Sinal de venda

        return df

    # Aplicar a função para gerar sinais
    df_candles = generate_signals(df_candles)

    # Obter a última linha para verificar sinais
    last_row = df_candles.iloc[-1]

  
    if last_row['signal'] == 1:  # Sinal de compra
        posicoes_abertas = gr.posicoes_abertas(symbol)
        if not gr.posicao_max(symbol, posicao_max) and (len(posicoes_abertas) == 0 or posicoes_abertas[0] != 'short') and not gr.ultima_ordem_aberta(symbol):
            try:
                bid, ask = gr.livro_ofertas(symbol)
                bid = exchange.price_to_precision(symbol, bid)
                exchange.create_order(symbol, side='buy', type='LIMIT', price=bid, amount=amount, params={'hedged':'true'})
                message = f"******* ABRINDO LONG DE {amount} MOEDAS EM {symbol} ICHIMOKU! *******"
                logger.info(message)
                await send_message(message)
            except Exception as e:
                error_message = f"******* PROBLEMA AO ABRIR LONG: {e} *******"
                logger.error(error_message)

    elif last_row['signal'] == -1:  # Sinal de venda
        posicoes_abertas = gr.posicoes_abertas(symbol)
        if not gr.posicao_max(symbol, posicao_max) and (len(posicoes_abertas) == 0 or posicoes_abertas[0] != 'long') and not gr.ultima_ordem_aberta(symbol):
            try:
                bid, ask = gr.livro_ofertas(symbol)
                ask = exchange.price_to_precision(symbol, ask)
                exchange.create_order(symbol, side='sell', type='LIMIT', price=ask, amount=amount, params={'hedged':'true'})
                message = f"******* ABRINDO SHORT DE {amount} MOEDAS EM {symbol} ICHIMOKU! *******"
                logger.info(message)
                await send_message(message)
            except Exception as e:
                error_message = f"******* PROBLEMA AO ABRIR SHORT: {e} *******"
                logger.error(error_message)
    else:
        logger.info('Nada para fazer')
        # await send_message('Nada para fazer')

    # # Exemplo de chamada da função
    # await aplicar_logica_entrada(symbol="BTC/USDT", last_row=last_row, posicao_max=3, amount=1)
