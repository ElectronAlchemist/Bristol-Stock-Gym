from Order import OType, Order

# OrderBookHalf is one side of the book: a list of bids or a list of asks, each sorted best-first

class OrderBookHalf:

    def __init__(self, booktype, minprice = 1, maxprice = 1000):
        # booktype: bids or asks?
        self.booktype = booktype
        # dictionary of orders received, indexed by Trader ID
        self.orders = {}
        # limit order book, dictionary indexed by price, with order info
        self.lob = {}
        # anonymized LOB, lists, with only price/qty info
        self.lob_anon = []
        # LOB rules
        self.minprice = minprice
        self.maxprice = maxprice


    # Add order to the dictionary holding the list of orders
    # Max one order per trader: if an existing one already exists, it is overwritten
    def add_order(self, order):

        # Validates the price tag of an order. If invalid, clip it to the min/max
        def validate_order_price(self, order):
            if order.price < self.minprice:
                order.price = self.minprice
            elif order.price > self.maxprice:
                order.price = self.maxprice
            return order

        # Validate order
        order = validate_order_price(self, order)

        # Add order to self.orders, keeping track of order numbers
        initial_n_orders = len(self.orders)
        self.orders[order.tid] = order
        new_n_orders = len(self.orders)

        # Rebuild LOB
        self.build_lob()

        # As a return, indicate if it has been an addition or an overwrite
        if initial_n_orders != new_n_orders:
            return('Addition')
        else:
            return('Overwrite')


    # Anonymize a lob, strip out order details, format as a sorted list
    def anonymize_lob(self):
        self.lob_anon = []
        if self.booktype == OType.BID:
            for price in sorted(self.lob, reverse = True):
                    qty = self.lob[price][0]
                    self.lob_anon.append([price, qty])
        elif self.booktype == OType.ASK:
            for price in sorted(self.lob):
                    qty = self.lob[price][0]
                    self.lob_anon.append([price, qty])
        else:
            raise RuntimeError('Error when anonymizing LOB: wrong booktype')


    # Take a list of orders and build a limit-order-book (LOB) from it
    def build_lob(self):
        # Sets the LOB as a dictionary (i.e., unsorted)
        self.lob = {}
        for tid in self.orders:
            order = self.orders.get(tid)
            price = order.price
            if price in self.lob:
                # update existing entry
                qty = self.lob[price][0]
                orderlist = self.lob[price][1]
                orderlist.append([order.time, order.qty, order.tid, order.qid])
                self.lob[price] = [qty + order.qty, orderlist]
            else:
                # create a new dictionary entry
                self.lob[price] = [order.qty, [[order.time, order.qty, order.tid, order.qid]]]

        # Builds anonymized version (just price/quantity, sorted, as a list) for publishing to traders
        self.anonymize_lob()


    # Delete qty = 1 of the best order (e.g. if the best bid/ask has been hit)
    # Retur the Trader ID of the deleted order
    def delete_best(self):
        _best_price, best_tid = self.get_best()
        order_to_delete = self.orders[best_tid]
        self.del_order(order_to_delete)
        return best_tid

    # Delete order from the dictionary holding the orders
    # assumes max of one order per trader per list
    # checks that the Trader ID does actually exist in the dict before deletion
    def del_order(self, order):

        if self.orders.get(order.tid) != None :
            del(self.orders[order.tid])
            self.build_lob()

    def get_best(self):

        if len(self.lob) == 0:
            return None, None

        if self.booktype == OType.BID:
            best_price = max(self.lob.keys())
        else:
            best_price = min(self.lob.keys())

        best_tid = self.lob[best_price][1][0][2] # TODO: This is confusing

        return best_price, best_tid

if __name__ == "__main__":

    otype = OType.BID

    order1 = Order('ID1', otype, 5, 1, 0, 1)
    order2 = Order('ID2', otype, 10, 1, 1, 2)
    order3 = Order('ID1', otype, 15, 1, 2, 3)

    OH = OrderBookHalf(otype)

    OH.add_order(order1)
    OH.add_order(order2)
    OH.add_order(order3)

    print(OH.booktype)
    print(OH.orders)
    print(OH.lob)
    print(OH.lob_anon)

    best_price, best_tid = OH.get_best()
    print(best_price, best_tid)

    OH.delete_best()

    print(OH.booktype)
    print(OH.orders)
    print(OH.lob)
    print(OH.lob_anon)

    best_price, best_tid = OH.get_best()
    print(best_price, best_tid)
