# Deribit WS Request Stress
This is an experimental tool that explores Deribit WebSocket request rate limit.

I used the following links and docs:
1. https://insights.deribit.com/dev-hub/how-to-maintain-and-authenticate-a-websocket-connection-to-deribit-python/
2. https://docs.deribit.com/#overview
3. https://www.deribit.com/kb/deribit-rate-limits

Most of the code is borrowed from https://github.com/ElliotP123/crypto-exchange-code-samples.git

The difference from the original implementation - this tool repeats subscription/unsubscription many times instead of subscribing to a single instrument/channel. For instance, in this example it does 100 sub/unsub iterations for 3 instruments ("BTC-PERPETUAL", "BTC_USDC", "ETH-PERPETUAL").

There is an option to do it with or without rate limiter.

## How to run
Please edit the dbt-ws-authenticated-example.py file and set `client_id` and `client_secret` variable.

... assuming you already have python3 env ...
```
$ pip3 install websockets # install dependency
$ python3 ./dbt-ws-authenticated-example.py
...
```

Typical output for the run without rate limiter (i.e. `rate_limit_request_per_sec=0`) - you can see "broken websocket" after 20-30 requests:
```
2024-08-06 21:48:31 | INFO | No rate limit set
2024-08-06 21:48:32 | INFO | Successfully authenticated WebSocket Connection
2024-08-06 21:48:32 | INFO | Request iteration 0
2024-08-06 21:48:32 | INFO | 	subscribe : BTC-PERPETUAL
2024-08-06 21:48:32 | INFO | 	subscribe : BTC_USDC
2024-08-06 21:48:32 | INFO | 	subscribe : ETH-PERPETUAL
2024-08-06 21:48:32 | INFO | Request iteration 1
2024-08-06 21:48:32 | INFO | 	unsubscribe : BTC-PERPETUAL
2024-08-06 21:48:32 | INFO | 	unsubscribe : BTC_USDC
2024-08-06 21:48:32 | INFO | 	unsubscribe : ETH-PERPETUAL
...
2024-08-06 21:48:32 | INFO | Request iteration 99
2024-08-06 21:48:32 | INFO | 	unsubscribe : BTC-PERPETUAL
2024-08-06 21:48:32 | INFO | 	unsubscribe : BTC_USDC
2024-08-06 21:48:32 | INFO | 	unsubscribe : ETH-PERPETUAL
2024-08-06 21:48:33 | INFO | Subscription reply : {'jsonrpc': '2.0', 'id': 1000, 'result': ['book.BTC-PERPETUAL.100ms'], 'usIn': 1722952112929191, 'usOut': 1722952112929333, 'usDiff': 142, 'testnet': True}
2024-08-06 21:48:33 | INFO | Subscription reply : {'jsonrpc': '2.0', 'id': 1001, 'result': ['book.BTC_USDC.100ms'], 'usIn': 1722952112929586, 'usOut': 1722952112929670, 'usDiff': 84, 'testnet': True}
2024-08-06 21:48:33 | INFO | Subscription reply : {'jsonrpc': '2.0', 'id': 1002, 'result': ['book.ETH-PERPETUAL.100ms'], 'usIn': 1722952112929722, 'usOut': 1722952112929833, 'usDiff': 111, 'testnet': True}
2024-08-06 21:48:33 | INFO | Unsubscription reply : {'jsonrpc': '2.0', 'id': 2000, 'result': ['book.BTC-PERPETUAL.100ms'], 'usIn': 1722952112929948, 'usOut': 1722952112929989, 'usDiff': 41, 'testnet': True}
2024-08-06 21:48:33 | INFO | Unsubscription reply : {'jsonrpc': '2.0', 'id': 2001, 'result': ['book.BTC_USDC.100ms'], 'usIn': 1722952112930040, 'usOut': 1722952112930069, 'usDiff': 29, 'testnet': True}
...
2024-08-06 21:48:33 | INFO | Subscription reply : {'jsonrpc': '2.0', 'id': 1014, 'result': ['book.ETH-PERPETUAL.100ms'], 'usIn': 1722952112932633, 'usOut': 1722952112932674, 'usDiff': 41, 'testnet': True}
2024-08-06 21:48:33 | INFO | Unsubscription reply : {'jsonrpc': '2.0', 'id': 2012, 'result': ['book.BTC-PERPETUAL.100ms'], 'usIn': 1722952112932716, 'usOut': 1722952112932761, 'usDiff': 45, 'testnet': True}
2024-08-06 21:48:33 | INFO | WebSocket connection has broken.
```

And similar run but with rate limiter (i.e. `rate_limit_request_per_sec=5`) - this time you can see that all requests were sent successfully:
```
$ python3 ./dbt-ws-authenticated-example.py 
2024-08-06 21:51:00 | INFO | Rate limit set to 5 requests per second
2024-08-06 21:51:02 | INFO | Successfully authenticated WebSocket Connection
2024-08-06 21:51:02 | INFO | Request iteration 0
2024-08-06 21:51:02 | INFO | 	subscribe : BTC-PERPETUAL
2024-08-06 21:51:02 | INFO | 	subscribe : BTC_USDC
2024-08-06 21:51:02 | INFO | 	subscribe : ETH-PERPETUAL
2024-08-06 21:51:02 | INFO | Request iteration 1
2024-08-06 21:51:02 | INFO | 	unsubscribe : BTC-PERPETUAL
2024-08-06 21:51:02 | INFO | 	unsubscribe : BTC_USDC
2024-08-06 21:51:02 | INFO | 	unsubscribe : ETH-PERPETUAL
...
2024-08-06 21:51:02 | INFO | Request iteration 99
2024-08-06 21:51:02 | INFO | 	unsubscribe : BTC-PERPETUAL
2024-08-06 21:51:02 | INFO | 	unsubscribe : BTC_USDC
2024-08-06 21:51:02 | INFO | 	unsubscribe : ETH-PERPETUAL
2024-08-06 21:51:02 | INFO | Subscription reply : {'jsonrpc': '2.0', 'id': 1000, 'result': ['book.BTC-PERPETUAL.100ms'], 'usIn': 1722952262457059, 'usOut': 1722952262457185, 'usDiff': 126, 'testnet': True}
2024-08-06 21:51:02 | INFO | Subscription reply : {'jsonrpc': '2.0', 'id': 1001, 'result': ['book.BTC_USDC.100ms'], 'usIn': 1722952262657174, 'usOut': 1722952262657254, 'usDiff': 80, 'testnet': True}
2024-08-06 21:51:02 | INFO | Subscription reply : {'jsonrpc': '2.0', 'id': 1002, 'result': ['book.ETH-PERPETUAL.100ms'], 'usIn': 1722952262858009, 'usOut': 1722952262858081, 'usDiff': 72, 'testnet': True}
2024-08-06 21:51:03 | INFO | Unsubscription reply : {'jsonrpc': '2.0', 'id': 2000, 'result': ['book.BTC-PERPETUAL.100ms'], 'usIn': 1722952263059735, 'usOut': 1722952263059804, 'usDiff': 69, 'testnet': True}
2024-08-06 21:51:03 | INFO | Unsubscription reply : {'jsonrpc': '2.0', 'id': 2001, 'result': ['book.BTC_USDC.100ms'], 'usIn': 1722952263261325, 'usOut': 1722952263261404, 'usDiff': 79, 'testnet': True}
...
2024-08-06 21:52:02 | INFO | Subscription reply : {'jsonrpc': '2.0', 'id': 1149, 'result': ['book.ETH-PERPETUAL.100ms'], 'usIn': 1722952322032586, 'usOut': 1722952322032677, 'usDiff': 91, 'testnet': True}
2024-08-06 21:52:02 | INFO | Unsubscription reply : {'jsonrpc': '2.0', 'id': 2147, 'result': ['book.BTC-PERPETUAL.100ms'], 'usIn': 1722952322234313, 'usOut': 1722952322234387, 'usDiff': 74, 'testnet': True}
2024-08-06 21:52:02 | INFO | Unsubscription reply : {'jsonrpc': '2.0', 'id': 2148, 'result': ['book.BTC_USDC.100ms'], 'usIn': 1722952322435563, 'usOut': 1722952322435634, 'usDiff': 71, 'testnet': True}
2024-08-06 21:52:02 | INFO | Unsubscription reply : {'jsonrpc': '2.0', 'id': 2149, 'result': ['book.ETH-PERPETUAL.100ms'], 'usIn': 1722952322635878, 'usOut': 1722952322635961, 'usDiff': 83, 'testnet': True}
...
```

## Simple Rate Limiter
I use very naive rate limiter implementation, see `TaskScheduler`. `TaskScheduler` is just a queue of tasks that are delayed by the fixed interval - which is not the best way to implement "credit based" logic of Deribit rate limiter (but it works).
