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
line_api_key = "nJrMOZNys2UUNgvchss5GKXfK1s8mcXTEWag7tTzW3B"
line_api_headers = {'content-type': 'application/x-www-form-urlencoded', 'Authorization': 'Bearer ' + line_api_key}

FUTURES_API_KEY = 'QsMBwEYN09aSTLrzGjizEi4MnKQPNO83veOtjTd6RIYNXGE4o6D18Ice81v9N8Kw'
FUTURES_API_SECRET = 'c87mIXGhNbIyKr1BbkWFZPF1g5jP8FLtjgq27HiPcrvbWqP19lKS2fGvBUoTw7eh'

taapi_api_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImZpbmVyX3Jhd2luQGhvdG1haWwuY29tIiwiaWF0IjoxNjM4ODg' \
				'1NDg2LCJleHAiOjc5NDYwODU0ODZ9.I9B_mnR9AiPBrpif0iEk70AIPEYKGsdUygQD6tqKFao'
taapi_rsi_url = 'https://api.taapi.io/rsi?secret=' + taapi_api_key + '&exchange=binance&symbol=BTC/USDT&interval=1m'
taapi_atr_url = 'https://api.taapi.io/atr?secret=' + taapi_api_key + '&exchange=binance&symbol=BTC/USDT&interval=1m'

client = Client(FUTURES_API_KEY, FUTURES_API_SECRET, testnet=True)
print("Using Binance TestNet Server")
rate = 34.00

print("Setting leverage to {}".format(LEVERAGE))
client.futures_change_leverage(symbol=COIN_SYMBOL, leverage=LEVERAGE)


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


def notify_line(alert, p0, p1):
	msg = alert + get_coin_info_text(p0, p1)
	
	r = requests.post(line_api_url, headers=line_api_headers, data={'message': msg})
	print('request sent: ' + r.text)


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
	p = client.futures_symbol_ticker(symbol=COIN_SYMBOL)
	pc = float(p['price'])
	rsi = get_rsi().json()['value']
	atr = get_atr().json()['value']
	
	return Price(COIN_SYMBOL, pc, rsi, atr)


def buy_market_order(symbol, quantity):
	buy_order = client.futures_create_order(
		symbol=symbol,
		type='MARKET',
		side='BUY',
		quantity=quantity
	)
	print('buy order initiated\n{}'.format(buy_order))


def sell_market_order(symbol, quantity):
	sell_order = client.futures_create_order(
		symbol=symbol,
		type='MARKET',
		side='SELL',
		quantity=quantity
	)
	print('sell order initiated\n{}'.format(sell_order))
	
	
def check_account_balance():
	print('Current futures balance\n')
	balance = client.futures_account_balance()
	for b in balance:
		print('{}={}\n'.format(b['asset'], b['balance']))


strategy_take_profit_price = 0
strategy_stop_loss_price = 0
opening_strategy = FuturesTradingStrategy.INACTIVE
while True:
	try:
		time.sleep(FUTURES_UPDATE_INTERVAL_IN_SECS)
		current_price = fetch_price()
		
		if opening_strategy == FuturesTradingStrategy.INACTIVE:
			if current_price.rsi > RSI_HIGH_THRESHOLD:
				print('RSI above {}, enter long strategy with price={}'.format(RSI_HIGH_THRESHOLD, current_price.price))
				buy_market_order(COIN_SYMBOL, 0.001)
				opening_strategy = FuturesTradingStrategy.LONG
				strategy_take_profit_price = current_price.price + (current_price.atr * 1.5)
				strategy_stop_loss_price = current_price.price - current_price.atr
			elif current_price.rsi < RSI_LOW_THRESHOLD:
				print('RSI below {}, enter short strategy with price={}'.format(RSI_LOW_THRESHOLD, current_price.price))
				sell_market_order(COIN_SYMBOL, 0.001)
				opening_strategy = FuturesTradingStrategy.SHORT
				strategy_take_profit_price = current_price.price - (current_price.atr * 1.5)
				strategy_stop_loss_price = current_price.price + current_price.atr
		elif opening_strategy == FuturesTradingStrategy.LONG:
			if current_price.price >= strategy_take_profit_price:
				print('Take profit from long strategy with price={}'.format(current_price.price))
				sell_market_order(COIN_SYMBOL, 0.001)
				opening_strategy = FuturesTradingStrategy.INACTIVE
			elif current_price.atr <= strategy_stop_loss_price:
				print('Cut loss from long strategy with price={}'.format(current_price.price))
				sell_market_order(COIN_SYMBOL, 0.001)
				opening_strategy = FuturesTradingStrategy.INACTIVE
			else:
				print('Holding long...')
		elif opening_strategy == FuturesTradingStrategy.SHORT:
			if current_price.atr <= strategy_take_profit_price:
				print('Take profit from short strategy with price={}'.format(current_price.price))
				buy_market_order(COIN_SYMBOL, 0.001)
				opening_strategy = FuturesTradingStrategy.INACTIVE
			elif current_price.atr >= strategy_stop_loss_price:
				print('Cut loss from short strategy with price={}'.format(current_price.price))
				buy_market_order(COIN_SYMBOL, 0.001)
				opening_strategy = FuturesTradingStrategy.INACTIVE
			else:
				print('Holding short...')
		else:
			check_account_balance()
	except KeyError:
		print('TaAPI rate limit reached')
