import random

from enum import Enum
from Order import OType, Order

# A trader can be multiple types, including a player agent
class TType(Enum):
    PLAYER = 'PLAYER'
    GVWY = 'GIVEAWAY'
    ZIU = 'ZIU' # After Gode & Sunder 1993
    ZIC = 'ZIC' # After Gode & Sunder 1993
    ZIP = 'ZIP' # After Cliff 1997

class Trader:

    def __init__(self, trader_type, trader_id, min_price = 1, max_price = 1000):
        # Trader attributes:
        self.ttype = trader_type
        self.tid = trader_id
        self.order = None
        self.otype = None # Type of the order last assigned to the trader. Used if we want to keep a trader exclusively bidding or asking
        self.balance = 0
        # Exchange rules: # TODO: maybe change it to storing a local copy of the exchange if necessary?
        self.exchange_rules = {
            'minprice' : min_price,
            'maxprice' : max_price
        }

    # Assigns a new order to the trader, replacing a previous one if there was one
    def assign_order(self, order):
        self.order = order
        self.otype = order.otype

    # Regress to a price and place an order in the exchange
    # player_action input is for the player action
    def action(self, player_action, time):
        # If the trader has no pending trade orders, do nothing
        if self.order == None:
            return None

        if self.ttype == TType.PLAYER: # The player's strategy
            order = player_action
        else:
            raise RuntimeError('Unrecognised trader strategy')

        return order

    # Called whenever a transaction involving the trader has occurred
    def notify_transaction(self, transaction_record):
        def calculate_benefit(order, trade_price):
            if order.otype == OType.BID:
                benefit = order.price - trade_price
            elif order.otype == OType.ASK:
                benefit = trade_price - order.price
            else:
                raise RuntimeError('Error: Wrong order type stored in trader')
            return benefit

        if transaction_record['type'] == 'Trade':
            benefit = calculate_benefit(self.order, transaction_record['price'])
            self.balance += benefit
            self.order = None

    # Called to update the trader with the latest LOB information after each timestep
    def update(self, public_lob):
        None
