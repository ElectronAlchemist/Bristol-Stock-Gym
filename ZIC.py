import random
from Order import OType, Order
from Trader import Trader

class ZIC(Trader):

    def action(self, player_action, time):
        # If the trader has no pending trade orders, do nothing
        if self.order == None:
            return None
        # Quote a random price, never make a loss
        if self.order.otype == OType.BID:
            price = random.randint(self.exchange_rules['minprice'], self.order.price)
        elif self.order.otype == OType.ASK:
            price = random.randint(self.order.price, self.exchange_rules['maxprice'])
        order = Order(self.tid, self.order.otype, price, self.order.qty, time)
        return order
