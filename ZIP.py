import random
from Order import OType, Order
from Trader import Trader

class ZIP(Trader):

    def __init__(self, trader_type, trader_id, min_price = 1, max_price = 1000):
        super().__init__(trader_type, trader_id, min_price, max_price)

        # Initialise ZIP arguments
        # self.job = None  # this gets switched to 'Bid' or 'Ask' depending on order-type       # self.otype
        # self.active = False  # gets switched to True while actively working an order          # self.order == None

        self.previous_change = 0  # this was called last_d in Cliff'97

        ## ZIP Parameters
        self.beta = 0.1 + 0.4 * random.random()
        self.momentum = 0.1 * random.random()
        self.ca = 0.05  # hard-coded in '97 but parameterised later
        self.cr = 0.05  # hard-coded in '97 but parameterised later

        ## Use different margins for buying and selling
        self.margin = None  # this was called profit in Cliff'97
        self.margin_buy = -1.0 * (0.05 + 0.3 * random.random())
        self.margin_sell = 0.05 + 0.3 * random.random()

        self.price = None # Price currently quoting
        # self.limit = None

        # Memory of best price & quantity of best bid and ask, on LOB on previous update
        self.prev_best_bid_p = min_price
        self.prev_best_bid_q = 0
        self.prev_best_ask_p = max_price
        self.prev_best_ask_q = 0

    # Assigns a new order to the trader, replacing a previous one if there was one
    def assign_order(self, order):
        self.order = order
        self.otype = order.otype

        # ZIP Specific initialisations
        if order.otype == OType.BID:
            self.margin = self.margin_buy
        else:
            self.margin = self.margin_sell
        self.price = int(self.order.price * (1 + self.margin))

    def action(self, player_action, time):
        # If the trader has no pending trade orders, do nothing
        if self.order == None:
            return None

        # Return an order with the order's price + the margin
        if self.order.otype == OType.BID:
            price = self.price
        else:
            price = self.price
        order = Order(self.tid, self.order.otype, price, self.order.qty, time)
        return order


    def update(self, public_lob):

        def alter_profit(price):
            old_price = self.price
            diff = price - old_price
            change = ((1.0 - self.momentum) * (self.beta * diff)) + (self.momentum * self.previous_change)
            self.previous_change = change
            new_margin = ((self.price + change) / self.order.price) - 1.0

            if self.otype == OType.BID:
                if new_margin < 0.0 :
                    self.margin_buy = new_margin
            else:
                if new_margin > 0.0 :
                    self.margin_sell = new_margin

            self.price = int(round(self.order.price * (1.0 + self.margin), 0))

        # Generate a lower target price by randomly perturbing a given price
        def target_down(price):
            absolute_shift = self.ca * random.random()
            relative_shift = price * (1.0 + (self.cr * random.random()))
            target = int(round(absolute_shift - relative_shift, 0))
            return target

        # Generate a higher target price by randomly perturbing a given price
        def target_up(price):
            absolute_shift = self.ca * random.random()
            relative_shift = price * (1.0 + (self.cr * random.random()))
            target = int(round(absolute_shift + relative_shift, 0))
            return target

        def willing_to_trade(price):
            willing = False
            if self.otype == OType.BID and self.order != None and self.price >= price:
                willing = True
            elif self.otype == OType.ASK and self.order != None and self.price <= price:
                willing = True
            return willing

        ## Main function code:

        # What, if anything, has happened on the bid LOB?

        # To check:
        bid_improved = False
        bid_hit = False

        # Get best bid data
        best_bid_p = self.exchange_rules['minprice']
        best_bid_q = 0
        if len(public_lob['bids']) > 0:
            best_bid_p = public_lob['bids'][0][0]
            best_bid_q = public_lob['bids'][0][1]

        # Run checks
        if best_bid_p != self.exchange_rules['minprice'] :
            if self.prev_best_bid_p < best_bid_p:
                bid_improved = True
            elif len(public_lob['tape']) > 0: # Get previous trade, if it exists
                last_trade_timestep = public_lob['tape'][-1]['time']
                last_timestep = public_lob['time'] - 1
                if last_trade_timestep == last_timestep:
                    bid_hit = True
        elif self.prev_best_bid_p != self.exchange_rules['minprice'] :
            # The LOB has been emptied: was it cancelled or hit?
            if len(public_lob['tape']) > 0:
                last_tape_item = public_lob['tape'][-1]
                if last_tape_item['type'] != 'Cancel' :
                    bid_hit = True


        # What, if anything, has happened on the ask LOB?

        # To check:
        ask_improved = False
        ask_lifted = False

        # Get best ask data
        best_ask_p = self.exchange_rules['maxprice']
        best_ask_q = 0
        if len(public_lob['asks']) > 0:
            best_ask_p = public_lob['asks'][0][0]
            best_ask_q = public_lob['asks'][0][1]

        # Run checks
        if best_ask_p != self.exchange_rules['maxprice'] :
            if self.prev_best_ask_p < best_ask_p:
                ask_improved = True
            elif len(public_lob['tape']) > 0: # Get previous trade, if it exists
                last_trade_timestep = public_lob['tape'][-1]['time']
                last_timestep = public_lob['time'] - 1
                if last_trade_timestep == last_timestep:
                    ask_lifted = True
        elif self.prev_best_ask_p != self.exchange_rules['maxprice'] :
            # The LOB has been emptied: was it cancelled or lifted?
            if len(public_lob['tape']) > 0:
                last_tape_item = public_lob['tape'][-1]
                if last_tape_item['type'] != 'Cancel' :
                    ask_lifted = True

        # Did a deal happen?
        deal_happened = bid_hit or ask_lifted
        deal = None
        if deal_happened:
            deal = public_lob['tape'][-1]

        # Update target price if asking:
        if self.order.otype == OType.ASK:
            if deal_happened :
                tradeprice = deal['price']
                if self.price <= tradeprice: # Raise Margin
                    new_target_price = target_up(tradeprice)
                    alter_profit(new_target_price)
                elif ask_lifted and self.order != None and not willing_to_trade(tradeprice): # Reduce Margin
                    new_target_price = target_down(tradeprice)
                    alter_profit(new_target_price)
            else:
                # No deal: aim for a target price higher than best bid
                if ask_improved and self.price > best_ask_p:
                    if best_bid_p > self.exchange_rules['minprice']:
                        new_target_price = target_up(best_bid_p)
                    else:
                        new_target_price = public_lob['asks'][-1][0]
                    alter_profit(new_target_price)

        # Update target price if bidding:
        if self.order.otype == OType.BID:
            if deal_happened :
                tradeprice = deal['price']
                if self.price >= tradeprice: # Raise Margin
                    new_target_price = target_down(tradeprice)
                    alter_profit(new_target_price)
                elif bid_hit and self.order != None and not willing_to_trade(tradeprice): # Reduce Margin
                    new_target_price = target_up(tradeprice)
                    alter_profit(new_target_price)
            else:
                # No deal: aim for a target price lower than best ask
                if bid_improved and self.price < best_bid_p:
                    if best_bid_p < self.exchange_rules['maxprice']:
                        new_target_price = target_down(best_ask_p)
                    else:
                        new_target_price = public_lob['bids'][-1][0]
                    alter_profit(new_target_price)

        # Remember the best LOB data for the next time-step update
        self.prev_best_bid_p = best_bid_p
        self.prev_best_bid_q = best_bid_q
        self.prev_best_ask_p = best_ask_p
        self.prev_best_ask_q = best_ask_q
