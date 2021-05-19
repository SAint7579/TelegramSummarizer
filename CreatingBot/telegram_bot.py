import os
import telebot
from utility_functions import *

API_KEY = os.getenv('API_KEY')
bot = telebot.TeleBot('1744705375:AAHSJVPjEIfBv09SWMGAfJRrAAktsredt4E')

@bot.message_handler(commands=['Greet'])
def greet(message):
	bot.reply_to(message,"Hello!")


def sum_request(message):
	req = message.text.split()

	return len(req)==2 and float(req[1]).is_integer()

@bot.message_handler(func=sum_request)
def send_summary(message):
	bot.reply_to(message,"I'll summarize in a minute")
	command = message.text.split()
	summary = callAllFunctions(command[0],command[1],sess_password=None)
	bot.send_message(message.chat.id,summary)

bot.polling()