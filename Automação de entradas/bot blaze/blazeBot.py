from blaze_double_bot import BlazeDoubleBot

import json

with open('config.json', 'r') as f:
        config = json.load(f)

bot = BlazeDoubleBot(config)

bot.run()