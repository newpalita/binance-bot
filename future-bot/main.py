import time
from enum import Enum

import requests
from binance.client import Client

COIN_SYMBOL = 'BTCBUSD'
LEVERAGE = 1

RSI_HIGH_THRESHOLD = 70
RSI_LOW_THRESHOLD = 30
FUTURES_UPDATE_INTERVAL_IN_SECS = 60

line_api_url = 'https://notify-api.line.me/api/notify'
line_api_key = "sbuoWm0RPYoGYaPEBrpnaL648QnKYxkiHFlHn2NlP6z"
line_api_headers = {'content-type': 'application/x-www-form-urlencoded', 'Authorization': 'Bearer ' + line_api_key}

BINANCE_API_KEY = 'cgZrARsfYlKYcL7cm964NYpzGU2c5ijzROqAQbVkXtVm1CMQk7lkUb34JRuP2WLd'
BINANCE_API_SECRET = 'h6BlWe5A0yIXNUfhwvrTSVGebt3PsbFEWs1Hmzm29Pjv1KEWyaXapcBomxXLtohN'

taapi_api_key_rsi = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImZpbmVyX3Jhd2luQGhvdG1haWwuY29tIiwiaWF0IjoxNjM' \
					'4ODg1NDg2LCJleHAiOjc5NDYwODU0ODZ9.I9B_mnR9AiPBrpif0iEk70AIPEYKGsdUygQD6tqKFao'
taapi_api_key_atr = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6Im5ld3BhbGl0YUBnbWFpbC5jb20iLCJpYXQiOjE2NDA3MTE' \
					'3MjMsImV4cCI6Nzk0NzkxMTcyM30.uY7vhsO7mnknvO4vjPoBVL92ra8H8nD7gDq4fBnRCig'
taapi_rsi_url = 'https://api.taapi.io/rsi?secret=' + taapi_api_key_rsi + '&exchange=binance&symbol=BTC/USDT&interval=1m'
taapi_atr_url = 'https://api.taapi.io/atr?secret=' + taapi_api_key_atr + '&exchange=binance&symbol=BTC/USDT&interval=1m'

client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)
print("Using Binance MainNet Server")
rate = 34.00


class Price:
	def __init__(self, s, p, rsi, atr):
		self.symbol = s
		self.price = p
		self.rsi = rsi
		self.atr = atr


class FuturesTradingStrategy(Enum):
	SHORT = -1
	INACTIVE = 0
	LONG = 1


def notify_line(msg):
	requests.post(line_api_url, headers=line_api_headers, data={'message': msg})


def get_coin_info_text(p0, p1):
	return 'Coin: {}, Price: {}'.format(p1.symbol, p1.price) \
		   + '\nin THB: {:,.2f}'.format(p1.converted_price) \
		   + '\nPercentage Change: {:,.8f}%'.format(get_percentage_change(p0.price, p1.price)) \
		   + '\nRSI: {}'.format(p1.rsi)


def get_percentage_change(p0, p1):
	return (p1 - p0) * 100 / p0


def get_rsi():
	r = requests.get(taapi_rsi_url)
	return r


def get_atr():
	r = requests.get(taapi_atr_url)
	return r


def fetch_price():
	p = client.get_symbol_ticker(symbol=COIN_SYMBOL)
	pc = float(p['price'])
	rsi = get_rsi().json()['value']
	atr = get_atr().json()['value']
	
	return Price(COIN_SYMBOL, pc, rsi, atr)


def buy_market_order(symbol, quantity):
	buy_order = client.order_market_buy(
		symbol=symbol,
		quantity=quantity
	)
	for bo in buy_order['fills']:
		print('buy order initiated for {} at price={} and quantity={}'.format(
			bo['commissionAsset'], bo['price'], bo['qty']))


def sell_market_order(symbol, quantity):
	sell_order = client.order_market_sell(
		symbol=symbol,
		quantity=quantity
	)
	for so in sell_order['fills']:
		print('sell order initiated for {} at price={} and quantity={}'.format(
			so['commissionAsset'], so['price'], so['qty']))


def check_account_balance():
	print('Current balance')
	balance = client.get_account()['balances']
	msg = []
	for b in balance:
		if b['asset'] in ['BTC', 'BUSD']:
			print('{}={}'.format(b['asset'], b['free']))
			msg.append('{}={}'.format(b['asset'], b['free']))
	return msg


def calibrate_balance_buy(amount):
	price = fetch_price()
	print('------------------------------')
	print('Calibrate balance by buying with price={} and amount={}'.format(price.price, amount))
	
	buy_market_order(COIN_SYMBOL, amount)
	
	check_account_balance()


def calibrate_balance_sell(amount):
	price = fetch_price()
	print('------------------------------')
	print('Calibrate balance by selling with price={} and amount={}'.format(price.price, amount))
	
	sell_market_order(COIN_SYMBOL, amount)
	
	check_account_balance()


# calibrate_balance_buy(0.006038)

qty = 0.0025
strategy_take_profit_price = 0
strategy_stop_loss_price = 0
opening_strategy = FuturesTradingStrategy.INACTIVE
should_update_balance = False
while True:
	try:
		current_price = fetch_price()
		
		if opening_strategy == FuturesTradingStrategy.INACTIVE:
			if current_price.rsi > RSI_HIGH_THRESHOLD:
				print('RSI above {}, enter long strategy with price={}'.format(RSI_HIGH_THRESHOLD, current_price.price))
				buy_market_order(COIN_SYMBOL, qty)
				opening_strategy = FuturesTradingStrategy.LONG
				strategy_take_profit_price = current_price.price + (current_price.atr * 1.5)
				strategy_stop_loss_price = current_price.price - current_price.atr
				notify_line(
					'\n\nENTER LONG STRATEGY\n\nEnter long strategy of BTC/BUSD\nprice = {}\nquantity = {}'.format(
						current_price.price, qty))
				should_update_balance = True
			elif current_price.rsi < RSI_LOW_THRESHOLD:
				print('RSI below {}, enter short strategy with price={}'.format(RSI_LOW_THRESHOLD, current_price.price))
				sell_market_order(COIN_SYMBOL, qty)
				opening_strategy = FuturesTradingStrategy.SHORT
				strategy_take_profit_price = current_price.price - (current_price.atr * 1.5)
				strategy_stop_loss_price = current_price.price + current_price.atr
				notify_line(
					'\n\nENTER SHORT STRATEGY\n\nEnter short strategy of BTC/BUSD\nprice = {}\nquantity = {}'.format(
						current_price.price, qty))
				should_update_balance = True
		elif opening_strategy == FuturesTradingStrategy.LONG:
			if current_price.price >= strategy_take_profit_price:
				print('Take profit from long strategy with price={}'.format(current_price.price))
				sell_market_order(COIN_SYMBOL, qty)
				opening_strategy = FuturesTradingStrategy.INACTIVE
				notify_line(
					'\n\nTAKE PROFIT\n\nTake profit from long strategy of BTC/BUSD\nprice = {}\nquantity = {}'.format(
						current_price.price, qty))
				should_update_balance = True
			elif current_price.price <= strategy_stop_loss_price:
				print('Cut loss from long strategy with price={}'.format(current_price.price))
				sell_market_order(COIN_SYMBOL, qty)
				opening_strategy = FuturesTradingStrategy.INACTIVE
				notify_line('\n\nCUT LOSS\n\nCut loss from long strategy of BTC/BUSD\nprice = {}\nquantity = {}'.format(
					current_price.price, qty))
				should_update_balance = True
			else:
				print('Holding long...')
		elif opening_strategy == FuturesTradingStrategy.SHORT:
			if current_price.price <= strategy_take_profit_price:
				print('Take profit from short strategy with price={}'.format(current_price.price))
				buy_market_order(COIN_SYMBOL, qty)
				opening_strategy = FuturesTradingStrategy.INACTIVE
				notify_line(
					'\n\nTAKE PROFIT\n\nTake profit from short strategy of BTC/BUSD\nprice = {}\nquantity = {}'.format(
						current_price.price, qty))
				should_update_balance = True
			elif current_price.price >= strategy_stop_loss_price:
				print('Cut loss from short strategy with price={}'.format(current_price.price))
				buy_market_order(COIN_SYMBOL, qty)
				opening_strategy = FuturesTradingStrategy.INACTIVE
				notify_line(
					'\n\nCUT LOSS\n\nCut loss from short strategy of BTC/BUSD\nprice = {}\nquantity = {}'.format(
						current_price.price, qty))
				should_update_balance = True
			else:
				print('Holding short...')
		print('------------------------------')
		print('Current Strategy: {}'.format(opening_strategy.name))
		
		balance_msg = check_account_balance()
		if should_update_balance:
			notify_line('\n\nACCOUNT BALANCE UPDATE\n\n' + '\n'.join(balance_msg))
			should_update_balance = False
		
		time.sleep(FUTURES_UPDATE_INTERVAL_IN_SECS)
	except Exception as e:
		if e.__class__.__name__ == 'KeyError':
			print('TaAPI rate limit reached.')
		elif e.__class__.__name__ == 'BinanceAPIException':
			print('Error when placing order in Binance.')
			notify_line('\n\nBOT ERROR!!\n\nError when placing order in Binance.\n\n{}'.format(e))
		elif e.__class__.__name__ in ['ConnectionError', 'MaxRetryError']:
			print('Error when trying to connect to services.')
			notify_line('\n\nBOT ERROR!!\n\nError when trying to connect to services.\n\n{}'.format(e))
		else:
			print('Unknown error!!')
			notify_line('\n\nBOT ERROR!!\n\nSomething went wrong with the bot.\n\n{}'.format(e))
		time.sleep(FUTURES_UPDATE_INTERVAL_IN_SECS)
