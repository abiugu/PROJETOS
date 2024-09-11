import ccxt
import config.config as k
import decimal
import time
import asyncio


binance = ccxt.binance({
    'enableRateLimit': True,
    'recvWindow': 5000,
    'apiKey': str(k.binancekey),
    'secret': str(k.binancesecret),
    'options': {
        'defaultType': 'future',
    }
})


def posicoes_abertas(symbol):
    lado = []
    tamanho = []
    precoEntrada = []
    notional = []
    percentage = []
    pnl = []
    bal = binance.fetch_positions(symbols=[symbol])
    for i in bal:
        lado = i['side']
        tamanho = i['info']['positionAmt'].replace('-', '')
        precoEntrada = i['entryPrice']
        notional = i['notional']
        percentage = i['percentage']
        pnl = i['info']['unRealizedProfit']

    if lado == 'long':
        pos_aberta = True
    elif lado == 'short':
        pos_aberta = True
    else:
        pos_aberta = False

    return lado, tamanho, precoEntrada, pos_aberta, notional, percentage, pnl


def livro_ofertas(symbol):
    livroOfertas = binance.fetch_order_book(symbol, limit=100)
    bid = decimal.Decimal(livroOfertas['bids'][0][0])
    ask = decimal.Decimal(livroOfertas['asks'][0][0])
    return bid, ask


def encerrar_posicao(symbol):
    posAberta = posicoes_abertas(symbol)[3]
    while posAberta == True:
        lado = posicoes_abertas(symbol)[0]
        tamanho = posicoes_abertas(symbol)[1]

        if lado == 'long':
            binance.cancel_all_orders(symbol)
            bid, ask = livro_ofertas(symbol)
            ask = binance.price_to_precision(symbol, ask)
            binance.create_order(symbol, side='sell', type='LIMIT',
                                 price=ask, amount=tamanho, params={'hedged': 'true'})
            print(f'Vendendo posição long de {tamanho} moedas de {symbol}')
            msg = 'Vendendo posição long'
            time.sleep(20)
        elif lado == 'short':
            binance.cancel_all_orders(symbol)
            bid, ask = livro_ofertas(symbol)
            bid = binance.price_to_precision(symbol, bid)
            binance.create_order(symbol, side='buy', type='LIMIT',
                                 price=bid, amount=tamanho, params={'hedged': 'true'})
            print(f'Comprando posição short de {tamanho} moedas de {symbol}')
            time.sleep(20)
        else:
            print('Impossivel Encerrar a Posição')

        posAberta = posicoes_abertas(symbol)[3]


def getBalance():
    params = {'type': 'futures', 'subType': 'linear'}
    balance = binance.fetch_balance(params)
    balance = balance['USDT']['total']
    return balance


trailing_loss = k.loss


async def fecha_pnl(symbol, loss, target, send_message, timeframe):
    global trailing_loss  # Define que vamos usar a variável global
    try:
        # Obtendo PnL e Percentual em uma única chamada
        posicao = posicoes_abertas(symbol=symbol)
        pnl = posicao[6]
        percent = posicao[5]

        # Obtendo saldo da Binance
        params = {'type': 'futures', 'subType': 'linear'}
        balance = binance.fetch_balance(params)['USDT']['total']

        # Definindo o tempo de espera com base no timeframe
        num_timeframe = int(timeframe[:-1])
        unidade = timeframe[-1]
        unidades = {'m': num_timeframe * 5 * 60, 'h': num_timeframe *
                    2 * 3600, 'd': num_timeframe * 0.5 * 86400}
        # Valor padrão de 60s caso a unidade seja inválida
        t_sleep = unidades.get(unidade, 60)

        if percent:
            # Verificando condições para encerrar posição
            if percent <= loss:
                msg = f"❌ Posição encerrada por perda: {
                    pnl}. Saldo atual: {balance}."
                encerrar_posicao(symbol=symbol)
                await send_message(msg)
                await asyncio.sleep(t_sleep)

            elif percent >= target:
                msg = f"✅ Posição encerrada por ganho: {pnl} em {
                    symbol}. Saldo atual: {balance}. Parabéns!"
                encerrar_posicao(symbol=symbol)
                await send_message(msg)

            elif percent <= trailing_loss:
                msg = f"🔄 Posição encerrada por trailing stop com ganho: {pnl} em {
                    symbol}. Saldo atual: {balance}. Proteção de lucro ativada!"
                encerrar_posicao(symbol=symbol)
                await send_message(msg)
                await asyncio.sleep(t_sleep)
                trailing_loss = loss

            loss_thresholds = [(50, 45), (40, 35), (30, 25), (20, 15), (10, 5)]
            updated = False
            for threshold, new_trailing in loss_thresholds:
                if percent >= threshold and trailing_loss < new_trailing:
                    trailing_loss = new_trailing
                    updated = True
                    break
            if not updated:
                # Se nenhuma condição for atendida, trailing_loss mantém o valor original de loss
                trailing_loss = loss

    except Exception as e:
        error_msg = f"⚠ Erro ao verificar PnL ou encerrar posição: {e}"
        await send_message(error_msg)


def posicao_max(symbol, maxPos):
    pos = posicoes_abertas(symbol)[1]
    # maxPos = maxPos
    if isinstance(pos, list):
        max_posicao = False
    elif float(pos) >= float(maxPos):
        max_posicao = True
    else:
        max_posicao = False
    return max_posicao


def ultima_ordem_aberta(symbol):
    order = []
    try:
        order = binance.fetch_orders(symbol)[-1]['status']
        if order == 'open':
            open_order = True
        else:
            open_order = False
    except:
        open_order = False
    return open_order


def get_balance():
    params = {'type': 'futures', 'subType': 'linear'}
    balance = binance.fetch_balance(params)
    balance = balance['USDT']['total']
    total_usdt = balance['USDT']['total']
    free_usdt = balance['USDT']['free']
    return total_usdt, free_usdt
