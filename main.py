import json
import requests
import time
from binance.client import Client

RSI_HIGH_THRESHOLD = 70
RSI_LOW_THRESHOLD = 30
PERCENTAGE_CHANGE_THRESHOLD = 1
ALERT_UPDATE_INTERVAL_IN_SECS = 60
REGULAR_PRICE_UPDATE_INTERVAL_COUNT = 30

line_api_url = 'https://notify-api.line.me/api/notify'
line_api_key = "nJrMOZNys2UUNgvchss5GKXfK1s8mcXTEWag7tTzW3B"
line_api_headers = {'content-type': 'application/x-www-form-urlencoded', 'Authorization': 'Bearer ' + line_api_key}

binance_api_key = 'QsMBwEYN09aSTLrzGjizEi4MnKQPNO83veOtjTd6RIYNXGE4o6D18Ice81v9N8Kw'
binance_api_secret = 'c87mIXGhNbIyKr1BbkWFZPF1g5jP8FLtjgq27HiPcrvbWqP19lKS2fGvBUoTw7eh'

taapi_api_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImZpbmVyX3Jhd2luQGhvdG1haWwuY29tIiwiaWF0IjoxNjM4ODg' \
				'1NDg2LCJleHAiOjc5NDYwODU0ODZ9.I9B_mnR9AiPBrpif0iEk70AIPEYKGsdUygQD6tqKFao'
taapi_api_url = 'https://api.taapi.io/rsi?secret=' + taapi_api_key + '&exchange=binance&symbol=BTC/USDT&interval=1m'

client = Client(binance_api_key, binance_api_secret)
rate = 34.00
my_coin = ['BTCUSDT']


class Price:
	def __init__(self, s, p, cp, rsi):
		self.symbol = s
		self.price = p
		self.converted_price = cp
		self.rsi = rsi


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
	r = requests.get(taapi_api_url)
	return r


def fetch_price():
	prices = client.get_all_tickers()
	for p in prices:
		for sym in my_coin:
			if p['symbol'] == sym:
				pc = float(p['price'])
				cal = pc * rate
				rsi = get_rsi().json()['value']

				return Price(sym, pc, cal, rsi)


count = 0
past_price = fetch_price()
while True:
	try:
		time.sleep(ALERT_UPDATE_INTERVAL_IN_SECS)
		current_price = fetch_price()

		changes = get_percentage_change(past_price.price, current_price.price)

		if changes > PERCENTAGE_CHANGE_THRESHOLD:
			notify_line('\n\nCHANGES ABOVE {}% ALERT!\n\n'.format(PERCENTAGE_CHANGE_THRESHOLD), past_price,
						current_price)
		elif current_price.rsi > RSI_HIGH_THRESHOLD:
			notify_line('\n\nRSI ABOVE {} ALERT!\n\n'.format(RSI_HIGH_THRESHOLD), past_price, current_price)
		elif current_price.rsi < RSI_LOW_THRESHOLD:
			notify_line('\n\nRSI BELOW {} ALERT!\n\n'.format(RSI_LOW_THRESHOLD), past_price, current_price)
		else:
			print('Everything is normal; no alert needed')

		past_price = current_price

		if count >= REGULAR_PRICE_UPDATE_INTERVAL_COUNT:
			notify_line('\n\nPrice update\n\n', past_price, current_price)
			count = 0
		else:
			count += count
	except KeyError:
		print('TaAPI rate limit reached')
