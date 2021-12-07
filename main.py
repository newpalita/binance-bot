import time

import requests
from binance.client import Client

line_url = 'https://notify-api.line.me/api/notify'
line_api_key = "nJrMOZNys2UUNgvchss5GKXfK1s8mcXTEWag7tTzW3B"
headers = {'content-type': 'application/x-www-form-urlencoded', 'Authorization': 'Bearer ' + line_api_key}

api_key = 'QsMBwEYN09aSTLrzGjizEi4MnKQPNO83veOtjTd6RIYNXGE4o6D18Ice81v9N8Kw'
api_secret = 'c87mIXGhNbIyKr1BbkWFZPF1g5jP8FLtjgq27HiPcrvbWqP19lKS2fGvBUoTw7eh'

client = Client(api_key, api_secret)
rate = 34.00
my_coin = ['BTCUSDT']


def fetch_price():
	prices = client.get_all_tickers()
	for p in prices:
		for sym in my_coin:
			if p['symbol'] == sym:
				pc = float(p['price'])
				cal = pc * rate
				
				return Price(sym, pc, cal)


class Price:
	def __init__(self, s, p, cp):
		self.symbol = s
		self.price = p
		self.converted_price = cp
	
	def notify_line(self):
		msg = 'coin: {} price: {}'.format(self.symbol, self.price) \
			  + '\nin THB: {:,.2f}'.format(self.converted_price)
		
		r = requests.post(line_url, headers=headers, data={'message': msg})
		print('request sent: ' + r.text)


while True:
	p1 = fetch_price()
	time.sleep(5)
	p2 = fetch_price()
	
	p2.notify_line()
	print((p2.price - p1.price) / p1.price)
