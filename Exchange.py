from Order import OType, Order
from OrderBookHalf import OrderBookHalf

# Orderbook for a single instrument: list of bids and list of asks
class OrderBook:

    def __init__(self, min_price = 1, max_price = 1000):
            self.bids = OrderBookHalf(OType.BID, min_price, max_price)
            self.asks = OrderBookHalf(OType.ASK, min_price, max_price)
            self.tape = []
            self.quote_id = 0  #unique ID code for each quote accepted onto the book

    def generate_quote_id(self):
        qid = self.quote_id
        self.quote_id += 1
        return qid

class Exchange(OrderBook):

    # add a quote/order to the exchange; return unique i.d.
    def add_order(self, order):

        order.qid = self.generate_quote_id()
        if order.otype == OType.BID:
            self.bids.add_order(order)
        elif order.otype == OType.ASK:
            self.asks.add_order(order)
        else:
            raise RuntimeError('Error when adding order to exchange: malformed order')

        return order.qid

    # delete a trader's quote/order from the exchange
    def del_order(self, order, time):

        #Delete order
        if order.otype == OType.BID:
            self.bids.del_order(order)
        elif order.otype == OType.ASK:
            self.asks.del_order(order)
        else:
            raise RuntimeError('Error when deleting order from exchange: malformed order')

        # Add cancellation to tape
        # TODO: This is not working. Fix it.
        cancel_record = { 'type': 'Cancel', 'time': time, 'order': order }
        self.tape.append(cancel_record)

    # receive an order and either add it to the relevant LOB (ie treat as limit order)
    # or if it crosses the best counterparty offer, execute it (treat as a market order)
    def process_order(self, order, time):
        # Add order to LOB
        self.add_order(order)

        best_bid, best_bid_tid = self.bids.get_best()
        best_ask, best_ask_tid = self.asks.get_best()

        # Check if the order crosses the best counterparty offer
        price = None
        party_tid = None
        counterparty_tid = None
        if order.otype == OType.BID and len(self.asks.lob) > 0 and best_bid >= best_ask: # If bid lifts the best ask
            price = best_ask
            party_tid = self.bids.delete_best()
            counterparty_tid = self.asks.delete_best()
        elif order.otype == OType.ASK and len(self.bids.lob) > 0 and best_ask <= best_bid: # If ask hits the best bid
            price = best_bid
            party_tid = self.asks.delete_best()
            counterparty_tid = self.bids.delete_best()

        # If there has been a transaction, add it to the tape and return it so that
        # the traders are notified

        if (price != None) and (party_tid != None) and (counterparty_tid != None):
            transaction_record = { 'type': 'Trade',
                                   'time': time,
                                   'price': price,
                                   'party1':counterparty_tid,
                                   'party2':party_tid,
                                   'qty': order.qty # Should always be 1 until update!
                                  }
            self.tape.append(transaction_record)
            return transaction_record


    # this returns the LOB data "published" by the exchange,
    # i.e., what is accessible to the traders
    def get_public_lob(self, time):
        public_data = {}
        public_data['time'] = time
        public_data['bids'] = self.bids.lob_anon
        public_data['asks'] = self.asks.lob_anon
        public_data['tape'] = self.tape
        return public_data

    # This prints the public LOB data
    def print_public_lob(self, time):
        public_data = self.get_public_lob(time)
        print('***')
        print('publish_lob: t=%d' % time)
        print('BID_lob=%s' % public_data['bids'])
        print('ASK_lob=%s' % public_data['asks'])
        print('TAPE =', public_data['tape'])
        print('***')
        print()

    # TODO: Revise this function
    def tape_dump(self, fname, fmode, tmode):
        dumpfile = open(fname, fmode)
        for tapeitem in self.tape:
            if tapeitem['type'] == 'Trade' :
                dumpfile.write('%s, %s\n' % (tapeitem['time'], tapeitem['price']))
        dumpfile.close()
        if tmode == 'wipe':
            self.tape = []



# TODO: replace this with unit tests
if __name__ == "__main__":

    exchange = Exchange()

    time = 0
    order1 = Order('ID1', OType.BID, 5, 1, time)
    exchange.process_order(order1, time)
    exchange.print_public_lob(time)

    time = 1
    order2 = Order('ID2', OType.BID, 10, 1, time)
    exchange.process_order(order2, time)
    exchange.print_public_lob(time)

    time = 2
    order3 = Order('ID1', OType.BID, 15, 1, time)
    exchange.process_order(order3, time)
    exchange.print_public_lob(time)

    time = 3
    order4 = Order('ID3', OType.ASK, 20, 1, time)
    exchange.process_order(order4, time)
    exchange.print_public_lob(time)

    time = 4
    order5 = Order('ID4', OType.ASK, 15, 1, time)
    exchange.process_order(order5, time)
    exchange.print_public_lob(time)
