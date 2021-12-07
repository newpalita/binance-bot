from binance.client import Client
api_key = 'QsMBwEYN09aSTLrzGjizEi4MnKQPNO83veOtjTd6RIYNXGE4o6D18Ice81v9N8Kw'
api_secret = 'c87mIXGhNbIyKr1BbkWFZPF1g5jP8FLtjgq27HiPcrvbWqP19lKS2fGvBUoTw7eh'
client = Client(api_key, api_secret)
klines = client.get_historical_klines("BTCBUSD", Client.KLINE_INTERVAL_1MINUTE, "1 day ago UTC")
print(klines)