import requests
import time
from binance.client import Client

line_url = 'https://notify-api.line.me/api/notify'
line_api_key = "nJrMOZNys2UUNgvchss5GKXfK1s8mcXTEWag7tTzW3B"
headers = {'content-type': 'application/x-www-form-urlencoded', 'Authorization': 'Bearer ' + line_api_key}

api_key = 'QsMBwEYN09aSTLrzGjizEi4MnKQPNO83veOtjTd6RIYNXGE4o6D18Ice81v9N8Kw'
api_secret = 'c87mIXGhNbIyKr1BbkWFZPF1g5jP8FLtjgq27HiPcrvbWqP19lKS2fGvBUoTw7eh'

client = Client(api_key, api_secret)
rate = 34.00
mycoin = ['BTCUSDT']


# depth = client.get_order_book(symbol='BTCUSDT')
# print(depth)
def fetch_price():
	prices = client.get_all_tickers()
	for p in prices:
		for c in mycoin:
			sym = c
			if p['symbol'] == 'BTCUSDT':
				pc = float(p['price'])
				cal = pc * rate
				msg = 'coin: {} price: {}'.format(sym, pc) \
					  + '\nin THB: {:,.2f}'.format(cal)

				r = requests.post(line_url, headers=headers, data={'message': msg})
				print(r.text)
				return pc


while True:
	p1 = fetch_price()
	time.sleep(5)
	p2 = fetch_price()
	print((p2 - p1) / p1)
