"""
Description:
    Deribit WebSocket Asyncio Example.

    - Authenticated connection.

Usage:
    python3.12 dbt-ws-authenticated-example.py

Requirements:
    - websocket-client >= 1.2.1
"""

# built ins
import asyncio
import sys
import json
import logging
from typing import Dict
from datetime import datetime, timedelta, timezone
import websockets
from collections import deque
from enum import Enum

class ReqID(Enum):
    HEARTBEAT = 10
    SET_HEARTBEAT = 11
    AUTH = 20
    ID_RANGE = 500
    SUBSCRIBE = 1000
    UNSUBSCRIBE = 2000


class TaskScheduler:
    def __init__(self, delay=0.2):  # delay for 5 requests per second
        self.tasks = deque()
        self.delay = delay
        self.new_task_event = asyncio.Event()

    def add_task(self, task):
        self.tasks.append(task)
        self.new_task_event.set()  # Resume the process_tasks coroutine

    async def process_tasks(self):
        while True:
            if self.tasks:
                task = self.tasks.popleft()
                await task
                await asyncio.sleep(self.delay)
            else:
                await self.new_task_event.wait()
                self.new_task_event.clear()


class Feeder:
    def __init__(
        self,
        ws_connection_url: str,
        client_id: str,
        client_secret: str,
        instruments: list,
        rate_limit_request_per_sec: int,
        request_iterations: int
    ) -> None:

        # Instance Variables
        self.ws_connection_url: str = ws_connection_url
        self.client_id: str = client_id
        self.client_secret: str = client_secret
        self.websocket_client: websockets.WebSocketClientProtocol = None
        self.refresh_token: str = None
        self.refresh_token_expiry_time: int = None

        if rate_limit_request_per_sec and rate_limit_request_per_sec > 0:
            logging.info("Rate limit set to " + str(rate_limit_request_per_sec) + " requests per second")
            self.scheduler = TaskScheduler(delay = 1. / rate_limit_request_per_sec)
        else:
            logging.info("No rate limit set")
            self.scheduler = None

        if request_iterations:
            self.request_iterations = request_iterations
        else:
            raise ValueError("request_iterations must be > 0")
        self.sub_id = 0
        self.unsub_id = 0
        if instruments:
            self.instruments = instruments
        else:
            raise ValueError("No instruments provided")

        # Start Primary Coroutine
        asyncio.run(self.ws_manager())

    async def ws_manager(self) -> None:
        async with websockets.connect(
            self.ws_connection_url,
            ping_interval=None,
            compression=None,
            close_timeout=60,
        ) as self.websocket_client:

            if self.scheduler:
                asyncio.create_task(self.scheduler.process_tasks())

            # Authenticate WebSocket Connection
            await self.ws_auth()

            # Establish Heartbeat
            await self.establish_heartbeat()

            # Start Authentication Refresh Task
            asyncio.create_task(self.ws_refresh_auth())

            while self.websocket_client.open:
                message: bytes = await self.websocket_client.recv()
                message: Dict = json.loads(message)
                #logging.info(message)

                if "id" in list(message):
                    req_id = message["id"]
                    if req_id == ReqID.AUTH.value:
                        if self.refresh_token is None:
                            logging.info(
                                "Successfully authenticated WebSocket Connection"
                            )
                        else:
                            logging.info(
                                "Successfully refreshed the authentication of the WebSocket Connection"
                            )

                        self.stress_test_subscribe()

                        self.refresh_token = message["result"]["refresh_token"]

                        # Refresh Authentication well before the required datetime
                        if message["testnet"]:
                            expires_in: int = 300
                        else:
                            expires_in: int = message["result"]["expires_in"] - 240

                        self.refresh_token_expiry_time = datetime.now(
                            timezone.utc
                        ) + timedelta(seconds=expires_in)

                    elif req_id == ReqID.HEARTBEAT.value or req_id == ReqID.SET_HEARTBEAT.value:
                        # Avoid logging Heartbeat messages
                        pass
                    elif req_id >= ReqID.SUBSCRIBE.value and message["id"] < (ReqID.SUBSCRIBE.value + ReqID.ID_RANGE.value):
                        logging.info(f"Subscription reply : {message}")
                    elif req_id >= ReqID.UNSUBSCRIBE.value and message["id"] < (ReqID.UNSUBSCRIBE.value + ReqID.ID_RANGE.value):
                        logging.info(f"Unsubscription reply : {message}")
                    else:
                        logging.info(f"Unknown message : {message}")

                elif "method" in list(message):
                    # Respond to Heartbeat Message
                    if message["method"] == "heartbeat":
                        await self.heartbeat_response()
                    elif message["method"] == "subscription":
                        #logging.info(message)
                        pass

            else:
                logging.info("WebSocket connection has broken.")
                sys.exit(1)

    async def establish_heartbeat(self) -> None:
        """
        Requests DBT's `public/set_heartbeat` to
        establish a heartbeat connection.
        """
        msg: Dict = {
            "jsonrpc": "2.0",
            "id": ReqID.SET_HEARTBEAT.value,
            "method": "public/set_heartbeat",
            "params": {"interval": 10},
        }

        await self.websocket_client.send(json.dumps(msg))

    async def heartbeat_response(self) -> None:
        """
        Sends the required WebSocket response to
        the Deribit API Heartbeat message.
        """
        msg: Dict = {
            "jsonrpc": "2.0",
            "id": ReqID.HEARTBEAT.value,
            "method": "public/test",
            "params": {},
        }

        await self.websocket_client.send(json.dumps(msg))

    async def ws_auth(self) -> None:
        """
        Requests DBT's `public/auth` to
        authenticate the WebSocket Connection.
        """
        msg: Dict = {
            "jsonrpc": "2.0",
            "id": ReqID.AUTH.value,
            "method": "public/auth",
            "params": {
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
        }

        await self.websocket_client.send(json.dumps(msg))

    async def ws_refresh_auth(self) -> None:
        """
        Requests DBT's `public/auth` to refresh
        the WebSocket Connection's authentication.
        """
        while True:
            if self.refresh_token_expiry_time is not None:
                if datetime.now(timezone.utc) > self.refresh_token_expiry_time:
                    msg: Dict = {
                        "jsonrpc": "2.0",
                        "id": ReqID.AUTH.value,
                        "method": "public/auth",
                        "params": {
                            "grant_type": "refresh_token",
                            "refresh_token": self.refresh_token,
                        },
                    }

                    await self.websocket_client.send(json.dumps(msg))

            await asyncio.sleep(150)

    async def ws_operation(self, operation: str, ws_channel: str) -> None:
        """
        Requests `public/subscribe` or `public/unsubscribe`
        to DBT's API for the specific WebSocket Channel.
        """
        #await asyncio.sleep(5)

        if operation == "subscribe":
            req_id = ReqID.SUBSCRIBE.value + self.sub_id
            self.sub_id += 1
            if self.sub_id >= ReqID.ID_RANGE.value:
                self.sub_id = 0
        elif operation == "unsubscribe":
            req_id = ReqID.UNSUBSCRIBE.value + self.unsub_id
            self.unsub_id += 1
            if self.unsub_id >= ReqID.ID_RANGE.value:
                self.unsub_id = 0

        msg: Dict = {
            "jsonrpc": "2.0",
            "method": f"public/{operation}",
            "id": req_id,
            "params": {"channels": [ws_channel]},
        }

        await self.websocket_client.send(json.dumps(msg))
    
    def stress_test_subscribe(self):
        is_subscribed = False
        for count in range(self.request_iterations):
            operation = "subscribe" if not is_subscribed else "unsubscribe"
            logging.info(f"Request iteration {count}")
            for instrument in self.instruments:
                logging.info(f"\t{operation} : {instrument}")
                self.create_task(
                        self.ws_operation(operation=operation, ws_channel=f"book.{instrument}.100ms")
                )
            is_subscribed = not is_subscribed
    
    def create_task(self, task):
        if self.scheduler:
            self.scheduler.add_task(task)
        else:
            asyncio.create_task(task)

if __name__ == "__main__":
    # Logging
    logging.basicConfig(
        level="INFO",
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # DBT LIVE WebSocket Connection URL
    # ws_connection_url: str = 'wss://www.deribit.com/ws/api/v2'
    # DBT TEST WebSocket Connection URL
    ws_connection_url: str = "wss://test.deribit.com/ws/api/v2"

    # DBT Client ID
    client_id: str = "***"
    # DBT Client Secret
    client_secret: str = "***"

    feeder = Feeder(
        ws_connection_url=ws_connection_url,
        client_id=client_id,
        client_secret=client_secret,
        instruments=["BTC-PERPETUAL", "BTC_USDC", "ETH-PERPETUAL"],
        rate_limit_request_per_sec=5, #set to 0 for no rate limit
        request_iterations=100
    )
