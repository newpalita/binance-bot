import time
from enum import Enum

import requests
from binance.client import Client

COIN_SYMBOL = 'BTCUSDT'
LEVERAGE = 1

RSI_HIGH_THRESHOLD = 70
RSI_LOW_THRESHOLD = 30
FUTURES_UPDATE_INTERVAL_IN_SECS = 60

line_api_url = 'https://notify-api.line.me/api/notify'
line_api_key = "sbuoWm0RPYoGYaPEBrpnaL648QnKYxkiHFlHn2NlP6z"
line_api_headers = {'content-type': 'application/x-www-form-urlencoded', 'Authorization': 'Bearer ' + line_api_key}

BINANCE_TEST_API_KEY = 'etOy0t6h6rMnn1J65at9Hj1ZuAn92MBWS9r2JHgajKzYegtR2hYgTh4rB1Vnn2tG'
BINANCE_TEST_API_SECRET = 'uevcP5yZVcUrd8wiZav4ewd8PVY26iR1RPJVE4SwxcM2efqcQ1FrI7r9Jq4FccLa'

taapi_api_key_rsi = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImZpbmVyX3Jhd2luQGhvdG1haWwuY29tIiwiaWF0IjoxNjM' \
					'4ODg1NDg2LCJleHAiOjc5NDYwODU0ODZ9.I9B_mnR9AiPBrpif0iEk70AIPEYKGsdUygQD6tqKFao'
taapi_api_key_atr = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6Im5ld3BhbGl0YUBnbWFpbC5jb20iLCJpYXQiOjE2NDA3MTE' \
					'3MjMsImV4cCI6Nzk0NzkxMTcyM30.uY7vhsO7mnknvO4vjPoBVL92ra8H8nD7gDq4fBnRCig'
taapi_rsi_url = 'https://api.taapi.io/rsi?secret=' + taapi_api_key_rsi + '&exchange=binance&symbol=BTC/USDT&interval=1m'
taapi_atr_url = 'https://api.taapi.io/atr?secret=' + taapi_api_key_atr + '&exchange=binance&symbol=BTC/USDT&interval=1m'

client = Client(BINANCE_TEST_API_KEY, BINANCE_TEST_API_SECRET, testnet=True)
print("Using Binance TestNet Server")
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
	print('Current futures balance')
	balance = client.get_account()['balances']
	msg = []
	for b in balance:
		if b['asset'] in ['BTC', 'USDT']:
			print('{}={}'.format(b['asset'], b['free']))
			msg.append('{}={}'.format(b['asset'], b['free']))
	return msg


qty = 0.01
strategy_take_profit_price = 0
strategy_stop_loss_price = 0
opening_strategy = FuturesTradingStrategy.INACTIVE
tick_count = 0
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
				notify_line('ENTER LONG STRATEGY\n\nEnter long strategy of BTC/USDT\nprice = {}\nquantity = {}'.format(
					current_price.price, qty))
			elif current_price.rsi < RSI_LOW_THRESHOLD:
				print('RSI below {}, enter short strategy with price={}'.format(RSI_LOW_THRESHOLD, current_price.price))
				sell_market_order(COIN_SYMBOL, qty)
				opening_strategy = FuturesTradingStrategy.SHORT
				strategy_take_profit_price = current_price.price - (current_price.atr * 1.5)
				strategy_stop_loss_price = current_price.price + current_price.atr
				notify_line(
					'ENTER SHORT STRATEGY\n\nEnter short strategy of BTC/USDT\nprice = {}\nquantity = {}'.format(
						current_price.price, qty))
		elif opening_strategy == FuturesTradingStrategy.LONG:
			if current_price.price >= strategy_take_profit_price:
				print('Take profit from long strategy with price={}'.format(current_price.price))
				sell_market_order(COIN_SYMBOL, qty)
				opening_strategy = FuturesTradingStrategy.INACTIVE
				notify_line(
					'TAKE PROFIT\n\nTake profit from long strategy of BTC/USDT\nprice = {}\nquantity = {}'.format(
						current_price.price, qty))
			elif current_price.atr <= strategy_stop_loss_price:
				print('Cut loss from long strategy with price={}'.format(current_price.price))
				sell_market_order(COIN_SYMBOL, qty)
				opening_strategy = FuturesTradingStrategy.INACTIVE
				notify_line('CUT LOSS\n\nCut loss from long strategy of BTC/USDT\nprice = {}\nquantity = {}'.format(
					current_price.price, qty))
			else:
				print('Holding long...')
		elif opening_strategy == FuturesTradingStrategy.SHORT:
			if current_price.atr <= strategy_take_profit_price:
				print('Take profit from short strategy with price={}'.format(current_price.price))
				buy_market_order(COIN_SYMBOL, qty)
				opening_strategy = FuturesTradingStrategy.INACTIVE
				notify_line(
					'TAKE PROFIT\n\nTake profit from short strategy of BTC/USDT\nprice = {}\nquantity = {}'.format(
						current_price.price, qty))
			elif current_price.atr >= strategy_stop_loss_price:
				print('Cut loss from short strategy with price={}'.format(current_price.price))
				buy_market_order(COIN_SYMBOL, qty)
				opening_strategy = FuturesTradingStrategy.INACTIVE
				notify_line('CUT LOSS\n\nCut loss from short strategy of BTC/USDT\nprice = {}\nquantity = {}'.format(
					current_price.price, qty))
			else:
				print('Holding short...')
		print('------------------------------')
		print('Current Strategy: {}'.format(opening_strategy.name))
		
		balance_msg = check_account_balance()
		if tick_count >= 60:
			notify_line('ACCOUNT BALANCE UPDATE\n\n' + '\n'.join(balance_msg))
			tick_count = 0
		else:
			tick_count += 1
			
		time.sleep(FUTURES_UPDATE_INTERVAL_IN_SECS)
	except KeyError:
		print('TaAPI rate limit reached')
