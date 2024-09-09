import logging
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler
import config.config as config
import asyncio
from GerenciamentoRisco import getBalance as saldo

# Ativando o logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Variável global para armazenar o chat_id
chat_id = config.TELEGRAM_CHAT_ID
application = None

async def start(update, context, start_trading):
    global chat_id
    chat_id = update.message.chat_id
    
    try:
        await start_trading()
        await update.message.reply_text('Bot de trading iniciado. Trading está ON.')
    except Exception as e:
        logger.error(f"Erro ao iniciar o trading: {e}")
        await update.message.reply_text('Erro ao iniciar o trading.')

async def stop(update, context, stop_trading):
    try:
        await stop_trading()
        await update.message.reply_text('Bot de trading parado. Trading está OFF.')
    except Exception as e:
        logger.error(f"Erro ao parar o trading: {e}")
        await update.message.reply_text('Erro ao parar o trading.')

async def help_command(update, context):
    await update.message.reply_text(
        'Comandos disponíveis:\n'
        '/start - Iniciar trading\n'
        '/stop - Parar trading\n'
        '/help - Ajuda\n'
        '/config <parametro> <valor> - Atualizar configuração de trading (parametros: capital, stop_loss, stop_gain)\n'
        '/balance - Obter saldo atual'
    )

async def config_command(update, context):
    if len(context.args) < 2:
        await update.message.reply_text('Uso: /config <parametro> <valor>\nParâmetros válidos: capital, stop_loss, stop_gain')
        return

    param = context.args[0].lower()
    value = context.args[1]

    try:
        if param == "capital":
            config.amount = float(value)
            await update.message.reply_text(f'Capital de entrada atualizado para: {config.amount}')
        elif param == "stop_loss":
            config.loss = float(value)
            await update.message.reply_text(f'Stop Loss atualizado para: {config.loss}')
        elif param == "stop_gain":
            config.target = float(value)
            await update.message.reply_text(f'Stop Gain atualizado para: {config.target}')
        else:
            await update.message.reply_text('Parâmetro inválido. Use capital, stop_loss, ou stop_gain.')
    except ValueError:
        await update.message.reply_text('Erro: o valor deve ser um número.')

async def balance_command(update, context):
    try:
        balance = await getBalance()
        await update.message.reply_text(f'Seu saldo atual é: {balance} USDT')
    except Exception as e:
        logger.error(f"Erro ao obter o saldo: {e}")
        await update.message.reply_text('Erro ao obter o saldo.')

async def send_message(message, max_retries=3, retry_delay=5):
    global chat_id, application
    
    if not chat_id or not application:
        logger.warning('Chat ID não está definido ou application não está inicializada. Não é possível enviar mensagem.')
        return
    
    attempt = 0
    
    while attempt < max_retries:
        try:
            await application.bot.send_message(chat_id=chat_id, text=message)
            logger.info("Mensagem enviada com sucesso.")
            break  # Sai do loop se a mensagem for enviada com sucesso
        except Exception as e:
            attempt += 1
            logger.error(f"Erro ao enviar mensagem: {e}. Tentativa {attempt}/{max_retries}.")
            
            if attempt >= max_retries:
                logger.error("Número máximo de tentativas atingido. Não foi possível enviar a mensagem.")
                break
            
            logger.info(f"Tentando reenviar a mensagem em {retry_delay} segundos...")
            await asyncio.sleep(retry_delay)  # Espera antes de tentar novamente

async def start_bot(start_trading, stop_trading):
    global application
    application = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

    # Adiciona os handlers para os comandos
    application.add_handler(CommandHandler("start", lambda update, context: start(update, context, start_trading)))
    application.add_handler(CommandHandler("stop", lambda update, context: stop(update, context, stop_trading)))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("config", config_command))
    application.add_handler(CommandHandler("balance", balance_command))

    # Inicializa e começa o polling
    await application.initialize()
    await application.start()
    await application.updater.start_polling()

# Função de exemplo para obter o saldo - deve ser implementada conforme sua lógica de negócios
async def getBalance():
    balance = saldo()
    return int(balance)  # Retorno de exemplo
