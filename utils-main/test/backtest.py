import logging
import pandas as pd
import pandas_ta as ta
from ta.momentum import RSIIndicator
from ta.volume import VolumePriceTrendIndicator
import ccxt

# Ativando o logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

class Backtest:
    def __init__(self, exchange, symbol, timeframe, initial_balance, position_size, posicao_max, take_profit, stop_loss):
        self.exchange = exchange
        self.symbol = symbol
        self.timeframe = timeframe
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.position_size = position_size
        self.posicao_max = posicao_max
        self.take_profit = take_profit
        self.stop_loss = stop_loss
        self.positions = []
        self.trade_log = []
        self.wins = 0
        self.losses = 0

    def fetch_historical_data(self, start_date, end_date):
        since = self.exchange.parse8601(f"{start_date}T00:00:00Z")
        end = self.exchange.parse8601(f"{end_date}T00:00:00Z")
        all_bars = []
        
        while since < end:
            bars = self.exchange.fetch_ohlcv(self.symbol, timeframe=self.timeframe, since=since, limit=1000)
            if len(bars) == 0:
                break
            last_time = bars[-1][0]
            if last_time == since:
                break
            since = last_time
            all_bars += bars
            if last_time >= end:
                break

        df = pd.DataFrame(all_bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df

    def simulate_order(self, side, price, amount):
        position = {
            'side': side,
            'price': price,
            'size': amount,
            'take_profit': price * (1 + self.take_profit) if side == 'long' else price * (1 - self.take_profit),
            'stop_loss': price * (1 - self.stop_loss) if side == 'long' else price * (1 + self.stop_loss),
            'timestamp': pd.Timestamp.now()
        }
        self.positions.append(position)
        logger.info(f"{side.capitalize()} order simulated at {price} with amount {amount}")
        logger.info(f"Take Profit set at {position['take_profit']}, Stop Loss set at {position['stop_loss']}")

    def close_position(self, price):
        if not self.positions:
            return

        position = self.positions.pop()
        pnl = (price - position['price']) * position['size'] if position['side'] == 'long' else (position['price'] - price) * position['size']
        self.balance += pnl
        trade_result = 'win' if pnl > 0 else 'loss'
        if pnl > 0:
            self.wins += 1
        else:
            self.losses += 1
        self.trade_log.append({
            'entry_price': position['price'],
            'exit_price': price,
            'side': position['side'],
            'size': position['size'],
            'pnl': pnl,
            'result': trade_result,
            'timestamp': pd.Timestamp.now(),
            'take_profit': position['take_profit'],
            'stop_loss': position['stop_loss']
        })
        logger.info(f"Closed {position['side']} position at {price}, PnL: {pnl:.2f}, Result: {trade_result}")

    def run_backtest(self, start_date, end_date):
        df_candles = self.fetch_historical_data(start_date, end_date)
        df_candles['fechamento'] = df_candles['close']

        for i in range(1, len(df_candles)):
            current_price = df_candles['close'].iloc[i]

            # Calcular indicadores
            rsi = RSIIndicator(df_candles['fechamento'][:i+1]).rsi()
            df_candles['RSI'] = rsi

            bbands = ta.bbands(df_candles['fechamento'][:i+1], length=20, std=2)
            bbands = bbands.iloc[:, [0, 1, 2]]
            bbands.columns = ['BBL', 'BBM', 'BBU']
            df_candles = pd.concat([df_candles, bbands], axis=1)

            vpt = VolumePriceTrendIndicator(close=df_candles['fechamento'][:i+1], volume=df_candles['volume'][:i+1])
            df_candles['VPT'] = vpt.volume_price_trend()

            # Determinar tendência do VPT
            if df_candles['VPT'].iloc[-1] > df_candles['VPT'].iloc[-2]:
                vpt_trend = 'alta'
            elif df_candles['VPT'].iloc[-1] < df_candles['VPT'].iloc[-2]:
                vpt_trend = 'baixa'
            else:
                vpt_trend = 'sem mudança significativa'

            # Verificar Stop Loss / Take Profit
            if self.positions:
                position = self.positions[-1]
                if (position['side'] == 'long' and current_price >= position['take_profit']) or (position['side'] == 'short' and current_price <= position['take_profit']):
                    self.close_position(position['take_profit'])
                elif (position['side'] == 'long' and current_price <= position['stop_loss']) or (position['side'] == 'short' and current_price >= position['stop_loss']):
                    self.close_position(position['stop_loss'])

            # Lógica de estratégia
            if df_candles['fechamento'].iloc[-1] >= df_candles['BBU'].iloc[-1] and df_candles['RSI'].iloc[-1] >= 70:
                if vpt_trend == 'alta':
                    if not self.positions or self.positions[-1]['side'] == 'short':
                        self.close_position(current_price)
                        self.simulate_order('long', current_price, self.position_size)
            elif df_candles['fechamento'].iloc[-1] <= df_candles['BBL'].iloc[-1] and df_candles['RSI'].iloc[-1] <= 30:
                if vpt_trend == 'baixa':
                    if not self.positions or self.positions[-1]['side'] == 'long':
                        self.close_position(current_price)
                        self.simulate_order('short', current_price, self.position_size)

    def print_summary(self):
        total_pnl = sum([trade['pnl'] for trade in self.trade_log])
        win_rate = (self.wins / (self.wins + self.losses)) * 100 if (self.wins + self.losses) > 0 else 0
        logger.info(f"Initial balance: {self.initial_balance}, Final balance: {self.balance}, Total PnL: {total_pnl:.2f}")
        logger.info(f"Total Wins: {self.wins}, Total Losses: {self.losses}, Win Rate: {win_rate:.2f}%")
        for trade in self.trade_log:
            logger.info(trade)

# Exemplo de uso
if __name__ == "__main__":
    exchange = ccxt.binance()
    backtest = Backtest(
        exchange=exchange, 
        symbol='BTC/USDT', 
        timeframe='15m', 
        initial_balance=1000, 
        position_size=0.002, 
        posicao_max=0.004,
        take_profit=0.04,  # 1% de take profit
        stop_loss=0.001   # 0.5% de stop loss
    )
    backtest.run_backtest(start_date='2023-01-01', end_date='2023-12-31')
    backtest.print_summary()
