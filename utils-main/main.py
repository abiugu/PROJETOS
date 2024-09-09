import logging
import asyncio
import estrategias.MacdRsi as MacdRsi
import estrategias.emaMacStoch as emaMacStoch
import config.config as config
from telegram_bot import start_bot, send_message

# Ativando o logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)
# commit
# Variáveis globais
running = False
running_lock = asyncio.Lock()
symbols2 = ['SOLUSDT','BTCUSDT','ETHUSDT']
symbols1 = ['AVAXUSDT','PENDLEUSDT','NEARUSDT','SOLUSDT','ETHUSDT','BTCUSDT']

async def start_trading():
    global running
    async with running_lock:
        running = True
    await send_message("Bot de trading iniciado. Trading está ON.")

async def stop_trading():
    global running
    async with running_lock:
        running = False
    await send_message("Bot de trading parado. Trading está OFF.")

async def run_strategy(strategy, strategy_name, symbol):
    while True:
        # async with running_lock:
        if running:
            try:
                logger.info(f'Iniciando {strategy_name} para {symbol}')
                await strategy(symbol, send_message)
            except Exception as e:
                logger.error(f"Erro na estratégia {strategy_name} para {symbol}: {e}")
        else:
            logger.info(f'Bot desligado no momento para {symbol} e {strategy_name}')
        await asyncio.sleep(15)

async def trade_symbol2(symbol):
    # Rodar todas as estratégias para um único símbolo de forma concorrente
    tasks = [
        asyncio.create_task(run_strategy(MacdRsi.startStrategy, "MACD", symbol))
        # asyncio.create_task(run_strategy(WPC.startStrategy, "WPC", symbol))
    ]
    await asyncio.gather(*tasks)

async def trade_symbol1(symbol):
    # Rodar todas as estratégias para um único símbolo de forma concorrente
    tasks = [
        asyncio.create_task(run_strategy(emaMacStoch.startStrategy, "emaStoch", symbol))
    ]
    await asyncio.gather(*tasks)

async def trading():
    # Criar uma tarefa para cada símbolo para rodar as estratégias de forma concorrente
    tasks = []
    # for symbol in symbols2:
    #     logger.info(f'Iniciando estratégias para {symbol}')  # Log para cada símbolo
    #     task = asyncio.create_task(trade_symbol2(symbol))
    #     tasks.append(task)
    for symbol in symbols1:
        logger.info(f'Iniciando estratégias para {symbol}')  # Log para cada símbolo
        task = asyncio.create_task(trade_symbol1(symbol))
        tasks.append(task)    
    
    # Aguardar todas as tarefas concluírem
    await asyncio.gather(*tasks)

async def main():
    # Iniciar a função de trading em uma task separada
    trading_task = asyncio.create_task(trading())

    # Iniciar o bot do Telegram em paralelo
    bot_task = asyncio.create_task(start_bot(start_trading, stop_trading))

    # Aguarda ambas as tasks de forma concorrente
    await asyncio.gather(trading_task, bot_task)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
