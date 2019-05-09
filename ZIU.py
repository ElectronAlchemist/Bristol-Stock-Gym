import random
from Order import OType, Order
from Trader import Trader

class ZIU(Trader):

    def action(self, player_action, time):
        # If the trader has no pending trade orders, do nothing
        if self.order == None:
            return None
        # Return an order with a random price
        price = random.randint(self.exchange_rules['minprice'], self.exchange_rules['maxprice'])
        order = Order(self.tid, self.order.otype, price, self.order.qty, time)
        return order
