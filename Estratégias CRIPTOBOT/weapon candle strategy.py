from config import binancesecret
from config import binancekey
import pandas as pd
import ccxt
import pandas_ta as ta


binance = ccxt.binance ({'enableRateLimit':True,
                        'apikey': binancekey,
                        'secret': binancesecret,
                        'options': {
                            'defaultType': 'future',
                              },
})

symbol = 'BTCUSDT'
timeframe = '5m' #1m 5m 15m 1h 1d
bars = binance.fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit=100)

df_candles = pd.DataFrame(bars, columns=[['time', 'abertura', 'max', 'min', 'fechamento', 'volume']])
df_candles['time'] = pd.to_datetime(df_candles['time'], unit='ms', utc=True).map(lambda x: x.tz_convert('America/Sao_Paulo'))