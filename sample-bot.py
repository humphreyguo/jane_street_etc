#!/usr/bin/env python3
# ~~~~~==============   HOW TO RUN   ==============~~~~~
# 1) Configure things in CONFIGURATION section
# 2) Change permissions: chmod +x bot.py
# 3) Run in loop: while true; do ./bot.py --test prod-like; sleep 1; done

import argparse
from collections import deque
from enum import Enum
import time
import socket
import json

# ~~~~~============== CONFIGURATION  ==============~~~~~
# Replace "REPLACEME" with your team name!
team_name = "Doge"

# ~~~~~============== MAIN LOOP ==============~~~~~

# You should put your code here! We provide some starter code as an example,
# but feel free to change/remove/edit/update any of it as you'd like. If you
# have any questions about the starter code, or what to do next, please ask us!
#
# To help you get started, the sample code below tries to buy BOND for a low
# price, and it prints the current prices for VALE every second. The sample
# code is intended to be a working example, but it needs some improvement
# before it will start making good trades!


def main():
    args = parse_arguments()

    exchange = ExchangeConnection(args=args)

    # Store and print the "hello" message received from the exchange. This
    # contains useful information about your positions. Normally you start with
    # all positions at zero, but if you reconnect during a round, you might
    # have already bought/sold symbols and have non-zero positions.
    hello_message = exchange.read_message()
    print("First message from exchange:", hello_message)

    # Send an order for BOND at a good price, but it is low enough that it is
    # unlikely it will be traded against. Maybe there is a better price to
    # pick? Also, you will need to send more orders over time.
    exchange.send_add_message(order_id=1, symbol="BOND", dir=Dir.BUY, price=990, size=1)

    # Set up some variables to track the bid and ask price of a symbol. Right
    # now this doesn't track much information, but it's enough to get a sense
    # of the VALE market.
    vale_bid_price, vale_ask_price = None, None
    vale_last_print_time = time.time()

    # Here is the main loop of the program. It will continue to read and
    # process messages in a loop until a "close" message is received. You
    # should write to code handle more types of messages (and not just print
    # the message). Feel free to modify any of the starter code below.
    #
    # Note: a common mistake people make is to call write_message() at least
    # once for every read_message() response.
    #
    # Every message sent to the exchange generates at least one response
    # message. Sending a message in response to every exchange message will
    # cause a feedback loop where your bot's messages will quickly be
    # rate-limited and ignored. Please, don't do that!
    
    buyOrders = deque()
    sellOrders = deque()
    
    valeSell = 999999
    valeSize = 999999
    ownedVale = 0
    orderId = 1
    
    valebzPrice = 0
    profits = 0
    
    while True:
        
        # print(buyOrders)
        # print(sellOrders)
        
        while len(buyOrders) > 0:
            msg = {
                "type":"cancel",
                "order_id": buyOrders.popleft()["order_id"]
            }
            exchange._write_message(msg)

        while len(sellOrders) > 0:
            msg = {
                "type":"cancel",
                "order_id": sellOrders.popleft()["order_id"]
            }
            exchange._write_message(msg)
            
        message = exchange.read_message()
        
        if message["type"] == "close":
            print("The round has ended")
            break
        elif message["type"] == "error":
            print(message)
        elif message["type"] == "reject":
            print(message)
        elif message["type"] == "fill":
            print(message)
        elif message["type"] == "book":
            symbol = message['symbol']
            
            buy = message["buy"]
            sell = message["sell"]
            
            if symbol == "VALE":

                def best_price(side):
                    if message[side]:
                        return message[side][0][0]
                def best_price_amount(side):
                    if message[side]:
                        return message[side][0][1]

                vale_bid_price = best_price("buy")
                vale_ask_price = best_price("sell")
                
                valeSell = vale_ask_price
                now = time.time()

                if now > vale_last_print_time + 1:
                    vale_last_print_time = now
                    # print(
                    #     {
                    #         "vale_bid_price": vale_bid_price,
                    #         "vale_ask_price": vale_ask_price,
                    #     }
                    # )
                if vale_bid_price and valebzPrice and vale_bid_price > valebzPrice:
                    if ownedVale > 0:
                        total_buying = best_price_amount("buy")
                        
                        
                        exchange.send_add_message(order_id=orderId, symbol="VALE", dir=Dir.SELL, price=vale_bid_price, size=total_buying)
                        sellOrders.append({"type":"add", "order_id": orderId, "symbol": "VALE", "dir": "SELL", "price": vale_bid_price, "size": ownedVale})
                        orderId += 1
                        print(f"Selling {ownedVale} Vale for {vale_bid_price}")
                        # profits += ownedVale * valeSell
                        # print(profits)
                        ownedVale -= total_buying
            if symbol == "VALBZ":

                def best_price(side):
                    if message[side]:
                        return message[side][0][0]
                
                
                for i in range(len(buy)):
                    valeSize = message["buy"][i][1]
                    # size = message[""][i][1]
                    valbz_bid_price = best_price("buy")
                    valebzPrice = valbz_bid_price
                    valbz_ask_price = best_price("sell")
                    if valbz_bid_price and valeSell:
                        if valbz_bid_price > valeSell and ownedVale < 10:
                            valeSize = min(10-ownedVale, valeSize)
                            exchange.send_add_message(order_id=orderId, symbol="VALE", dir=Dir.BUY, price=valeSell, size=valeSize)
                            sellOrders.append({"type":"add", "order_id": orderId, "symbol": "VALBZ", "dir": "BUY", "price": valbz_bid_price, "size": valeSize})
                            orderId += 1
                            ownedVale += valeSize
                            # profits -= valeSize * valeSell
                            print(f"Buying {valeSize} Vale for {valeSell}")
                            # print(profits)
                        # if valbz_bid_price > valeSell and valeSize <= 10:
                        #     exchange.send_add_message(order_id=orderId, symbol="VALE", dir=Dir.BUY, price=valeSell, size=valeSize)
                        #     sellOrders.append({"type":"add", "order_id": orderId, "symbol": "VALBZ", "dir": "BUY", "price": valbz_bid_price, "size": valeSize})
                        #     orderId += 1
                        #     exchange.send_add_message(order_id=orderId, symbol="VALE", dir=Dir.SELL, price=valbz_bid_price, size=valeSize)
                        #     sellOrders.append({"type":"add", "order_id": orderId, "symbol": "VALE", "dir": "SELL", "price": valeSell, "size": valeSize})
                        #     orderId += 1
                now = time.time()

                # if now > vale_last_print_time + 1:
                #     valbz_last_print_time = now
                #     print(
                #         {
                #             "valbz_bid_price": valbz_bid_price,
                #             "valbz_ask_price": valbz_ask_price,
                #         }
                #     )
                    
            
                
                    
            # if (len(message['buy'] > 0)) :
            #     buyPrice = message['buy'][0][0]
            
            
            if (symbol == "BOND"):
                for i in range(len(buy)):
                    if buy[i][0] > 1000:
                        # print(f"buy is{buy[i]}")
                        exchange.send_add_message(order_id=orderId, symbol="BOND", dir=Dir.SELL, price=buy[i][0], size=buy[i][1])
                        buyOrders.append({"type":"add", "order_id": orderId, "symbol": "BOND", "dir": "SELL", "price": buy[i][0], "size": buy[i][1]})
                        orderId+=1

                for i in range(len(sell)):
                    if sell[i][0] < 1000:
                        # print(sell[i])
                        exchange.send_add_message(order_id=orderId, symbol="BOND", dir=Dir.BUY, price=sell[i][0], size=sell[i][1])
                        sellOrders.append({"type":"add", "order_id": orderId, "symbol": "BOND", "dir": "BUY", "price": sell[i][0], "size": sell[i][1]})
                        orderId+=1
            
            if symbol in ["GS", "MS", "WFC", "XLF"]:
                def best_price(side):
                    if message[side]:
                        return message[side][0][0]
                
                
                exchange.send_add_message(order_id=orderId, symbol=symbol, dir=Dir.BUY, price=buy[0][0] + 1, size=100)
                sellOrders.append({"type":"add", "order_id": orderId, "symbol": symbol, "dir": "BUY", "price": sell[0][0] + 1, "size": 100})
                orderId+=1
                sellOrders.append({"type":"add", "order_id": orderId, "symbol": symbol, "dir": "SELL", "price": sell[0][0] + 10, "size": 100})
                orderId += 1
            message = exchange.read_message()
            
            # print(message) 
            # is ack message with id
            # return buy_trades + sell_trades


# ~~~~~============== PROVIDED CODE ==============~~~~~

# You probably don't need to edit anything below this line, but feel free to
# ask if you have any questinos about what it is doing or how it works. If you
# do need to change anything below this line, please feel free to


class Dir(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class ExchangeConnection:
    def __init__(self, args):
        self.message_timestamps = deque(maxlen=500)
        self.exchange_hostname = args.exchange_hostname
        self.port = args.port
        self.exchange_socket = self._connect(add_socket_timeout=args.add_socket_timeout)

        self._write_message({"type": "hello", "team": team_name.upper()})

    def read_message(self):
        """Read a single message from the exchange"""
        message = json.loads(self.exchange_socket.readline())
        if "dir" in message:
            message["dir"] = Dir(message["dir"])
        return message

    def send_add_message(
        self, order_id: int, symbol: str, dir: Dir, price: int, size: int
    ):
        """Add a new order"""
        self._write_message(
            {
                "type": "add",
                "order_id": order_id,
                "symbol": symbol,
                "dir": dir,
                "price": price,
                "size": size,
            }
        )

    def send_convert_message(self, order_id: int, symbol: str, dir: Dir, size: int):
        """Convert between related symbols"""
        self._write_message(
            {
                "type": "convert",
                "order_id": order_id,
                "symbol": symbol,
                "dir": dir,
                "size": size,
            }
        )

    def send_cancel_message(self, order_id: int):
        """Cancel an existing order"""
        self._write_message({"type": "cancel", "order_id": order_id})

    def _connect(self, add_socket_timeout):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        if add_socket_timeout:
            # Automatically raise an exception if no data has been recieved for
            # multiple seconds. This should not be enabled on an "empty" test
            # exchange.
            s.settimeout(5)
        s.connect((self.exchange_hostname, self.port))
        return s.makefile("rw", 1)

    def _write_message(self, message):
        json.dump(message, self.exchange_socket)
        self.exchange_socket.write("\n")

        now = time.time()
        self.message_timestamps.append(now)
        if len(
            self.message_timestamps
        ) == self.message_timestamps.maxlen and self.message_timestamps[0] > (now - 1):
            print(
                "WARNING: You are sending messages too frequently. The exchange will start ignoring your messages. Make sure you are not sending a message in response to every exchange message."
            )


def parse_arguments():
    test_exchange_port_offsets = {"prod-like": 0, "slower": 1, "empty": 2}

    parser = argparse.ArgumentParser(description="Trade on an ETC exchange!")
    exchange_address_group = parser.add_mutually_exclusive_group(required=True)
    exchange_address_group.add_argument(
        "--production", action="store_true", help="Connect to the production exchange."
    )
    exchange_address_group.add_argument(
        "--test",
        type=str,
        choices=test_exchange_port_offsets.keys(),
        help="Connect to a test exchange.",
    )

    # Connect to a specific host. This is only intended to be used for debugging.
    exchange_address_group.add_argument(
        "--specific-address", type=str, metavar="HOST:PORT", help=argparse.SUPPRESS
    )

    args = parser.parse_args()
    args.add_socket_timeout = True

    if args.production:
        args.exchange_hostname = "production"
        args.port = 25000
    elif args.test:
        args.exchange_hostname = "test-exch-" + team_name
        args.port = 25000 + test_exchange_port_offsets[args.test]
        if args.test == "empty":
            args.add_socket_timeout = False
    elif args.specific_address:
        args.exchange_hostname, port = args.specific_address.split(":")
        args.port = int(port)

    return args


if __name__ == "__main__":
    # Check that [team_name] has been updated.
    assert (
        team_name != "REPLACEME"
    ), "Please put your team name in the variable [team_name]."
    
    main()
