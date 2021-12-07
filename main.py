from binance.client import Client
import time
api_key = 'QsMBwEYN09aSTLrzGjizEi4MnKQPNO83veOtjTd6RIYNXGE4o6D18Ice81v9N8Kw'
api_secret = 'c87mIXGhNbIyKr1BbkWFZPF1g5jP8FLtjgq27HiPcrvbWqP19lKS2fGvBUoTw7eh'
lineApiKey = "nJrMOZNys2UUNgvchss5GKXfK1s8mcXTEWag7tTzW3B"

client = Client(api_key, api_secret)
rate = 34.00
mycoin = ['BTCUSDT']

# depth = client.get_order_book(symbol='BTCUSDT')
# print(depth)
while True:
    prices = client.get_all_tickers()
    for p in prices:
        for c in mycoin:
            sym = c
            if p['symbol'] == 'BTCUSDT':
                pc = float(p['price'])
                print('coin: {} price: {}'.format(sym,pc))
                cal = pc*rate
                print('in THB: {:,.8f}'.format(cal))
    time.sleep (0.2)
