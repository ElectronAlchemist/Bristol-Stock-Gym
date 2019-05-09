import random
from Order import OType, Order
from Trader import Trader

class Giveaway(Trader):

    def action(self, player_action, time):
        # If the trader has no pending trade orders, do nothing
        if self.order == None:
            return None
        # Return an order with the given sale price
        price = self.order.price
        order = Order(self.tid, self.order.otype, price, self.order.qty, time)
        return order
