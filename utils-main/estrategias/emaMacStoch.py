import logging
import pandas as pd
import pandas_ta as ta
import asyncio
import GerenciamentoRisco as gr
import config.config as k

# Configuração de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Função para implementar a estratégia com EMA 26, MACD (9, 21, 5), RSI 10 e ADX 14
async def startStrategy(symbol, send_message):
    try:
        exchange = gr.binance

        # Fechar posições com lucro ou prejuízo conforme gerenciamento de risco
        await gr.fecha_pnl(symbol=symbol, loss=-15, target=60, send_message=send_message, timeframe='15m')

        # Configurações de capital e alavancagem
        total_usdt = k.amount
        leverage = 10
        capital_usado = total_usdt * leverage

        # Obter preço atual
        ticker = exchange.fetch_ticker(symbol)
        current_price = ticker['last']
        amount = capital_usado / current_price
        amount = float(exchange.amount_to_precision(symbol, amount))
        posicao_max = amount * 2

        # Obter dados de mercado
        timeframe = '15m'  # Timeframe de 15 minutos
        bars = exchange.fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit=100)
        df = pd.DataFrame(bars, columns=['time', 'open', 'high', 'low', 'close', 'volume'])

        # Calcular o EMA de 34 períodos (para identificar tendências)
        df['ema_34'] = ta.ema(df['close'], length=26)

        # Calcular o MACD (8, 21, 5)
        macd = ta.macd(df['close'], fast=9, slow=21, signal=5)
        df['macd_line'] = macd['MACD_9_21_5']
        df['signal_line'] = macd['MACDs_9_21_5']

        # Calcular o ADX (Average Directional Index) com 14 períodos
        adx = ta.adx(df['high'], df['low'], df['close'], length=14)
        df['adx'] = adx['ADX_14']
        df['di_plus'] = adx['DMP_14']
        df['di_minus'] = adx['DMN_14']

        # Calcular o RSI com 10 períodos (Relative Strength Index)
        df['rsi'] = ta.rsi(df['close'], length=10)

        # Verificar se o preço está acima ou abaixo da EMA 34 para identificar a tendência
        is_uptrend = df['close'].iloc[-1] > df['ema_34'].iloc[-1]  # Tendência de alta
        is_downtrend = df['close'].iloc[-1] < df['ema_34'].iloc[-1]  # Tendência de baixa

        # Detectar cruzamento do MACD
        previous_macd_line = df['macd_line'].iloc[-2]
        current_macd_line = df['macd_line'].iloc[-1]
        previous_signal_line = df['signal_line'].iloc[-2]
        current_signal_line = df['signal_line'].iloc[-1]

        # Condições para o ADX (força da tendência: ADX > 25 indica tendência forte)
        strong_trend = df['adx'].iloc[-1] > 25

        # Condições do RSI (sobrecompra > 70, sobrevenda < 30)
        is_rsi_overbought = df['rsi'].iloc[-1] > 70 
        is_rsi_oversold = df['rsi'].iloc[-1] < 30
        is_rsi_level_above_55= df['rsi'].iloc[-1] >= 60
        is_rsi_level_under_40 = df['rsi'].iloc[-1] <= 44
        
        # Estratégia de Compra (LONG) no cruzamento positivo do MACD e com RSI e ADX em condições adequadas
        if (previous_macd_line <= previous_signal_line and current_macd_line >= current_signal_line
            and is_uptrend and strong_trend and not is_rsi_overbought):
             if not gr.posicao_max(symbol, posicao_max) and gr.posicoes_abertas(symbol)[0] != 'short' and not gr.ultima_ordem_aberta(symbol):
                    try:
                        exchange.create_order(symbol=symbol, side='buy', type='market', amount=amount, params={'hedged': 'true'})
                        message = f"🚀 Abrindo Long em {symbol} com EMA 26 + MACD + ADX + RSI! 📈"
                        logger.info(message)
                        await send_message(message)
                    except:
                        logger.info(f"⚠️ Problema ao abrir Long em {symbol}!")
        # Estratégia de Venda (SHORT) no cruzamento negativo do MACD e com RSI e ADX em condições adequadas
        elif (previous_macd_line >= previous_signal_line and current_macd_line <= current_signal_line
              and is_downtrend and strong_trend and not is_rsi_oversold):
            if not gr.posicao_max(symbol, posicao_max) and gr.posicoes_abertas(symbol)[0] != 'long' and not gr.ultima_ordem_aberta(symbol):
                try:
                    exchange.create_order(symbol=symbol, side='sell', type='market', amount=amount)
                    message = f"🔻 Abrindo Short em {symbol} com EMA 26 + MACD + ADX + RSI! 📉"
                    logger.info(message)
                    await send_message(message)
                except:
                    logger.info(f"⚠️ Problema ao abrir Short em {symbol}!")
    except Exception as e:
        logger.error(f"Erro ao executar a estratégia para {symbol}: {e}")
        # await send_message(f"Erro ao executar a estratégia: {e}")
